import json

def _load_company_list():
    try:
        with open("app/data/company_list.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

_company_list = _load_company_list()

def parse_query(query: str) -> dict:
    # 簡單解析
    company_names = []
    for c in _company_list:
        alias_words = c["alias"].split()
        if any(word in query for word in alias_words):
            company_names.append(c["name"])

    metric = None
    metric_keywords = ["碳排", "用水", "工傷", "薪酬", "減碳", "水資源", "福利"]
    for kw in metric_keywords:
        if kw in query:
            metric = kw
            break

    intent = "trend"
    if "比" in query or "高於" in query or "比較" in query:
        intent = "comparison"
    elif "多少" in query or "是多少" in query:
        intent = "single"

    return {
        "company_names": company_names,
        "metric": metric,
        "intent": intent
    }