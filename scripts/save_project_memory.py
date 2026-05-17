#!/usr/bin/env python3
"""
scripts/save_project_memory.py
將專案開發知識存入 MongoDB，供日後 Claude 快速載入
"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["esg_db"]
col = db["project_memory"]

memories = [
    {
        "category": "download",
        "title": "TWSE ESG平台下載方式",
        "content": """
網址：https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW
必填欄位：市場別（下拉）、報告年度（下拉）
可選欄位：產業別（不選預設全選）、公司代號（autocomplete）

Playwright關鍵步驟：
1. 市場別/年度：用 page.evaluate() 找div文字精確匹配點選
2. 公司代號：輸入後等1000ms點autocomplete第一項
3. 查詢按鈕：等變藍才點
4. 結果：點 {code}-{公司名} 展開，點「下載 PDF」

存檔路徑：data/reports/{公司名}/{公司名}_ESG_2024.pdf
有效大小：>1MB
腳本：download_p1_batch.py
        """.strip(),
        "tags": ["download", "playwright", "twse", "pdf"],
    },
    {
        "category": "architecture",
        "title": "系統架構總覽",
        "content": """
專案名稱：eSider ESG洞察平台
路徑：C:\\Users\\Sam Joseph\\esg-agent

技術棧：
- Embedding: BAAI/bge-m3（本地，RTX 3060，CUDA 12.4）
- 向量DB: FAISS（data/faiss_index/esg.index + id_map.json）
- 文件DB: MongoDB（localhost:27017，esg_db.chunks）
- LLM: Azure OpenAI gpt-4.1-mini（config.ini）
- Bot: LINE Bot + FastAPI + ngrok
- 下載: Playwright

核心模組：
- app/core/retriever.py: FAISS語意搜尋
- app/core/pipeline.py: 完整查詢流程
- app/core/persona_router.py: 4個Persona的system prompt
- app/core/tag_parser.py: 40個ESG tag的jieba比對
- app/core/company_resolver.py: 公司名稱模糊比對（rapidfuzz）
- app/bot/line_handler.py: LINE Bot訊息處理
- app/bot/suggestion_engine.py: LLM動態生成延伸問題
- app/bot/webhook.py: FastAPI webhook
        """.strip(),
        "tags": ["architecture", "tech-stack", "modules"],
    },
    {
        "category": "data",
        "title": "資料結構與統計",
        "content": """
MongoDB schema（esg_db.chunks）：
{
  company: str,      # 公司名稱（如「台積電」）
  source: str,       # PDF檔名
  page: int,         # 頁碼
  chunk_id: str,     # {公司}_p{頁}_c{idx}
  text: str,         # 500字，50字重疊
  embedding: list    # 1024維 bge-m3向量
}

現有資料（2024-05）：
- 公司數：30家（上市）
- 總chunk數：16,406
- FAISS向量數：16,406
- 向量維度：1024

fetch_k設定：
- 有指定公司：top_k * 50（避免撈不到）
- 無指定公司：top_k

公司清單：
中國信託銀行、中華電信、中鋼公司、亞洲水泥、佳世達集團、
南山產物、台北富邦銀行、台塑、台新金控、台灣中油、
台積電、台達電、合作金庫銀行、國泰金控、宏遠興業、
崇越科技、廣達、彰化銀行、日月光投控、榮成紙業、
欣興電子、永豐銀行、玉山金控、第一銀行、統一超商、
聯電、遠東新世紀、長榮航空、開發金控、鴻海精密
        """.strip(),
        "tags": ["data", "mongodb", "faiss", "companies"],
    },
    {
        "category": "linebot",
        "title": "LINE Bot架構與互動邏輯",
        "content": """
啟動：python run_bot.py（FastAPI on port 8000）
外網：ngrok http 8000 → LINE Developer Console設Webhook URL

互動流程：
1. 加入帳號 → FollowEvent → 推送歡迎+身份選單（Flex Message）
2. 選身份 → Postback → 設session + 推薦3個問題（Quick Reply）
3. 問問題 → 查詢pipeline → 回答+延伸選單
4. 延伸選單：
   - 延伸問題（3題）：前2題鎖定公司，第3題廣泛型
   - 同類型公司：同產業3家 → 選一家 → 延伸問題
   - 換角色：其他3個角色 → 選一個 → 推薦問題

廣泛型觸發：含「哪些/那些/哪幾/還有/都有/類似/相同」等關鍵字
公司繼承：沒帶公司名時繼承session的last_company
input_type：text=手動輸入，postback=點選按鈕

session結構：
{
  persona: Persona,
  last_query: str,
  last_company: str,
  last_answer: str,
  asked_questions: set,
  input_type: str
}
        """.strip(),
        "tags": ["linebot", "session", "flex-message", "quick-reply"],
    },
    {
        "category": "persona",
        "title": "4個Persona設計",
        "content": """
求職者：
- 語氣：口語親切像朋友，「這家公司還不錯喔！」
- 關心：薪資福利、特休病假、工時彈性、DEI、職涯發展
- 禁止：學術語言、GRI/TCFD框架縮寫

機構投資人：
- 語氣：專業嚴謹數據導向
- 關心：TCFD氣候風險財務、供應鏈ESG、高階薪酬ESG連結
- 必須：引用具體數字、框架

散戶投資人：
- 語氣：直接口語重點在賺不賺錢
- 關心：獲利能力、AI題材、環保裁罰、配息
- 格式：條列式，✅⚠️符號

ESG從業者：
- 語氣：專業術語咬文嚼字
- 關心：GRI/SASB/TCFD/IFRS S1S2、雙重重大性、確信
- 必須：引用準則條文方法論

回答規則：
- 字數：100~250字
- 來源標註：(2024-p.頁碼)
- 不用「根據以上資料」等套話收尾
        """.strip(),
        "tags": ["persona", "tone", "prompt"],
    },
    {
        "category": "etl",
        "title": "ETL Pipeline",
        "content": """
流程：PDF → Parse → Chunk → Embed → MongoDB + FAISS

關鍵腳本：
- app/etl/run_pipeline.py：完整ETL自動化
- build_faiss_index.py：從MongoDB重建FAISS index

Chunking：500字，50字重疊，PyMuPDF (fitz)
Embedding：bge-m3，batch_size=64，normalize=True，CUDA
MongoDB：upsert防重複（chunk_id為key）
FAISS：IndexFlatL2，存 data/faiss_index/esg.index + id_map.json

擴充公司時步驟：
1. 下載PDF到 data/reports/{公司名}/
2. 執行 run_pipeline.py
3. 執行 build_faiss_index.py 重建index
4. 更新 company_resolver.py 的 COMPANY_MASTER
        """.strip(),
        "tags": ["etl", "pipeline", "embedding", "faiss"],
    },
    {
        "category": "company",
        "title": "公司擴充計畫",
        "content": """
現有：30家（2024年完成）
P1新增：19家（三指數都上榜）- 已下載
- 聯發科、兆豐金、統一、大立光、華碩、元大金、長榮、南亞
- 華南金、聯詠、瑞昱、台泥、緯創、英業達、遠傳、台灣大
- 台化、台塑化、陽明

目標：100家
參考清單：ESG_Company_Download_List.xlsx
優先級：P1(三指數) > P2(兩指數) > P3(一指數) > TSAA獲獎

產業分組（同類型公司功能用）：
半導體製造：台積電、聯電
半導體封測：日月光投控、欣興電子
電子代工：鴻海精密、廣達、佳世達集團
金融銀行：中國信託銀行、台北富邦銀行、玉山金控、永豐銀行、彰化銀行、合作金庫銀行、第一銀行
金控：開發金控、國泰金控、台新金控
石化塑化：台塑、台塑化、台化、南亞
鋼鐵：中鋼公司
水泥建材：亞洲水泥、台泥
紡織：宏遠興業、遠東新世紀
航運：長榮、陽明
電信：中華電信、遠傳、台灣大
        """.strip(),
        "tags": ["company", "expansion", "industry-group"],
    },
]

# 清除舊記憶再寫入
col.delete_many({})

for mem in memories:
    mem["updated_at"] = datetime.now()
    col.insert_one(mem)

print(f"已存入 {len(memories)} 筆專案記憶")
for m in memories:
    print(f"  [{m['category']}] {m['title']}")

client.close()
