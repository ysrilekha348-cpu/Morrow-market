from fastapi import FastAPI, APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import os, uuid, logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
app = FastAPI(title="Morrow Market API")
api_router = APIRouter(prefix="/api")
PRIVATE_DIR = ROOT_DIR / "private_uploads"
PRIVATE_DIR.mkdir(exist_ok=True)

try:
    from clerk_auth import clerk_router, require_user
except Exception:
    clerk_router = None
    def require_user(): return {"user_id": "preview-owner"}

class ProductIn(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0)
    category: str = "Guides"
    tag: str = "New"
    image_url: str = ""
    published: bool = True
    file_name: str = ""

class Product(ProductIn):
    id: str
    created_at: str

class CheckoutIn(BaseModel):
    product_id: str
    customer_email: str
    origin_url: str

async def seed_products():
    if await db.products.count_documents({}) == 0:
        now = datetime.now(timezone.utc).isoformat()
        seed = [
            {"id":"weekly-reset","name":"The Weekly Reset","description":"A gentle planning system for people who want their weeks to feel lighter, not louder.","price":18.0,"category":"Workbooks","tag":"Bestseller","image_url":"https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1000&q=85","published":True,"file_name":"weekly-reset.pdf","created_at":now},
            {"id":"quiet-brand","name":"Quiet Brand Kit","description":"A considered visual direction kit for small brands ready to look like themselves.","price":32.0,"category":"Templates","tag":"Fresh drop","image_url":"https://images.unsplash.com/photo-1558655146-9f40138edfeb?auto=format&fit=crop&w=1000&q=85","published":True,"file_name":"quiet-brand-kit.zip","created_at":now},
            {"id":"slow-content","name":"Slow Content Calendar","description":"30 thoughtful prompts to keep showing up without becoming a content machine.","price":12.0,"category":"Planning","tag":"Popular","image_url":"https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=1000&q=85","published":True,"file_name":"slow-content-calendar.pdf","created_at":now},
        ]
        await db.products.insert_many(seed)

@app.on_event("startup")
async def startup(): await seed_products()

@api_router.get("/")
async def root(): return {"message":"Morrow Market API"}

@api_router.get("/products", response_model=List[Product])
async def products(): return await db.products.find({"published": True}, {"_id": 0}).sort("created_at", -1).to_list(100)

@api_router.get("/products/{product_id}", response_model=Product)
async def product(product_id: str):
    item = await db.products.find_one({"id": product_id, "published": True}, {"_id": 0})
    if not item: raise HTTPException(404, "Product not found")
    return item

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
    doc = body.model_dump() | {"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.products.insert_one(doc); return doc

@api_router.patch("/admin/products/{product_id}", response_model=Product)
async def update_product(product_id: str, body: ProductIn, _: dict = Depends(admin_user)):
    await db.products.update_one({"id": product_id}, {"$set": body.model_dump()})
    item = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not item: raise HTTPException(404, "Product not found")
    return item

@api_router.post("/admin/products/{product_id}/file")
async def upload_product_file(product_id: str, file: UploadFile = File(...), _: dict = Depends(admin_user)):
    safe_name = f"{product_id}-{uuid.uuid4().hex}-{Path(file.filename or 'download.bin').name}"
    (PRIVATE_DIR / safe_name).write_bytes(await file.read())
    await db.products.update_one({"id": product_id}, {"$set": {"file_name": file.filename, "private_file": safe_name}})
    return {"file_name": file.filename, "status": "stored"}

@api_router.get("/admin/orders")
async def orders(_: dict = Depends(admin_user)): return await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)

@api_router.post("/payments/checkout")
async def checkout(body: CheckoutIn):
    item = await db.products.find_one({"id": body.product_id, "published": True}, {"_id": 0})
    if not item: raise HTTPException(404, "Product not found")
    session_id = "demo_" + uuid.uuid4().hex
    order = {"id": str(uuid.uuid4()), "session_id": session_id, "product_id": item["id"], "product_name": item["name"], "amount": item["price"], "customer_email": body.customer_email, "payment_status":"paid", "download_status":"ready", "created_at": datetime.now(timezone.utc).isoformat()}
    await db.orders.insert_one(order)
    return {"checkout_url": f"{body.origin_url}/payment/success?session_id={session_id}", "session_id": session_id, "payment_status": "paid", "demo": True}

@api_router.get("/payments/status/{session_id}")
async def payment_status(session_id: str):
    item = await db.orders.find_one({"session_id": session_id}, {"_id": 0, "session_id": 1, "payment_status": 1, "download_status": 1, "product_id": 1, "product_name": 1})
    if not item: raise HTTPException(404, "Order not found")
    return item

@api_router.get("/downloads/{session_id}")
async def download(session_id: str):
    order = await db.orders.find_one({"session_id": session_id, "payment_status": "paid"}, {"_id": 0})
    if not order: raise HTTPException(404, "Download unavailable")
    product = await db.products.find_one({"id": order["product_id"]}, {"_id": 0})
    content = f"Morrow Market\n\n{product['name']}\n\nThank you for your purchase. Your private download is ready."
    return Response(content=content, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={product.get('file_name') or 'morrow-download.txt'}"})

app.include_router(api_router)
if clerk_router: app.include_router(clerk_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])
@app.on_event("shutdown")
async def shutdown(): client.close()