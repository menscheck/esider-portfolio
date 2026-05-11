from openai import AzureOpenAI
import os

from app.services.role_intent_map import ROLE_PILLAR_INTENT_MAP, ROLE_PRIORITY_INTENTS

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")


def _prefilter_intents(query: str, options: list[str]) -> str | None:
    keyword_map = {
        "薪資": "workforce_compensation",
        "薪水": "workforce_compensation",
        "中位數": "workforce_compensation",
        "離職": "workforce_turnover",
        "流動率": "workforce_turnover",
        "訓練": "training_development",
        "培訓": "training_development",
        "霸凌": "harassment_ethics",
        "騷擾": "harassment_ethics",
        "申訴": "grievance_mechanism",
        "檢舉": "grievance_mechanism",
        "持股": "executive_shareholding",
        "股權": "executive_shareholding",
    }

    for k, v in keyword_map.items():
        if k in query and v in options:
            return v

    return None


def _get_client():
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


def _llm_pick(query: str, options: list[str], instruction: str) -> str:
    prompt = f"""
你是一個ESG查詢分類器。
{instruction}

問題：
{query}

可選分類：
{", ".join(options)}

只回傳一個分類名稱，不要其他文字。
"""
    response = _get_client().chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    picked = (response.choices[0].message.content or "").strip()
    return picked if picked in options else options[0]


def classify_role(query: str) -> str:
    options = list(ROLE_PILLAR_INTENT_MAP.keys())
    try:
        return _llm_pick(query, options, "請先判斷提問者角色。")
    except Exception:
        return "investor"


def classify_pillar(query: str, role: str) -> str:
    role_map = ROLE_PILLAR_INTENT_MAP.get(role, {})
    options = list(role_map.keys()) or ["E", "S", "G"]
    try:
        return _llm_pick(query, options, "請判斷問題最主要屬於 E/S/G 哪一個面向。")
    except Exception:
        return "G"


def classify_intent(query: str, role: str, pillar: str) -> str:
    role_map = ROLE_PILLAR_INTENT_MAP.get(role, {})
    pillar_map = role_map.get(pillar, {})
    options = pillar_map.get("intents", []) or ROLE_PRIORITY_INTENTS.get(role, []) or ["general"]

    pre = _prefilter_intents(query, options)
    if pre:
        return pre

    try:
        return _llm_pick(query, options, "請在指定 intent 清單中選最貼近的一項。")
    except Exception:
        return options[0]


def classify_query(query: str) -> dict:
    role = classify_role(query)
    pillar = classify_pillar(query, role)
    intent = classify_intent(query, role, pillar)
    return {"role": role, "pillar": pillar, "intent": intent}


class IntentClassifier:

    def __init__(self):
        self.intent_map = {
            "薪酬": "workforce_compensation",
            "福利": "workforce_compensation",
            "薪資": "workforce_compensation",
            "減碳": "climate_strategy",
            "碳排": "climate_strategy",
            "排放": "climate_strategy",
            "水": "water_management",
            "水資源": "water_management",
        }

    def classify(self, query: str):
        for k, v in self.intent_map.items():
            if k in query:
                return v

        return "unknown"
