import json
import re
from collections import Counter
from pathlib import Path

import jieba

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


STOPWORDS = {
    # 基础停用词
    "的", "是", "在", "有", "與", "及",
    # 问卷格式词、无意义高频词
    "公司", "為何", "對應", "管理", "議題", "指標", "是否", "模組", "本年度",
    "章節", "自訂", "比例", "針對", "實績", "如何", "報告", "準則", "重大",
    "評估", "核心", "問卷", "提供", "使用", "策略", "哪些", "衝擊", "事件",
    "企業", "調查", "目標", "環境", "主題", "機制", "具體", "流程", "服務",
    "整體", "進行", "設定", "員工", "內部", "包含", "發生", "客戶", "社會",
    "整合", "系統", "直接", "發展", "金額", "原則", "揭露", "設計", "營收",
    "營運", "地區", "基礎", "商業", "行業", "方法", "計畫", "數量", "納入",
    "壓力", "雙重", "明貴", "台新", "新世紀", "銀行", "部位"
}

# Local files
LOCAL_FILES = [
    Path(__file__).resolve().parent.parent.parent / "report" / "台新金控SASB問卷.txt",
    Path(__file__).resolve().parent.parent.parent / "report" / "#台新金控 (Taishin FHC) 雙重重大性分析與永續問卷系統.txt",
    Path(__file__).resolve().parent.parent.parent / "report" / "遠東新世紀_重大性分析問卷.txt",
    Path(__file__).resolve().parent.parent.parent / "report" / "遠東新世紀SASB問卷.txt",
]

# Web sources (will use playwright)
WEB_SOURCES = [
    "https://esg.tsmc.com/zh-TW/update/sustainableEnvironment/climateStrategy/index.html",
    "https://www.cathayholdings.com/holdings/esg/esg-report",
    "https://www.globalreporting.org/how-to-use-the-gri-standards/gri-standards-english-language/",
]

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "fetched_keywords.json"


def read_local_text(file_path: Path) -> str:
    """Read local text file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, UnicodeDecodeError) as exc:
        print(f"Warning: failed to read {file_path}: {exc}")
        return ""


def fetch_page_text_playwright(url: str) -> str:
    """Fetch page text using Playwright"""
    if not HAS_PLAYWRIGHT:
        print(f"Warning: Playwright not installed, skipping {url}")
        return ""
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)  # Wait 2 seconds for JS rendering
            text = page.content()
            browser.close()
            # Remove HTML tags
            text = re.sub(r"<[^>]+>", " ", text)
            return text
    except Exception as exc:
        print(f"Warning: failed to fetch {url} with Playwright: {exc}")
        return ""


def normalize_text(text: str) -> str:
    # 移除標點與數字，只保留中文與英文
    cleaned = re.sub(r"[0-9０-９]+", " ", text)
    cleaned = re.sub(r"[\,\.!\?\-\_\/\:\;\"\'\(\)\[\]\{\}\<\>\|\@\#\$\%\^\&\*\~\`\+=]+", " ", cleaned)
    # fallback for punctuation with ascii classes
    cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_valid_token(token: str) -> bool:
    if not token:
        return False
    if token in STOPWORDS:
        return False
    if token.isupper() and len(token) >= 2 and token.isalpha():
        return True
    # 全中文詞，至少 2 個字
    if all("\u4e00" <= ch <= "\u9fff" for ch in token) and len(token) >= 2:
        return True
    return False


def extract_keywords_from_text(text: str) -> Counter:
    normalized = normalize_text(text)
    tokens = list(jieba.cut(normalized))
    valid_tokens = [token for token in tokens if is_valid_token(token)]
    return Counter(valid_tokens)


def main(use_web: bool = False) -> None:
    """
    Fetch and analyze keywords from local and optionally web sources
    
    Args:
        use_web: If True, also fetch from web sources using Playwright
    """
    combined_text = []

    # Read local files
    print("Reading local files...")
    for file_path in LOCAL_FILES:
        if file_path.exists():
            print(f"  Reading {file_path.name}...")
            text = read_local_text(file_path)
            combined_text.append(text)
        else:
            print(f"  Warning: {file_path.name} not found")

    # Optionally fetch from web
    if use_web:
        print("\nFetching web sources with Playwright...")
        for url in WEB_SOURCES:
            print(f"  Fetching {url}...")
            text = fetch_page_text_playwright(url)
            if text:
                combined_text.append(text)

    corpus = "\n".join(combined_text)
    counter = extract_keywords_from_text(corpus)

    filtered = [(token, count) for token, count in counter.items() if count >= 3]
    filtered.sort(key=lambda x: x[1], reverse=True)

    top100 = filtered[:100]
    print("\nTop 100 high-frequency tokens:")
    if top100:
        for token, count in top100:
            print(f"{token}: {count}")
    else:
        print("No tokens met the threshold of frequency >= 3.")

    output_data = [{"token": token, "count": count} for token, count in top100]
    OUTPUT_FILE.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved fetched keywords to: {OUTPUT_FILE}")


if __name__ == "__main__":
    # Run with local files only by default
    # Change use_web=True to also fetch from web sources
    main(use_web=False)


