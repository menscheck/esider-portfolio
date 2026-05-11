def build_vector_query(query: str, company: dict, intent: str, intent_map: dict):
    meta = intent_map.get(intent, {})

    return f"""
公司：{company.get('name')}
使用者問題：{query}
ESG主題：{meta.get('query', '')}

請找出與此最相關的揭露段落與數據
"""

