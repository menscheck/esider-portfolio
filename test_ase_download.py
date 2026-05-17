# -*- coding: utf-8 -*-
"""
針對日月光投控(3711)的 TWSE ESGGenPlus 查詢 + PDF 下載測試腳本
headless=False，每個步驟均印出結果
"""
import asyncio
import os
import requests
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
DOWNLOAD_DIR = "data/reports/日月光投控"
TARGET_COMPANY_TEXT = "3711 日月光投控"
TARGET_YEAR = "2024"
TARGET_MARKET = "上市"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SEP = "─" * 60


def step(n, title):
    print(f"\n{SEP}")
    print(f"【步驟 {n}】{title}")
    print(SEP)


async def select_dropdown(page, index, target_text, label):
    """點開第 index 個 dropdown 並選取 target_text 的選項。"""
    try:
        await page.evaluate(f"""
            () => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[{index}].click()
        """)
        await page.wait_for_timeout(800)

        clicked = await page.evaluate(f"""
            (target) => {{
                const items = document.querySelectorAll('.option-item');
                for (const item of items) {{
                    if (item.offsetParent !== null && item.textContent.trim() === target) {{
                        item.click();
                        return true;
                    }}
                }}
                return false;
            }}
        """, target_text)

        await page.wait_for_timeout(600)
        if clicked:
            print(f"  ✓ {label} 選取成功：{target_text!r}")
        else:
            print(f"  ✗ {label} 找不到選項：{target_text!r}")
            # 印出可見選項
            options = await page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.option-item');
                    return [...items]
                        .filter(i => i.offsetParent !== null)
                        .map(i => i.textContent.trim())
                        .slice(0, 20);
                }
            """)
            print(f"  可見選項(前20)：{options}")
        return clicked
    except Exception as e:
        print(f"  ✗ {label} 操作異常：{e}")
        return False


async def click_query_button(page):
    """點擊查詢按鈕。"""
    try:
        # 嘗試多種 selector
        selectors = [
            'button:has-text("查詢")',
            'button.query-btn',
            'button[class*="query"]',
            'button[class*="search"]',
            'input[type="submit"]',
            'button:last-of-type',
        ]
        for sel in selectors:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    text = await btn.inner_text()
                    print(f"  找到查詢按鈕 [{sel}]，文字：{text!r}")
                    await btn.click()
                    await page.wait_for_timeout(2500)
                    return True
            except Exception:
                continue

        # fallback: 用 JS 找文字含「查詢」的按鈕
        clicked = await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.trim().includes('查詢')) {
                        b.click();
                        return b.textContent.trim();
                    }
                }
                return null;
            }
        """)
        if clicked:
            await page.wait_for_timeout(2500)
            print(f"  ✓ JS fallback 點擊查詢按鈕：{clicked!r}")
            return True

        print("  ✗ 找不到查詢按鈕")
        return False
    except Exception as e:
        print(f"  ✗ 查詢按鈕異常：{e}")
        return False


async def expand_result(page):
    """點擊查詢結果的該列以展開詳細資訊（PDF 連結）。"""
    await page.wait_for_timeout(1500)

    # 策略 1：嘗試點擊該列的圓形展開按鈕（可能在該列左側）
    print("  【嘗試策略 1】點擊該列的展開按鈕...")
    try:
        # 找包含 3711 的行，然後點擊其內部的展開按鈕
        rows = await page.query_selector_all('[class*="table-row"], [class*="row"], tr')
        for row in rows:
            txt = await row.inner_text()
            if '3711' in txt and '日月光' in txt:
                print(f"    找到該公司的列")
                # 在該列中找按鈕
                btn = await row.query_selector('button')
                if btn:
                    print(f"    該列內有按鈕，點擊之")
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    return True
    except Exception as e:
        print(f"    策略 1 失敗：{e}")

    # 策略 2：向下滾動，看是否有更多內容
    print("  【嘗試策略 2】向下滾動查找 PDF 連結...")
    try:
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(500)
            content = await page.content()
            if 'pdf' in content.lower() or '下載' in content or '報告書' in content:
                print(f"    滾動後偵測到下載相關內容")
                return True
    except Exception as e:
        print(f"    策略 2 失敗：{e}")

    # 策略 3：列出頁面上所有互動元素
    print("  【嘗試策略 3】列出頁面互動元素...")
    buttons = await page.query_selector_all('button')
    print(f"    頁面按鈕數：{len(buttons)}")
    for i, btn in enumerate(buttons):
        cls = await btn.get_attribute('class')
        txt = (await btn.inner_text()).strip()[:40]
        print(f"    [{i}] class={cls!r}  text={txt!r}")

    divs = await page.query_selector_all('[class*="expand"], [class*="collapse"], [class*="toggle"]')
    if divs:
        print(f"    找到 {len(divs)} 個展開/縮合相關元素")
        return True

    print("  ✗ 未找到展開按鈕")
    return False


async def find_pdf_links(page):
    """從展開後的頁面找 PDF 下載連結（含多種形式）。"""
    import re
    pdfs = []

    # 方法 1：掃描 <a href> 標籤
    print("  掃描 <a> 標籤...")
    anchors = await page.query_selector_all('a[href]')
    for a in anchors:
        href = await a.get_attribute('href') or ''
        text = (await a.inner_text()).strip()
        if '.pdf' in href.lower() or 'pdf' in text.lower() or '下載' in text or '報告' in text:
            pdfs.append({'href': href, 'text': text, 'type': 'a_href'})

    # 方法 2：掃描含「下載」「報告」「PDF」的按鈕
    print("  掃描按鈕...")
    buttons = await page.query_selector_all('button')
    for btn in buttons:
        text = (await btn.inner_text()).strip()
        onclick = await btn.get_attribute('onclick') or ''
        if any(kw in text for kw in ['下載', '報告', 'PDF', 'download']) or 'pdf' in onclick.lower():
            pdfs.append({'href': f'button:{text}', 'text': text, 'type': 'button'})

    # 方法 3：掃描 <link> 或其他資源
    print("  掃描原始碼中的 PDF URL...")
    content = await page.content()
    for m in re.findall(r'https?://[^\s"\'<>]+\.pdf', content, re.IGNORECASE):
        if not any(p['href'] == m for p in pdfs):
            pdfs.append({'href': m, 'text': 'source_scan', 'type': 'source'})

    # 方法 4：掃描含下載相關的 div 或其他元素
    print("  掃描下載相關區塊...")
    divs = await page.query_selector_all('[class*="download"], [class*="report"], [class*="file"]')
    for div in divs[:10]:  # 只看前10個
        text = (await div.inner_text()).strip()[:100]
        if text:
            pdfs.append({'href': f'div:{text}', 'text': text, 'type': 'div'})

    # 去重
    seen = set()
    unique = []
    for p in pdfs:
        key = (p['href'], p['text'])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique


async def download_pdf(url, dest_dir, filename):
    os.makedirs(dest_dir, exist_ok=True)
    filepath = os.path.join(dest_dir, filename)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        return filepath
    except Exception as e:
        print(f"  下載失敗：{e}")
        return None


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # ── 步驟 1：開啟查詢頁面 ──────────────────────────
        step(1, "開啟 TWSE ESGGenPlus 查詢頁面")
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        print(f"  ✓ 頁面載入完成：{page.url}")

        # ── 步驟 2：選條件 ────────────────────────────────
        step(2, "選取查詢條件")

        ok_market = await select_dropdown(page, 0, TARGET_MARKET, "市場別")
        await page.wait_for_timeout(500)

        ok_year = await select_dropdown(page, 1, TARGET_YEAR, "報告年度")
        await page.wait_for_timeout(500)

        # 公司代號 dropdown 是第 3 個 (index 3)
        ok_company = await select_dropdown(page, 3, TARGET_COMPANY_TEXT, "公司代號")
        await page.wait_for_timeout(500)

        all_ok = ok_market and ok_year and ok_company
        print(f"\n  條件選取結果：市場別={ok_market}, 報告年度={ok_year}, 公司代號={ok_company}")
        print(f"  {'✓ 全部成功' if all_ok else '✗ 部分失敗，繼續執行'}")

        # ── 步驟 3：點擊查詢 ──────────────────────────────
        step(3, "點擊查詢按鈕")
        query_ok = await click_query_button(page)
        print(f"  {'✓ 查詢按鈕點擊成功' if query_ok else '✗ 查詢按鈕點擊失敗'}")
        await page.screenshot(path="sc_query_result.png")
        print("  截圖已儲存：sc_query_result.png")

        # ── 步驟 4：展開結果 ──────────────────────────────
        step(4, "點擊展開按鈕（圓形下箭頭）")
        expand_ok = await expand_result(page)
        await page.screenshot(path="sc_expanded.png")
        print(f"  截圖已儲存：sc_expanded.png")
        print(f"  {'✓ 展開成功' if expand_ok else '✗ 展開失敗'}")

        # ── 步驟 5：找 PDF 連結 ───────────────────────────
        step(5, "掃描 PDF 下載連結")
        pdfs = await find_pdf_links(page)
        if pdfs:
            print(f"  找到 {len(pdfs)} 個 PDF 候選：")
            for i, p_info in enumerate(pdfs):
                print(f"  [{i}] {p_info['text']!r}  →  {p_info['href']}")
        else:
            print("  ✗ 未找到任何 PDF 連結")

        # ── 步驟 6：下載最佳 PDF ──────────────────────────
        step(6, "下載 PDF 並確認存檔路徑")
        if pdfs:
            print(f"  找到 {len(pdfs)} 個下載候選")
            # 優先選含「中文版」或完整 URL 的
            pdf_urls = [x for x in pdfs if x.get('type') in ['a_href', 'source']]
            if pdf_urls:
                best = next((x for x in pdf_urls if '中文' in x.get('text', '')), pdf_urls[0])
                print(f"  選定候選：{best['text']!r}  →  {best['href']}")
                if best['href'].startswith('http'):
                    saved = await download_pdf(best['href'], DOWNLOAD_DIR, "日月光投控_ESG_2024.pdf")
                    if saved:
                        abs_path = os.path.abspath(saved)
                        size_kb = os.path.getsize(saved) // 1024
                        print(f"  ✓ 下載成功")
                        print(f"  存檔路徑：{abs_path}")
                        print(f"  檔案大小：{size_kb} KB")
                    else:
                        print("  ✗ 下載失敗")
                else:
                    print(f"  ⓘ 非直接 URL，跳過下載")
            else:
                print("  ⓘ 無直接 PDF URL，列出其他候選：")
                for p in pdfs[:5]:
                    print(f"    - {p['type']:8s} {p['text'][:60]!r}  →  {p['href'][:80]}")
        else:
            print("  ✗ 無下載候選找到")

        print(f"\n{SEP}")
        print("全部步驟完成，按 Enter 關閉瀏覽器...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
