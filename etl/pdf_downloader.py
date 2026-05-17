import os
import sys
import json
import re
import asyncio
import urllib.parse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import requests

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from benchmark_companies import COMPANY_INFO

# P1 新增公司（三指數都上榜）
P1_NEW_COMPANIES = [
    "聯發科", "兆豐金", "統一", "大立光", "華碩",
    "元大金", "長榮", "南亞", "華南金", "聯詠",
    "瑞昱", "台泥", "緯創", "英業達", "遠傳",
    "台灣大", "台化", "台塑化", "陽明",
]

TEST_COMPANIES = ["台積電", "玉山金控", "統一超商"] + P1_NEW_COMPANIES
DOWNLOAD_DIR = os.path.join(ROOT_DIR, "data", "reports")
LOG_FILE = os.path.join(ROOT_DIR, "etl", "download_log.json")
TIMEOUT = 5000

STAGE1_TEXT_KEYWORDS = ["報告書", "下載", "download", "report", "pdf", "年報"]
STAGE1_HREF_KEYWORDS = [".pdf", "report", "download"]
PDF_HREF_KEYWORD = ".pdf"

GOOGLE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}


def should_skip(company_name: str, reports_dir: str = "data/reports") -> bool:
    """檢查該公司是否已有 PDF，有則跳過"""
    company_dir = Path(reports_dir) / company_name
    if company_dir.exists():
        pdfs = list(company_dir.glob("*.pdf"))
        if pdfs:
            print(f"[SKIP] {company_name} 已有 {len(pdfs)} 份PDF，跳過")
            return True
    return False


def normalize_url(href, base_url):
    return urllib.parse.urljoin(base_url, href)


def same_domain(url, root_url):
    try:
        parsed = urllib.parse.urlparse(url)
        root = urllib.parse.urlparse(root_url)
        return parsed.scheme in {"http", "https"} and parsed.netloc == root.netloc
    except Exception:
        return False


async def extract_stage1_links(page, base_url):
    anchors = await page.query_selector_all("a[href]")
    entry_links = []
    direct_pdfs = []

    for anchor in anchors:
        href = await anchor.get_attribute("href")
        if not href:
            continue
        text = (await anchor.inner_text()) or ""
        lower_text = text.lower()
        lower_href = href.lower()
        full = f"{lower_text} {lower_href}"

        if any(keyword in full for keyword in STAGE1_TEXT_KEYWORDS) or any(keyword in lower_href for keyword in STAGE1_HREF_KEYWORDS):
            url = normalize_url(href, base_url)
            if PDF_HREF_KEYWORD in lower_href:
                direct_pdfs.append({"href": url, "text": text.strip()})
            else:
                entry_links.append({"href": url, "text": text.strip()})

    return direct_pdfs, entry_links


async def find_pdfs_on_page(page, base_url):
    anchors = await page.query_selector_all("a[href]")
    pdfs = []

    for anchor in anchors:
        href = await anchor.get_attribute("href")
        if not href:
            continue
        lower_href = href.lower()
        if ".pdf" in lower_href:
            url = normalize_url(href, base_url)
            text = (await anchor.inner_text()) or ""
            pdfs.append({"href": url, "text": text.strip()})

    return pdfs


async def find_internal_links(page, base_url, root_url, limit=5):
    anchors = await page.query_selector_all("a[href]")
    links = []
    seen = set()

    for anchor in anchors:
        href = await anchor.get_attribute("href")
        if not href:
            continue
        url = normalize_url(href, base_url)
        if same_domain(url, root_url) and url not in seen:
            seen.add(url)
            if url != base_url:
                links.append(url)
        if len(links) >= limit:
            break

    return links


async def find_download_buttons(page):
    anchors = await page.query_selector_all("a, button, input[type=button], input[type=submit]")
    buttons = []

    for anchor in anchors:
        href = await anchor.get_attribute("href")
        value = await anchor.get_attribute("value") or ""
        text = (await anchor.inner_text()) or value or ""
        if not text:
            continue
        lower = text.lower()
        keywords = ["下載完整報告書", "下載報告書", "下載pdf", "download", "下載完整", "完整報告"]
        if any(keyword in lower for keyword in keywords):
            buttons.append({"element": anchor, "text": text.strip(), "href": href})

    return buttons


async def click_download_button(page, base_url):
    buttons = await find_download_buttons(page)
    print(f"Button策略: 找到 {len(buttons)} 個下載按鈕/連結")
    for idx, btn in enumerate(buttons, 1):
        print(f"  按鈕 {idx}: text={btn['text']} href={btn['href']}")

    if not buttons:
        return None

    button = buttons[0]
    if button["href"] and ".pdf" in button["href"].lower():
        url = normalize_url(button["href"], base_url)
        print(f"直接按鈕 href 發現 PDF: {url}")
        return {"href": url, "text": button["text"]}

    try:
        async with page.expect_download(timeout=3000) as download_info:
            await button["element"].click()
        download = await download_info.value
        download_url = download.url
        print(f"攔截到下載事件: {download_url}")
        return {"href": download_url, "text": button["text"]}
    except Exception as e:
        print(f"按鈕點擊未觸發下載: {e}")
        try:
            await page.wait_for_timeout(3000)
            current_url = page.url
            if current_url.lower().endswith(".pdf"):
                print(f"導航至 PDF: {current_url}")
                return {"href": current_url, "text": button["text"]}
        except Exception:
            pass

    return None


async def scan_page_source_for_pdfs(page, base_url):
    content = await page.content()
    patterns = [
        r"https?://[^\s\"'<>]+\.pdf",
        r"['\"]([^'\"]*\.pdf)['\"]",
        r"url\s*:\s*['\"]([^'\"]*\.pdf)['\"]"
    ]
    found_urls = set()

    for pattern in patterns:
        for match in re.findall(pattern, content, flags=re.IGNORECASE):
            if isinstance(match, tuple):
                match = match[0]
            if not match:
                continue
            href = match.strip()
            if href.startswith(("http://", "https://")):
                full_url = href
            else:
                full_url = normalize_url(href, base_url)

            parsed = urllib.parse.urlparse(full_url)
            if parsed.path.lower().endswith(".pdf"):
                found_urls.add(full_url)

    pdfs = [{"href": url, "text": "source_scan"} for url in found_urls]
    return pdfs


def get_file_name_from_url(url):
    path = urllib.parse.urlparse(url).path
    filename = os.path.basename(path)
    return filename.lower()


def has_year(filename):
    years = re.findall(r"20(\d{2})", filename)
    if not years:
        return None
    years = [int(year) for year in years]
    return min(years)


def contains_keywords(filename):
    keywords = ["永續報告", "esg報告", "csr報告", "sustainability report"]
    lower = filename.lower()
    return any(keyword in lower for keyword in keywords)


def is_traditional_chinese(filename):
    markers = ["_c", "_zh", "_tw", "chinese", "繁中", "中文"]
    lower = filename.lower()
    return any(marker in lower for marker in markers)


def is_excluded_pdf(filename):
    exclude_markers = ["tcfd", "tnfd", "english", "_e_", "_en_"]
    lower = filename.lower()
    if any(marker in lower for marker in exclude_markers):
        return True
    year = has_year(lower)
    if year and year < 2022:
        return True
    return False


def score_pdf_candidate(pdf):
    href = pdf.get("href", "")
    text = pdf.get("text", "")
    filename = get_file_name_from_url(href)
    combined = f"{filename} {text.lower()}"

    if is_excluded_pdf(combined):
        return -9999, "排除條件"

    score = 0
    reason_parts = []
    year = has_year(combined)
    has_keyword = contains_keywords(combined)
    lang = is_traditional_chinese(combined)

    if year in {2023, 2024}:
        score += 100
        reason_parts.append(f"年份{year}")
    elif year:
        score += 10
        reason_parts.append(f"年份{year}")

    if has_keyword:
        score += 50
        reason_parts.append("包含報告關鍵字")

    if lang:
        score += 20
        reason_parts.append("繁體中文標記")

    if year in {2023, 2024} and has_keyword and lang:
        score += 200
        reason_parts.append("最高優先級1")
    elif year in {2023, 2024}:
        score += 150
        reason_parts.append("優先級2")
    elif has_keyword:
        score += 75
        reason_parts.append("優先級3")

    if score == 0:
        reason_parts.append("無明顯優先條件")

    return score, "; ".join(reason_parts)


def choose_best_pdf_candidate(candidates):
    scored = []
    for pdf in candidates:
        score, reason = score_pdf_candidate(pdf)
        pdf["score"] = score
        pdf["reason"] = reason
        scored.append(pdf)

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def google_search_first_pdf(company_name):
    query = f"{company_name} ESG永續報告書 2024 filetype:pdf"
    print(f"Google fallback 查詢: {query}")
    search_url = "https://www.google.com/search"
    params = {"q": query, "hl": "zh-TW"}

    try:
        resp = requests.get(search_url, params=params, headers=GOOGLE_HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text

        matches = re.findall(r'/url\?q=(https?://[^&]+?\.pdf)&', html)
        if matches:
            first_pdf = urllib.parse.unquote(matches[0])
            print(f"Google fallback 找到 PDF: {first_pdf}")
            return first_pdf
    except Exception as e:
        print(f"Google fallback 失敗: {e}")

    return None


async def download_pdf(url, company, index, company_dir):
    filename = f"{company}_{index+1}.pdf"
    filepath = os.path.join(company_dir, filename)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        return {
            "url": url,
            "filename": filename,
            "status": "success",
            "download_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "url": url,
            "filename": filename,
            "status": f"error: {str(e)}",
            "download_time": datetime.now().isoformat()
        }


async def download_pdfs():
    print("=" * 50)
    print("下載預覽：")
    for company in TEST_COMPANIES:
        status = "SKIP" if should_skip(company) else "DOWNLOAD"
        print(f"  [{status}] {company}")
    print("=" * 50)
    input("確認後按 Enter 開始...")

    download_log = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for company in TEST_COMPANIES:
            if should_skip(company):
                continue
            company_info = COMPANY_INFO.get(company)
            if not company_info or company_info["ESG報告書URL"] == "待補充":
                print(f"{company}: 無有效URL，跳過")
                download_log[company] = {"status": "skip", "reason": "無有效ESG URL", "download_time": datetime.now().isoformat()}
                continue

            homepage = company_info["ESG報告書URL"]
            print(f"\n==== {company} ====")
            print(f"ESG首頁: {homepage}")

            company_dir = os.path.join(DOWNLOAD_DIR, company)
            os.makedirs(company_dir, exist_ok=True)
            company_log = {}
            pdf_candidates = []
            playwright_error = None
            stage_used = None

            current_url = homepage
            try:
                await page.goto(homepage, timeout=TIMEOUT)
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                current_url = page.url

                direct_pdfs, entry_links = await extract_stage1_links(page, homepage)
                print(f"Stage1: 首頁找到 {len(direct_pdfs)} 直接PDF, {len(entry_links)} 個報告書/下載入口")
                stage_used = None

                if direct_pdfs:
                    pdf_candidates.extend(direct_pdfs)
                    stage_used = "Stage1"

                source_pdfs = await scan_page_source_for_pdfs(page, current_url)
                new_source_pdfs = [pdf for pdf in source_pdfs if pdf["href"] not in [x["href"] for x in pdf_candidates]]
                if new_source_pdfs:
                    pdf_candidates.extend(new_source_pdfs)
                    print(f"Stage2: 原始碼掃描找到 {len(new_source_pdfs)} 個 PDF")
                    if not stage_used:
                        stage_used = "Stage2"

                if entry_links:
                    print("Stage1.5: 使用報告入口連結進行內部頁面搜尋")
                    print("Stage1 入口連結:")
                    for entry in entry_links:
                        print(f"  - {entry['text']} -> {entry['href']}")

                    level_links = [entry["href"] for entry in entry_links][:5]
                    visited = {homepage}
                    next_level = []

                    for level in range(1, 3):
                        if not level_links:
                            break
                        print(f"Stage1.5: 第 {level} 層，處理 {len(level_links)} 個連結")
                        for link in level_links:
                            if link in visited:
                                continue
                            visited.add(link)
                            print(f"  訪問: {link}")
                            try:
                                await page.goto(link, timeout=TIMEOUT)
                                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                                current_url = page.url
                                page_pdfs = await find_pdfs_on_page(page, link)
                                print(f"    找到 {len(page_pdfs)} 個PDF")
                                for pdf in page_pdfs:
                                    if pdf["href"] not in [x["href"] for x in pdf_candidates]:
                                        pdf_candidates.append(pdf)
                                        if not stage_used:
                                            stage_used = "Stage1"
                                if level < 2:
                                    child_links = await find_internal_links(page, link, homepage, limit=5)
                                    print(f"    擴展 {len(child_links)} 個內部連結")
                                    for child in child_links:
                                        if child not in visited and child not in next_level and len(next_level) < 5:
                                            next_level.append(child)
                            except Exception as e:
                                print(f"    連結錯誤: {e}")
                        level_links = next_level

            except Exception as e:
                print(f"{company}: Playwright 讀取失敗 - {e}")
                playwright_error = str(e)
                company_log["error"] = str(e)

            if not pdf_candidates:
                print("Stage3: 嘗試按鈕下載策略")
                button_pdf = await click_download_button(page, current_url)
                if button_pdf:
                    pdf_candidates.append(button_pdf)
                    stage_used = stage_used or "Stage3"
                    print(f"Button策略新增候選 PDF: {button_pdf['href']}")
                else:
                    print("Button策略未找到可下載 PDF")

            if not pdf_candidates:
                print("Stage4: 嘗試 Google fallback")
                google_pdf = google_search_first_pdf(company)
                if google_pdf:
                    pdf_candidates.append({"href": google_pdf, "text": "Google fallback"})
                    stage_used = stage_used or "Stage4"
                else:
                    print("Google fallback 也未找到 PDF")

            print(f"本次找到 PDF 的階段: {stage_used or 'None'}")

            print(f"總共候選PDF: {len(pdf_candidates)}")
            scored_candidates = choose_best_pdf_candidate(pdf_candidates)
            for idx, candidate in enumerate(scored_candidates, start=1):
                print(f"  候選 {idx}: {candidate['href']} score={candidate['score']} reason={candidate['reason']}")

            if scored_candidates and scored_candidates[0]["score"] > 0:
                chosen = scored_candidates[0]
                print(f"最終選擇: {chosen['href']} 原因: {chosen['reason']}")
                result = await download_pdf(chosen["href"], company, 0, company_dir)
                company_log[result["filename"]] = result
            else:
                print("未選擇任何PDF下載")
                company_log["status"] = "no_pdf_found"
                company_log["download_time"] = datetime.now().isoformat()

            download_log[company] = company_log

        await browser.close()

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(download_log, f, ensure_ascii=False, indent=2)

    print("下載完成，詳見 etl/download_log.json")


if __name__ == "__main__":
    asyncio.run(download_pdfs())