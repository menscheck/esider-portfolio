import json
from pathlib import Path
from typing import Dict, List, Set, Any

# Mapping from fetched keywords to tag_rules.py tags
KEYWORD_TO_TAG = {
    "範疇": "碳排放",
    "排放": "碳排放",
    "氣候": "氣候風險",
    "溫室": "碳排放",
    "再生能源": "能源",
    "能源": "能源",
    "水資源": "用水",
    "污染": "空氣污染",
    "廢棄物": "廢棄物",
    "職業": "職業安全",
    "安全": "職業安全",
    "資訊": "資訊安全",
    "治理": "董事會結構",
    "供應鏈": "供應鏈",
    "金融": "永續金融",
    "綠色": "綠色製造",
    "人權": "多元共融",
    "平等": "多元共融",
    "社區": "多元共融",
    "永續": "政策聲明",
    "風險": "風險管理",
    "產品": "產品生命週期",
    "GRI": "法規遵循",
    "SASB": "法規遵循",
    # Additional mappings for unmapped keywords
    "FN": "永續金融",
    "CB": "永續金融",
    "ESG": "法規遵循",
    "轉型": "氣候風險",
    "投融資": "永續金融",
    "赤道": "永續金融",
    "揭露": "法規遵循",
    "衛生": "職業安全",
    "回收": "廢棄物",
    "排放量": "碳排放",
    "氣體": "碳排放"
}

FETCHED_KEYWORDS_FILE = Path(r"c:\Users\Sam Joseph\esg-agent\app\fetched_keywords.json")
TAG_RULES_FILE = Path(r"c:\Users\Sam Joseph\esg-agent\app\core\tag_rules.py")
UNMAPPED_FILE = Path(r"c:\Users\Sam Joseph\esg-agent\app\unmapped_keywords.json")


def load_fetched_keywords() -> List[Dict[str, Any]]:
    """Load fetched_keywords.json"""
    with open(FETCHED_KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_tag_rules() -> Dict[str, List[Any]]:
    """Load TAG_RULES from tag_rules.py"""
    import sys
    sys.path.insert(0, str(TAG_RULES_FILE.parent.parent))
    from core.tag_rules import TAG_RULES
    return TAG_RULES


def map_keywords() -> None:
    """Map fetched keywords to tags and update tag_rules.py"""
    
    # Load data
    fetched_keywords = load_fetched_keywords()
    tag_rules = load_tag_rules()
    
    # Track new keywords per tag
    new_keywords_per_tag: Dict[str, List[str]] = {tag: [] for tag in tag_rules}
    unmapped_keywords = []
    
    for item in fetched_keywords:
        token = item["token"]
        count = item["count"]
        
        # Try exact match first
        mapped_tag = KEYWORD_TO_TAG.get(token)
        
        # If no exact match, try substring match
        if not mapped_tag:
            for keyword, tag in KEYWORD_TO_TAG.items():
                if keyword in token:
                    mapped_tag = tag
                    break
        
        if mapped_tag and mapped_tag in tag_rules:
            # Get existing keywords for this tag
            existing_keywords = set(str(kw) for kw in tag_rules[mapped_tag])
            
            # Only add if not already exists
            if token not in existing_keywords:
                new_keywords_per_tag[mapped_tag].append(token)
                tag_rules[mapped_tag].append(token)
        else:
            unmapped_keywords.append({
                "token": token,
                "count": count
            })
    
    # Print summary
    print("=" * 70)
    print("Keyword Mapping Summary")
    print("=" * 70)
    
    for tag in sorted(tag_rules.keys()):
        if new_keywords_per_tag[tag]:
            print(f"\n{tag} (新增 {len(new_keywords_per_tag[tag])} 個 keywords):")
            for kw in new_keywords_per_tag[tag]:
                print(f"  + {kw}")
    
    # Print final keyword counts per tag
    print("\n" + "=" * 70)
    print("每個 tag 最終 keyword 總數")
    print("=" * 70)
    for tag in sorted(tag_rules.keys()):
        total_keywords = len(tag_rules[tag])
        print(f"{tag}: {total_keywords}")
    
    # Save unmapped keywords
    unmapped_file_path = UNMAPPED_FILE
    unmapped_file_path.write_text(
        json.dumps(unmapped_keywords, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print("\n" + "=" * 70)
    print(f"剩餘無法對應的詞 ({len(unmapped_keywords)} total):")
    print("=" * 70)
    for item in unmapped_keywords:
        print(f"{item['token']}: {item['count']}")
    
    print(f"\nFull unmapped list saved to: {unmapped_file_path}")
    
    # Write updated tag_rules.py
    write_updated_tag_rules(tag_rules)
    print(f"\nUpdated tag_rules.py saved!")


def write_updated_tag_rules(tag_rules: Dict[str, List[Any]]) -> None:
    """Write updated TAG_RULES back to tag_rules.py"""
    
    lines = [
        "TAG_RULES = {\n"
    ]
    
    for i, (tag, keywords) in enumerate(tag_rules.items()):
        # Format keywords list
        kw_strs = []
        for kw in keywords:
            if isinstance(kw, str):
                kw_strs.append(f'"{kw}"')
            else:
                kw_strs.append(str(kw))
        
        kw_list = "[" + ", ".join(kw_strs) + "]"
        
        # Add to lines
        lines.append(f'    "{tag}": {kw_list}')
        if i < len(tag_rules) - 1:
            lines.append(",\n")
        else:
            lines.append("\n")
    
    lines.append("}\n")
    
    TAG_RULES_FILE.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    map_keywords()
