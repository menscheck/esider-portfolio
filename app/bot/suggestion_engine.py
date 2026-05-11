"""
app/bot/suggestion_engine.py
用 LLM 動態生成延伸問題、同類型公司、推薦問題
"""

import json
from openai import AzureOpenAI
from app.core.config import get_config
from app.core.company_resolver import INDUSTRY_GROUPS, COMPANY_MASTER


def _get_client():
    cfg = get_config()["azure_openai"]
    return AzureOpenAI(
        azure_endpoint=cfg["endpoint"],
        api_key=cfg["api_key"],
        api_version=cfg["api_version"],
    ), cfg["deployment"]


def generate_followup_questions(
    company: str,
    last_query: str,
    persona_name: str,
    exclude: set[str] | None = None,
    include_broad: bool = False,
    query_type: str = "esg",  # "esg" 或 "finmind"
) -> list[str]:
    client, deployment = _get_client()

    exclude_questions = list(exclude or [])
    persona_style = {
        "求職者": "口語親切，像朋友問問題，關心薪資福利工時職涯",
        "機構投資人": "專業嚴謹，用法人語氣，關心財務風險數據框架",
        "散戶投資人": "直接口語，關心賺不賺錢有沒有雷，短句",
        "ESG從業者": "專業術語，關心方法論框架準則細節",
    }
    style = persona_style.get(persona_name, "口語親切")

    # query_type 決定延伸問題切入點（finmind 走台股即時財務；esg 走永續/方法論）
    if query_type == "finmind":
        focus = {
            "散戶投資人": "股價走勢、成交量、法人動向、技術面、近期漲跌、配息、本益比",
            "機構投資人": "財務比率ROE/ROA/ROIC、自由現金流、資本支出、營收YoY/MoM、法人買超",
        }.get(persona_name, "股價財務即時數據")
        broad_instruction = (
            f"- 問題3：從{company}本題提到的財務/市場重點提煉一個具體指標，跨公司問是否也相似，20字以內"
        )
    else:
        focus = {
            "求職者": "薪資福利工時職涯",
            "機構投資人": "氣候風險財務衝擊TCFD供應鏈ESG",
            "散戶投資人": "ESG風險環保罰單永續競爭力",
            "ESG從業者": "方法論框架準則細節",
        }.get(persona_name, "ESG永續報告書")

        if include_broad:
            broad_instruction = (
                f"- 問題3：從回答內容提取一個具體特點，生成跨公司廣泛型問題，格式："
                f"「還有哪些公司也有[具體特點]？」，20字以內"
            )
        else:
            broad_instruction = (
                f"- 問題3：同樣針對「{company}」，符合{persona_name}語氣與關心點，15字以內"
            )

    prompt = f"""使用者身份：{persona_name}（{style}）
切入重點：{focus}
剛才查詢：{last_query}
公司：{company}
已問過（不得重複）：{list(exclude_questions)}

請生成3個延伸問題：
- 問題1、問題2：針對「{company}」，符合{persona_name}語氣與切入重點，15字以內
{broad_instruction}

繁體中文，只回傳JSON陣列：["問題1", "問題2", "問題3"]"""

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        defaults = {
            "求職者": [f"{company}薪資市場競爭力如何？", f"{company}特休幾天？", f"{company}有彈性上班嗎？"],
            "機構投資人": [f"{company}TCFD氣候風險量化？", f"{company}高階薪酬ESG連結機制？", f"{company}供應鏈稽核涵蓋率？"],
            "散戶投資人": [f"{company}最近獲利如何？", f"{company}有沒有環保罰單？", f"{company}配息穩定嗎？"],
            "ESG從業者": [f"{company}GRI揭露完整度？", f"{company}第三方確信機構？", f"{company}雙重重大性方法？"],
        }
        return defaults.get(persona_name, [f"{company}ESG表現", f"{company}風險管理", f"{company}永續目標"])


def generate_similar_companies(
    company: str,
    last_query: str,
) -> list[str]:
    available = [c for c in COMPANY_MASTER.keys() if c != company]

    # 找同產業
    same_industry = []
    for group, members in INDUSTRY_GROUPS.items():
        if company in members:
            same_industry = [c for c in members if c != company]
            break

    if len(same_industry) >= 2:
        return same_industry[:3]

    # 同產業不足，用跨產業相近邏輯
    cross_map = {
        "台塑": ["中鋼公司", "亞洲水泥", "遠東新世紀"],
        "中鋼公司": ["台塑", "亞洲水泥", "榮成紙業"],
        "亞洲水泥": ["台塑", "中鋼公司", "榮成紙業"],
        "榮成紙業": ["亞洲水泥", "中鋼公司", "宏遠興業"],
        "長榮航空": ["統一超商", "中華電信", "台達電"],
        "南山產物": ["國泰金控", "開發金控", "台新金控"],
    }
    if company in cross_map:
        return cross_map[company]

    # fallback：排除自己，取前3
    return available[:3]


def generate_persona_questions(persona_name: str) -> list[str]:
    import random
    available = list(COMPANY_MASTER.keys())
    
    # 每次隨機挑3家不同公司
    selected_companies = random.sample(available, 3)
    
    client, deployment = _get_client()
    prompt = f"""使用者身份：{persona_name}

這次要針對這3家公司各出1題：{selected_companies[0]}、{selected_companies[1]}、{selected_companies[2]}

各角色切入點：
- 求職者：薪資、特休、加班文化、職涯發展、員工福利（口語親切）
- 機構投資人：氣候風險、供應鏈ESG、高階薪酬連結、TCFD（專業嚴謹）
- 散戶投資人：獲利、配息、環保罰單、AI題材、黑天鵝（直接口語）
- ESG從業者：GRI揭露、雙重重大性、第三方確信、IFRS S2（專業術語）

請針對{persona_name}，用符合該角色語氣，為每家公司各出1個問題。
每題20字以內，問題要帶公司名稱，繁體中文。

只回傳JSON陣列：["問題1", "問題2", "問題3"]"""

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.9,  # 高溫增加多樣性
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        defaults = {
            "求職者": [
                f"{selected_companies[0]}新人薪資大概多少？",
                f"{selected_companies[1]}特休幾天？",
                f"{selected_companies[2]}加班文化嚴重嗎？"
            ],
            "機構投資人": [
                f"{selected_companies[0]}TCFD氣候風險量化？",
                f"{selected_companies[1]}供應鏈ESG稽核涵蓋率？",
                f"{selected_companies[2]}高階薪酬ESG連結機制？"
            ],
            "散戶投資人": [
                f"{selected_companies[0]}今年獲利如何？",
                f"{selected_companies[1]}配息穩定嗎？",
                f"{selected_companies[2]}有沒有環保罰單？"
            ],
            "ESG從業者": [
                f"{selected_companies[0]}GRI揭露完整度？",
                f"{selected_companies[1]}雙重重大性採用何方法？",
                f"{selected_companies[2]}第三方確信機構為何？"
            ],
        }
        return defaults.get(persona_name, defaults["求職者"])
