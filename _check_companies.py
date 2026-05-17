from app.core.config import get_config
from pymongo import MongoClient

cfg = get_config()
uri = cfg["mongodb"]["uri"]
client = MongoClient(uri)
col = client["esg_db"]["chunks"]

companies = sorted(col.distinct("company"))
total = col.count_documents({})

print(f"總 chunks 數：{total}")
print(f"已入庫公司（{len(companies)} 家）：")
for c in companies:
    count = col.count_documents({"company": c})
    print(f"  {c}：{count} chunks")

client.close()
