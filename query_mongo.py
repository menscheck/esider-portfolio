import sys
sys.path.insert(0, '.')
from pymongo import MongoClient

# 直接用 MongoDB 連接設定
client = MongoClient('localhost', 27017)
db = client['esg_db']
col = db['chunks']

print('總chunk數:', col.count_documents({}))
companies = sorted(col.distinct('company'))
print('公司數:', len(companies))
for c in companies:
    count = col.count_documents({"company": c})
    print(f'  {c}: {count}')
