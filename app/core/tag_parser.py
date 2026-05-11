"""
app/core/tag_parser.py
雙軌比對：jieba分詞 + substring
回傳 matched_tags: List[str]
"""

import jieba
try:
    from app.core.tag_rules import TAG_RULES
except ModuleNotFoundError:
    from tag_rules import TAG_RULES


def parse_tags(query: str) -> list[str]:
    """
    輸入使用者查詢文字，回傳匹配的 tag 清單

    比對策略：
    1. substring：query 直接包含 keyword
    2. jieba分詞：query 切詞後任一詞命中 keyword

    Args:
        query: 使用者輸入文字

    Returns:
        matched_tags: List[str]，去重後的 tag 名稱清單
    """
    if not query or not query.strip():
        return []

    query_lower = query.lower()

    # jieba 分詞
    tokens = set(jieba.cut(query_lower))

    matched_tags = []

    for tag, keywords in TAG_RULES.items():
        for kw in keywords:
            kw_lower = kw.lower()
            # 策略1: substring 直接比對
            if kw_lower in query_lower:
                matched_tags.append(tag)
                break
            # 策略2: jieba token 命中
            if kw_lower in tokens:
                matched_tags.append(tag)
                break

    return matched_tags


def parse_tags_with_detail(query: str) -> dict:
    """
    Debug用：回傳每個 tag 命中的 keyword

    Returns:
        {tag: matched_keyword}
    """
    if not query or not query.strip():
        return {}

    query_lower = query.lower()
    tokens = set(jieba.cut(query_lower))
    result = {}

    for tag, keywords in TAG_RULES.items():
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in query_lower or kw_lower in tokens:
                result[tag] = kw
                break

    return result


if __name__ == "__main__":
    tests = [
        "台積電碳排放目標是什麼",
        "員工福利和薪資水準如何",
        "氣候風險管理做了哪些",
        "供應鏈永續採購政策",
        "董事會獨立董事比例",
    ]
    for q in tests:
        tags = parse_tags(q)
        print(f"Q: {q}")
        print(f"  Tags: {tags}")
        print()