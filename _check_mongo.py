import configparser
cp = configparser.ConfigParser()
cp.read('config.ini', encoding='utf-8')
from pymongo import MongoClient
client = MongoClient(cp['mongodb']['uri'], serverSelectionTimeoutMS=5000)
client.server_info()
print('MongoDB 連線正常')
print('目前 chunks 數量:', client['esg_db']['chunks'].count_documents({}))
client.close()
