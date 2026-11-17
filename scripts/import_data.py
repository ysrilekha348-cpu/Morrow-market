import os
import sys
from pathlib import Path
from bson import json_util
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / "backend" / ".env")
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
folder = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data_export")

for f in folder.glob("*.json"):
    docs = json_util.loads(f.read_text())
    db[f.stem].delete_many({})
    if docs:
        db[f.stem].insert_many(docs)
    print(f"{f.stem}: {len(docs)} restored")
