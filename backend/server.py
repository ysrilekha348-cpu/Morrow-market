from fastapi import FastAPI, APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List
from pathlib import Path
from datetime import datetime, timezone
import os, uuid, logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
from storage import init_storage, put_object, get_object, APP_NAME  # noqa: E402

logger = logging.getLogger("morrow")
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
app = FastAPI(title="Morrow Market API")
api_router = APIRouter(prefix="/api")
MAX_FILE_BYTES = 100 * 1024 * 1024

try:
    from clerk_auth import clerk_router, require_user
except Exception:
    clerk_router = None
    def require_user(): return {"user_id": "preview-owner"}


def now(): return datetime.now(timezone.utc).isoformat()


class ProductIn(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0)
    category: str = "Guides"
    tag: str = "New"
    image_url: str = ""
    published: bool = True


class Product(ProductIn):
    id: str
    created_at: str
    file_name: str = ""


class CheckoutIn(BaseModel):
    product_id: str
    customer_email: EmailStr


class SubmitPaymentIn(BaseModel):
    transaction_id: str = Field(min_length=6, max_length=40)


class SettingsIn(BaseModel):
    gpay_number: str = Field(min_length=4, max_length=60)


SEED = [
    ("weekly-reset", "The Weekly Reset", "A gentle planning system for people who want their weeks to feel lighter, not louder.", 499, "Workbooks", "Bestseller", "photo-1517842645767-c639042777db", "weekly-reset.pdf"),
    ("quiet-brand", "Quiet Brand Kit", "A considered visual direction kit for small brands ready to look like themselves.", 899, "Templates", "Fresh drop", "photo-1558655146-9f40138edfeb", "quiet-brand-kit.zip"),
    ("slow-content", "Slow Content Calendar", "30 thoughtful prompts to keep showing up without becoming a content machine.", 299, "Planning", "Popular", "photo-1499750310107-5fef28a66643", "slow-content-calendar.pdf"),
]
OLD_USD_PRICES = {"weekly-reset": 18.0, "quiet-brand": 32.0, "slow-content": 12.0}


async def seed():
    if await db.products.count_documents({}) == 0:
        await db.products.insert_many([
            {"id": i, "name": n, "description": d, "price": float(p), "category": c, "tag": t,
             "image_url": f"https://images.unsplash.com/{img}?auto=format&fit=crop&w=1000&q=85",
             "published": True, "file_name": f, "created_at": now()}
            for i, n, d, p, c, t, img, f in SEED])
    for i, _, _, p, *_ in SEED:
        await db.products.update_one({"id": i, "price": OLD_USD_PRICES[i]}, {"$set": {"price": float(p)}})
    await db.settings.update_one({"id": "store"}, {"$setOnInsert": {"id": "store", "gpay_number": "9337939011", "qr_path": ""}}, upsert=True)


@app.on_event("startup")
async def startup():
    await seed()
    try:
        init_storage()
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


async def read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if not data: raise HTTPException(400, "Empty file")
    if len(data) > MAX_FILE_BYTES: raise HTTPException(413, "File too large (max 100 MB)")
    return data


async def get_settings():
    return await db.settings.find_one({"id": "store"}, {"_id": 0})


# ---------- Public ----------
@api_router.get("/")
async def root(): return {"message": "Morrow Market API"}


@api_router.get("/products", response_model=List[Product])
async def products(): return await db.products.find({"published": True}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.get("/products/{product_id}", response_model=Product)
async def product(product_id: str):
    item = await db.products.find_one({"id": product_id, "published": True}, {"_id": 0})
    if not item: raise HTTPException(404, "Product not found")
    return item


@api_router.get("/store/payment-info")
async def payment_info():
    s = await get_settings()
    return {"gpay_number": s["gpay_number"], "has_qr": bool(s.get("qr_path")), "qr_version": s.get("qr_updated_at", "")}


@api_router.get("/store/qr")
async def store_qr():
    s = await get_settings()
    if not s.get("qr_path"): raise HTTPException(404, "No QR code uploaded yet")
    data, ctype = get_object(s["qr_path"])
    return Response(content=data, media_type=s.get("qr_content_type") or ctype)


@api_router.post("/payments/checkout")
async def checkout(body: CheckoutIn):
    item = await db.products.find_one({"id": body.product_id, "published": True}, {"_id": 0})
    if not item: raise HTTPException(404, "Product not found")
    session_id = uuid.uuid4().hex
    await db.orders.insert_one({
        "id": str(uuid.uuid4()), "session_id": session_id, "product_id": item["id"], "product_name": item["name"],
        "amount": item["price"], "customer_email": body.customer_email, "payment_method": "gpay",
        "payment_status": "awaiting_payment", "transaction_id": "", "created_at": now()})
    return {"session_id": session_id}


ORDER_PUBLIC = {"_id": 0, "session_id": 1, "payment_status": 1, "product_id": 1, "product_name": 1, "amount": 1, "customer_email": 1}


@api_router.get("/payments/status/{session_id}")
async def payment_status(session_id: str):
    item = await db.orders.find_one({"session_id": session_id}, ORDER_PUBLIC)
    if not item: raise HTTPException(404, "Order not found")
    return item


@api_router.post("/payments/{session_id}/submit")
async def submit_payment(session_id: str, body: SubmitPaymentIn):
    res = await db.orders.update_one(
        {"session_id": session_id, "payment_status": {"$in": ["awaiting_payment", "rejected"]}},
        {"$set": {"transaction_id": body.transaction_id.strip(), "payment_status": "pending_review", "submitted_at": now()}})
    if not res.matched_count: raise HTTPException(400, "This order can't accept a payment reference")
    return await db.orders.find_one({"session_id": session_id}, ORDER_PUBLIC)


@api_router.get("/downloads/{session_id}")
async def download(session_id: str):
    order = await db.orders.find_one({"session_id": session_id, "payment_status": "paid"}, {"_id": 0})
    if not order: raise HTTPException(404, "Download unavailable")
    p = await db.products.find_one({"id": order["product_id"]}, {"_id": 0})
    name = p.get("file_name") or "morrow-download.txt"
    if p.get("storage_path"):
        data, ctype = get_object(p["storage_path"])
        ctype = p.get("file_content_type") or ctype
    else:
        data, ctype = f"Morrow Market\n\n{p['name']}\n\nThank you for your purchase. (Sample file - the owner hasn't uploaded the real file yet.)".encode(), "text/plain"
        name = Path(name).stem + "-sample.txt"
    return Response(content=data, media_type=ctype, headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ---------- Admin ----------
def is_admin(user: dict):
    claims = user.get("claims", {})
    email = (claims.get("email") or claims.get("email_address") or "").lower()
    allowed = {x.strip().lower() for x in os.environ.get("ADMIN_EMAIL", "").split(",") if x.strip()}
    return email in allowed or os.environ.get("CLERK_SECRET_KEY") == ""


async def admin_user(user=Depends(require_user)):
    if not is_admin(user): raise HTTPException(403, "Owner access required")
    return user


@api_router.get("/admin/products", response_model=List[Product])
async def admin_products(_: dict = Depends(admin_user)): return await db.products.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.post("/admin/products", response_model=Product)
async def create_product(body: ProductIn, _: dict = Depends(admin_user)):
    doc = body.model_dump() | {"id": str(uuid.uuid4()), "file_name": "", "created_at": now()}
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.patch("/admin/products/{product_id}", response_model=Product)
async def update_product(product_id: str, body: ProductIn, _: dict = Depends(admin_user)):
    await db.products.update_one({"id": product_id}, {"$set": body.model_dump()})
    item = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not item: raise HTTPException(404, "Product not found")
    return item


@api_router.post("/admin/products/{product_id}/file")
async def upload_product_file(product_id: str, file: UploadFile = File(...), _: dict = Depends(admin_user)):
    if not await db.products.find_one({"id": product_id}): raise HTTPException(404, "Product not found")
    data = await read_upload(file)
    ext = Path(file.filename or "file.bin").suffix or ".bin"
    ctype = file.content_type or "application/octet-stream"
    result = put_object(f"{APP_NAME}/products/{product_id}/{uuid.uuid4()}{ext}", data, ctype)
    await db.products.update_one({"id": product_id}, {"$set": {"file_name": Path(file.filename).name, "storage_path": result["path"], "file_content_type": ctype, "file_size": len(data)}})
    return {"file_name": Path(file.filename).name, "status": "stored"}


@api_router.get("/admin/orders")
async def orders(_: dict = Depends(admin_user)): return await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)


@api_router.post("/admin/orders/{order_id}/{action}")
async def review_order(order_id: str, action: str, _: dict = Depends(admin_user)):
    if action not in ("approve", "reject"): raise HTTPException(404, "Unknown action")
    status = "paid" if action == "approve" else "rejected"
    res = await db.orders.update_one({"id": order_id}, {"$set": {"payment_status": status, "reviewed_at": now()}})
    if not res.matched_count: raise HTTPException(404, "Order not found")
    return await db.orders.find_one({"id": order_id}, {"_id": 0})


@api_router.get("/admin/settings")
async def admin_settings(_: dict = Depends(admin_user)):
    s = await get_settings()
    return {"gpay_number": s["gpay_number"], "has_qr": bool(s.get("qr_path")), "qr_version": s.get("qr_updated_at", "")}


@api_router.put("/admin/settings")
async def save_settings(body: SettingsIn, _: dict = Depends(admin_user)):
    await db.settings.update_one({"id": "store"}, {"$set": {"gpay_number": body.gpay_number.strip()}})
    return await admin_settings(_)


@api_router.post("/admin/settings/qr")
async def upload_qr(file: UploadFile = File(...), _: dict = Depends(admin_user)):
    if not (file.content_type or "").startswith("image/"): raise HTTPException(400, "Please upload an image")
    data = await read_upload(file)
    ext = Path(file.filename or "qr.png").suffix or ".png"
    result = put_object(f"{APP_NAME}/settings/qr-{uuid.uuid4()}{ext}", data, file.content_type)
    await db.settings.update_one({"id": "store"}, {"$set": {"qr_path": result["path"], "qr_content_type": file.content_type, "qr_updated_at": now()}})
    return await admin_settings(_)


app.include_router(api_router)
if clerk_router: app.include_router(clerk_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])


@app.on_event("shutdown")
async def shutdown(): client.close()
