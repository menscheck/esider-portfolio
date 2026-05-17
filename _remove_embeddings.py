import configparser
cp = configparser.ConfigParser()
cp.read('config.ini', encoding='utf-8')
from pymongo import MongoClient
client = MongoClient(cp['mongodb']['uri'])
result = client['esg_db']['chunks'].update_many(
    {'embedding': {'$exists': True}},
    {'$unset': {'embedding': ''}}
)
print(f'清除 {result.modified_count} 筆 embedding，等待 Atlas 空間釋放（約1-2分鐘）')
client.close()
