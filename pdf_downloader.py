import os
import json
import re
import asyncio
import urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup
from benchmark_companies import COMPANY_INFO

# 測試公司列表
TEST_COMPANIES = list(COMPANY_INFO.keys())

# 關鍵字篩選
KEYWORDS = ["永續", "ESG", "CSR", "sustainability", "report", "報告"]

# 下載目錄
DOWNLOAD_DIR = "data/reports"
LOG_FILE = "etl/download_log.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

PDF_PATTERN = re.compile(r"https?://[^\s\"'<>]+\.pdf", re.IGNORECASE)


def normalize_url(href, base_url):
    return urllib.parse.urljoin(base_url, href)


def find_pdf_candidates_from_html(html, base_url):
    candidates = []
    seen = set()

    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        text = anchor.get_text(separator=" ").strip()
        if ".pdf" in href.lower():
            url = normalize_url(href, base_url)
            key = url.lower()
            if key in seen:
                continue
            seen.add(key)
            full_text = f"{text} {href}".lower()
            if any(keyword.lower() in full_text for keyword in KEYWORDS):
                candidates.append({"href": url, "text": text})

    for match in PDF_PATTERN.findall(html):
        url = match.strip()
        if url.lower() not in seen:
            seen.add(url.lower())
            candidates.append({"href": url, "text": "source_scan"})

    return candidates


async def stage0_static_fetch(url):
    print("Stage0: 嘗試 requests 靜態抓取")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        pdfs = find_pdf_candidates_from_html(response.text, url)
        print(f"Stage0: 找到 {len(pdfs)} 個 PDF 候選")
        return pdfs
    except Exception as e:
        print(f"Stage0 失敗: {e}")
        return []


async def stage1_playwright_links(page, base_url):
    print("Stage1: Playwright 直接搜尋 a[href] PDF")
    anchors = await page.query_selector_all("a[href$='.pdf']")
    candidates = []
    for anchor in anchors:
        href = await anchor.get_attribute("href")
        if not href:
            continue
        text = (await anchor.inner_text()) or ""
        url = normalize_url(href, base_url)
        full_text = f"{text} {href}".lower()
        if any(keyword.lower() in full_text for keyword in KEYWORDS):
            candidates.append({"href": url, "text": text.strip()})
    print(f"Stage1: 找到 {len(candidates)} 個符合關鍵字的 PDF")
    return candidates


async def stage2_source_scan(page, base_url):
    print("Stage2: Playwright 原始碼掃描 PDF")
    content = await page.content()
    pdf_urls = set()
    for match in PDF_PATTERN.findall(content):
        pdf_urls.add(match.strip())
    candidates = [{"href": normalize_url(url, base_url), "text": "source_scan"} for url in pdf_urls]
    print(f"Stage2: 找到 {len(candidates)} 個 PDF")
    return candidates


async def stage_expand_result(page):
    """點擊查詢結果頁面的展開按鈕（圓形下箭頭），讓內容顯示出來。"""
    expand_selectors = [
        'button.collapse-btn',
        'button[class*="collapse"]',
        'button[class*="expand"]',
        '.query-result button',
        'div[class*="result"] button:first-child',
        'svg[data-icon="chevron-down"]',
    ]
    for selector in expand_selectors:
        try:
            btn = await page.query_selector(selector)
            if btn:
                print(f"Stage_expand: 找到展開按鈕 [{selector}]")
                await btn.click()
                await page.wait_for_timeout(1500)
                content = await page.content()
                if '中文版報告書' in content or '永續' in content:
                    print("Stage_expand: 展開成功，內容已顯示")
                else:
                    print("Stage_expand: 點擊後未偵測到預期內容")
                return
        except Exception:
            continue

    # 若上方 selector 均未命中，印出所有按鈕 class 供診斷
    print("Stage_expand: 未找到展開按鈕，列出頁面所有 button class：")
    buttons = await page.query_selector_all('button')
    for btn in buttons:
        cls = await btn.get_attribute('class')
        print(f"  button class: {cls}")


async def stage3_click_button(page, base_url):
    print("Stage3: Playwright 嘗試下載按鈕")
    selectors = ["a", "button", "input[type=button]", "input[type=submit]"]
    keywords = ["下載完整報告書", "下載報告書", "下載pdf", "download", "下載完整", "完整報告", "PDF"]
    elements = []

    for selector in selectors:
        for element in await page.query_selector_all(selector):
            text = (await element.inner_text()) or (await element.get_attribute("value") or "")
            if not text:
                continue
            if any(keyword.lower() in text.lower() for keyword in keywords):
                elements.append((element, text.strip()))

    print(f"Stage3: 找到 {len(elements)} 個可能的按鈕或連結")
    for element, text in elements:
        href = await element.get_attribute("href")
        if href and ".pdf" in href.lower():
            url = normalize_url(href, base_url)
            print(f"Stage3: 按鈕 href 發現 PDF {url}")
            return [{"href": url, "text": text}]

        try:
            async with page.expect_download(timeout=5000) as download_info:
                await element.click()
            download = await download_info.value
            print(f"Stage3: 攔截到下載事件 {download.url}")
            return [{"href": download.url, "text": text}]
        except Exception as e:
            print(f"Stage3: 按鈕點擊未觸發下載: {e}")
            try:
                await page.wait_for_timeout(3000)
                current_url = page.url
                if current_url.lower().endswith(".pdf"):
                    print(f"Stage3: 導航到 PDF {current_url}")
                    return [{"href": current_url, "text": text}]
            except Exception:
                pass

    return []


def stage4_google_fallback(company):
    print("Stage4: Google fallback")
    query = f"{company} ESG永續報告書 2024 filetype:pdf"
    search_url = "https://www.google.com/search"
    params = {"q": query, "hl": "zh-TW"}
    try:
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text
        matches = re.findall(r'/url\?q=(https?://[^&]+?\.pdf)&', html)
        if matches:
            url = urllib.parse.unquote(matches[0])
            print(f"Stage4: Google fallback 找到 {url}")
            return [{"href": url, "text": "Google fallback"}]
    except Exception as e:
        print(f"Stage4 失敗: {e}")
    return []


def choose_best_candidate(candidates):
    if not candidates:
        return None
    for candidate in candidates:
        candidate["score"] = 0
        text = candidate.get("text", "").lower()
        href = candidate.get("href", "").lower()
        content = f"{text} {href}"
        if any(keyword.lower() in content for keyword in KEYWORDS):
            candidate["score"] += 50
        if ".pdf" in href:
            candidate["score"] += 10
        if any(year in href for year in ["2024", "2023"]):
            candidate["score"] += 20
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0]


async def download_pdf(url, company, index, company_dir):
    filename = f"{company}_{index+1}.pdf"
    filepath = os.path.join(company_dir, filename)
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
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
    download_log = {}
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        for company in TEST_COMPANIES:
            company_info = COMPANY_INFO.get(company)
            if not company_info or company_info["ESG報告書URL"] == "待補充":
                print(f"{company}: 無有效URL，跳過")
                download_log[company] = {"status": "skip", "reason": "無有效ESG URL", "download_time": datetime.now().isoformat()}
                results.append((company, "失敗", "Skip", "N/A"))
                continue

            url = company_info["ESG報告書URL"]
            print(f"\n==== {company} ====")
            print(f"處理 URL: {url}")

            company_dir = os.path.join(DOWNLOAD_DIR, company)
            os.makedirs(company_dir, exist_ok=True)
            company_log = {}
            pdf_candidates = []
            stage_used = None

            static_candidates = await stage0_static_fetch(url)
            if static_candidates:
                pdf_candidates.extend(static_candidates)
                stage_used = "Stage0"

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state('networkidle')
                await stage_expand_result(page)

                if not pdf_candidates:
                    stage1_candidates = await stage1_playwright_links(page, url)
                    if stage1_candidates:
                        pdf_candidates.extend(stage1_candidates)
                        stage_used = "Stage1"

                if not pdf_candidates:
                    stage2_candidates = await stage2_source_scan(page, url)
                    if stage2_candidates:
                        pdf_candidates.extend(stage2_candidates)
                        stage_used = "Stage2"

                if not pdf_candidates:
                    stage3_candidates = await stage3_click_button(page, url)
                    if stage3_candidates:
                        pdf_candidates.extend(stage3_candidates)
                        stage_used = "Stage3"

            except Exception as e:
                print(f"{company}: Playwright 讀取失敗 - {e}")
                company_log["error"] = str(e)

            if not pdf_candidates:
                pdf_candidates.extend(stage4_google_fallback(company))
                if pdf_candidates and not stage_used:
                    stage_used = "Stage4"

            print(f"本次找到 PDF 階段: {stage_used or 'None'}")
            print(f"候選 PDF 數量: {len(pdf_candidates)}")

            chosen = choose_best_candidate(pdf_candidates)
            if chosen:
                print(f"下載候選: {chosen['href']}")
                result = await download_pdf(chosen["href"], company, 0, company_dir)
                company_log[result["filename"]] = result
            else:
                print("未找到可下載 PDF")
                company_log["status"] = "no_pdf_found"
                company_log["download_time"] = datetime.now().isoformat()

            download_log[company] = company_log

            # 確定結果
            success = "失敗"
            stage = stage_used or "None"
            filename = "N/A"
            if company_log.get("status") == "skip":
                success = "失敗"
                stage = "Skip"
            elif any(key.endswith(".pdf") and isinstance(value, dict) and value.get("status") == "success" for key, value in company_log.items()):
                success = "成功"
                for key, value in company_log.items():
                    if key.endswith(".pdf") and isinstance(value, dict) and value.get("status") == "success":
                        filename = key
                        break
            results.append((company, success, stage, filename))

        await browser.close()

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(download_log, f, ensure_ascii=False, indent=2)

    # 輸出結果
    for company, success, stage, filename in results:
        print(f"{company} | {success} | {stage} | {filename}")

    # 統計
    total = len(results)
    success_count = sum(1 for _, s, _, _ in results if s == "成功")
    fail_count = total - success_count
    stage_counts = {}
    for _, _, stage, _ in results:
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    print(f"\n成功: {success_count}/{total}")
    print(f"失敗: {fail_count}/{total}")
    for stage in ["Stage0", "Stage1", "Stage2", "Stage3", "Stage4", "Skip", "None"]:
        count = stage_counts.get(stage, 0)
        print(f"{stage}: {count}家")

    print("下載完成，詳見 etl/download_log.json")


if __name__ == "__main__":
    asyncio.run(download_pdfs())