import requests
import configparser
from pathlib import Path

cfg = configparser.ConfigParser()
cfg.read(Path(__file__).parent.parent / "config.ini", encoding="utf-8")
token = cfg["finmind"]["token"]

url = "https://api.finmindtrade.com/api/v4/data"
headers = {"Authorization": f"Bearer {token}"}

# 測試：台積電最近月營收
params = {
    "dataset": "TaiwanStockMonthRevenue",
    "data_id": "2330",
    "start_date": "2024-01-01",
}
resp = requests.get(url, headers=headers, params=params)
data = resp.json()
print(f"狀態: {data.get('status')}")
print(f"資料筆數: {len(data.get('data', []))}")
if data.get('data'):
    print(f"最新一筆: {data['data'][-1]}")
