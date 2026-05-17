# -*- coding: utf-8 -*-
import asyncio
from playwright.async_api import async_playwright
import os

# Stock code → display name used in TWSE dropdown (abbreviated)
# Codes not in 上市 list are marked as 上櫃 or skipped
COMPANIES = {
    "2330": "台積電",
    "3711": "日月光投控",
    "8069": "元太科技",       # may be 上櫃
    "2317": "鴻海",
    "2325": "矽品",           # may be 上櫃 / delisted
    "3037": "欣興",
    "2884": "玉山金",
    "2891": "中信金",
    "2882": "國泰金",
    "2881": "富邦金",
    "5880": "合庫金",
    "2892": "第一金",
    "2801": "彰銀",
    "2887": "台新新光金",
    "1102": "亞泥",
    "1402": "遠東新",
    "1909": "榮成",
    "1460": "宏遠",
    "2002": "中鋼",
    "2912": "統一超",
    "5903": "全家",           # may be 上櫃
    "9907": "台灣中油",       # may be 公發 or not listed
    "2890": "永豐金",
    "5434": "崇越",
    "2618": "長榮航",
    "2352": "佳世達",
    "2888": "新光人壽",       # may be merged / delisted
}

# Friendly full names just for file naming
FULL_NAMES = {
    "2330": "台積電",
    "3711": "日月光投控",
    "8069": "元太科技",
    "2317": "鴻海精密",
    "2325": "矽品精密工業",
    "3037": "欣興電子",
    "2884": "玉山金控",
    "2891": "中國信託銀行",
    "2882": "國泰金控",
    "2881": "台北富邦銀行",
    "5880": "合作金庫銀行",
    "2892": "第一銀行",
    "2801": "彰化銀行",
    "2887": "台新金控",
    "1102": "亞洲水泥",
    "1402": "遠東新世紀",
    "1909": "榮成紙業",
    "1460": "宏遠興業",
    "2002": "中鋼公司",
    "2912": "統一超商",
    "5903": "全家便利商店",
    "9907": "台灣中油",
    "2890": "永豐銀行",
    "5434": "崇越科技",
    "2618": "長榮航空",
    "2352": "佳世達集團",
    "2888": "新光人壽",
}

MARKETS = ["上市", "上櫃", "公發", "興櫃"]
YEAR = "2024"
DOWNLOAD_DIR = r"C:\Users\Sam Joseph\esg-agent\report\2024"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def js_click_option(page, text):
    """Click a visible .option-item whose text equals the given string."""
    return await page.evaluate(f"""
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
    """, text)


async def js_click_option_startswith(page, prefix):
    """Click first visible .option-item whose text starts with the given prefix."""
    return await page.evaluate(f"""
        (prefix) => {{
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {{
                if (item.offsetParent !== null && item.textContent.trim().startsWith(prefix)) {{
                    item.click();
                    return item.textContent.trim();
                }}
            }}
            return null;
        }}
    """, prefix)


async def open_dropdown(page, index):
    """Open the Nth dropdown (0-based) via JS click."""
    await page.evaluate(f"""
        () => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[{index}].click()
    """)
    await page.wait_for_timeout(800)


async def close_dropdowns(page):
    """Press Escape and wait for dropdowns to close."""
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(400)


async def reset_page(page):
    """Navigate fresh to the ESG query page."""
    await page.goto(
        "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW",
        timeout=20000,
    )
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(1500)


async def try_download(page, context, stock_code, market, year):
    """
    Try to find + download report for stock_code under given market & year.
    Returns (clicked_option_text, success) or (None, False).
    """
    # --- Select market (dropdown 0) ---
    await open_dropdown(page, 0)
    ok = await js_click_option(page, market)
    if not ok:
        return None, False
    await page.wait_for_timeout(600)

    # --- Select year (dropdown 1) ---
    await open_dropdown(page, 1)
    ok = await js_click_option(page, year)
    if not ok:
        return None, False
    await page.wait_for_timeout(600)

    # --- Skip 產業別 (dropdown 2), go straight to 公司代號 (dropdown 3) ---
    await open_dropdown(page, 3)
    await page.wait_for_timeout(600)
    option_text = await js_click_option_startswith(page, stock_code + " ")
    await page.wait_for_timeout(400)

    if not option_text:
        return None, False

    # --- Click 查詢 ---
    await page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent.trim() === '查詢') { b.click(); return; }
            }
        }
    """)
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2500)

    # --- Find download button ---
    # Look for a link/button that has "下載" and "PDF" (zh-TW version)
    download_el = await page.query_selector('text=下載 PDF')
    if not download_el:
        download_el = await page.query_selector('[class*="download"]')
    if not download_el:
        return option_text, False

    # --- Download ---
    try:
        async with context.expect_page() as new_page_info:
            await download_el.click()
        new_page = await new_page_info.value
        await new_page.wait_for_load_state("load")
        url = new_page.url
        await new_page.close()
        # If it opened a PDF in a new tab, fetch it
        if url.lower().endswith(".pdf") or "pdf" in url.lower():
            import urllib.request
            save_path = os.path.join(
                DOWNLOAD_DIR, f"{FULL_NAMES.get(stock_code, stock_code)}_{stock_code}_{year}.pdf"
            )
            urllib.request.urlretrieve(url, save_path)
            return option_text, True
    except Exception:
        pass

    # Fallback: expect_download
    try:
        async with context.expect_page():
            pass
    except Exception:
        pass

    try:
        async with page.expect_download(timeout=20000) as dl_info:
            await download_el.click()
        dl = await dl_info.value
        save_path = os.path.join(
            DOWNLOAD_DIR, f"{FULL_NAMES.get(stock_code, stock_code)}_{stock_code}_{year}.pdf"
        )
        await dl.save_as(save_path)
        return option_text, True
    except Exception as e:
        return option_text, False


async def download_company(stock_code):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            # Try each market in order
            for market in MARKETS:
                await reset_page(page)
                try:
                    option_text, success = await try_download(
                        page, context, stock_code, market, YEAR
                    )
                except Exception as e:
                    print(f"  [{market}] error: {str(e)[:60]}", flush=True)
                    continue

                if option_text is None:
                    # Company not found in this market
                    continue

                full_name = FULL_NAMES.get(stock_code, stock_code)
                if success:
                    print(f"OK  {full_name} ({stock_code}) [{market}] → {option_text}", flush=True)
                    return True
                else:
                    print(f"FOUND but no PDF  {full_name} ({stock_code}) [{market}] → {option_text}", flush=True)
                    return False

            print(f"MISS {FULL_NAMES.get(stock_code, stock_code)} ({stock_code}) — not found in any market", flush=True)
            return False
        finally:
            await browser.close()


async def main():
    ok, fail = 0, 0
    for code in COMPANIES:
        result = await download_company(code)
        if result:
            ok += 1
        else:
            fail += 1

    print(f"\n=== Done: {ok} success / {fail} fail / {len(COMPANIES)} total ===", flush=True)


asyncio.run(main())
