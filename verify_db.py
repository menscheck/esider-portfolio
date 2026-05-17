from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
col = client["esg_db"]["chunks"]

print(f"總chunk數: {col.count_documents({})}")
print(f"公司數: {len(col.distinct('company'))}")
print()
for c in sorted(col.distinct("company")):
    count = col.count_documents({"company": c})
    print(f"  {c}: {count}")

client.close()