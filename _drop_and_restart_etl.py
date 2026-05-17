import configparser
cp = configparser.ConfigParser()
cp.read('config.ini', encoding='utf-8')
from pymongo import MongoClient
client = MongoClient(cp['mongodb']['uri'])
col = client['esg_db']['chunks']

before = col.count_documents({})
print(f'Drop 前 chunks 數：{before}')
col.drop()
print('Collection dropped，Atlas 空間釋放中（請等 1-2 分鐘後再跑 ETL）')
client.close()
