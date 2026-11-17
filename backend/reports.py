import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

IST = ZoneInfo("Asia/Kolkata")
STATUS = {"awaiting_payment": "Awaiting payment", "pending_review": "Needs review", "paid": "Paid", "rejected": "Rejected"}
COLUMNS = [("Order date (IST)", "created_at", 20), ("Product", "product_name", 32), ("Customer email", "customer_email", 30),
           ("Status", "payment_status", 16), ("List price (₹)", "original_amount", 14), ("Discount code", "discount_code", 14),
           ("Discount %", "discount_percent", 11), ("Amount paid (₹)", "amount", 15), ("Payment method", "payment_method", 15),
           ("UTR / Transaction ID", "transaction_id", 22), ("Confirmed on (IST)", "reviewed_at", 20), ("Order ID", "id", 38)]
HEAD_FILL = PatternFill("solid", fgColor="29352F")


def ist_text(iso: str) -> str:
    if not iso:
        return ""
    return datetime.fromisoformat(iso).astimezone(IST).strftime("%d %b %Y, %I:%M %p")


def _cell(order: dict, key: str):
    value = order.get(key, "")
    if key in ("created_at", "reviewed_at"):
        return ist_text(value)
    if key == "payment_status":
        return STATUS.get(value, value)
    if key == "discount_percent":
        return value or ""
    return value


def orders_xlsx(orders: list) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append([c[0] for c in COLUMNS])
    for i, (_, _, width) in enumerate(COLUMNS):
        ws.cell(1, i + 1).font = Font(bold=True, color="F5F4EF")
        ws.cell(1, i + 1).fill = HEAD_FILL
        ws.column_dimensions[ws.cell(1, i + 1).column_letter].width = width
    for o in orders:
        ws.append([_cell(o, key) for _, key, _ in COLUMNS])
    paid = [o for o in orders if o.get("payment_status") == "paid"]
    ws.append([])
    ws.append(["Confirmed revenue", "", "", f"{len(paid)} paid orders", "", "", "", sum(o.get("amount", 0) for o in paid)])
    ws.cell(ws.max_row, 1).font = Font(bold=True)
    ws.cell(ws.max_row, 8).font = Font(bold=True)
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_zip(collections: dict, orders: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, docs in collections.items():
            z.writestr(f"{name}.json", json.dumps(docs, indent=2, default=str))
        z.writestr("orders.xlsx", orders_xlsx(orders))
    return buf.getvalue()


def daily_stats(orders: list, now: datetime) -> dict:
    since = (now - timedelta(hours=24)).isoformat()
    confirmed = [o for o in orders if o.get("payment_status") == "paid" and o.get("amount", 0) > 0 and (o.get("reviewed_at") or "") >= since]
    return {
        "date": now.astimezone(IST).strftime("%A, %d %B"),
        "confirmed_count": len(confirmed),
        "revenue": sum(o["amount"] for o in confirmed),
        "new_orders": sum(1 for o in orders if o.get("amount", 0) > 0 and o.get("created_at", "") >= since),
        "free_downloads": sum(1 for o in orders if o.get("amount", 0) == 0 and o.get("created_at", "") >= since),
        "waiting": [o for o in orders if o.get("payment_status") == "pending_review"],
    }
