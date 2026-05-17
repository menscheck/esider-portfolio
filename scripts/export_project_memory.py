#!/usr/bin/env python3
"""
scripts/export_project_memory.py
列印一筆 sample 並匯出 esg_db.project_memory 為 JSON
"""
from pymongo import MongoClient
from bson import json_util
import json

client = MongoClient("mongodb://localhost:27017")
db = client["esg_db"]
col = db["project_memory"]

sample = col.find_one({}, sort=[("updated_at", -1)])
if sample:
    print("--- SAMPLE DOCUMENT (most recent) ---")
    print(json_util.dumps(sample, ensure_ascii=False, indent=2))
else:
    print("No documents found in esg_db.project_memory")

all_docs = list(col.find({}))
out_path = r"C:\Users\Sam Joseph\esg-agent\scripts\project_memory.json"
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(json_util.dumps(all_docs, ensure_ascii=False, indent=2))

print(f"Exported {len(all_docs)} documents to {out_path}")
client.close()
