import jieba
from app.core.tag_rules import TAG_RULES
from typing import List


def parse_tags(query: str) -> List[str]:
    """
    根據輸入的使用者問題，匹配 TAG_RULES 中的 keywords
    
    邏輯：
    1. 先用 jieba 分詞把問題切成詞列表
    2. 對每個 tag 的 keywords 做比對：
       - keyword 長度 == 1：只有在分詞結果中完整出現才算命中
       - keyword 長度 >= 2：維持 substring 比對（在原始 query 中搜尋）
    3. 回傳命中的 tag list
    
    Args:
        query (str): 使用者問題
        
    Returns:
        List[str]: 命中的所有 tag 列表
    """
    matched_tags = set()
    
    # 用 jieba 分詞
    segmented_words = list(jieba.cut(query))
    
    # 遍歷所有 tag 和它們的 keywords
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            # 轉換為字串進行比對（處理數字類型的 keyword）
            keyword_str = str(keyword)
            
            # 根據 keyword 長度選擇匹配策略
            if len(keyword_str) == 1:
                # 單字 keyword：只有在分詞結果中完整出現才算命中
                if keyword_str in segmented_words:
                    matched_tags.add(tag)
                    break
            else:
                # 多字 keyword：substring 比對（在原始 query 中搜尋）
                if keyword_str in query:
                    matched_tags.add(tag)
                    break
    
    return sorted(list(matched_tags))


if __name__ == "__main__":
    # 測試五句話
    test_queries = [
        "這家公司員工薪資水準如何？",
        "廢水處理量是多少？",
        "台積電用水量？",
        "台積電去年碳排放量是多少？",
        "有沒有設定2030年的減碳目標？"
    ]
    
    expected_results = [
        ['薪酬'],
        ['用水'],
        ['用水'],
        ['碳排放'],
        ['目標設定', '碳排放']
    ]
    
    print("=" * 70)
    print("Tag Parser (Jieba 分詞版) 測試結果")
    print("=" * 70)
    for query, expected in zip(test_queries, expected_results):
        tags = parse_tags(query)
        match_status = "✓" if tags == expected else "✗"
        segmented = list(jieba.cut(query))
        
        print(f"\n{match_status} 查詢: {query}")
        print(f"  分詞結果: {segmented}")
        print(f"  預期: {expected}")
        print(f"  實際: {tags}")


