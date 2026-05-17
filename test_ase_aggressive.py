# -*- coding: utf-8 -*-
"""
更激進的展開策略：點擊該行的各個部分，尋找展開詳情的方式
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
DOWNLOAD_DIR = "data/reports/日月光投控"

async def select_and_query(page):
    """選取條件並查詢。"""
    # 市場別
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[0].click()")
    await page.wait_for_timeout(800)
    await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim() === target) {
                    item.click();
                }
            }
        }
    """, "上市")
    await page.wait_for_timeout(600)

    # 報告年度
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[1].click()")
    await page.wait_for_timeout(800)
    await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim() === target) {
                    item.click();
                }
            }
        }
    """, "2024")
    await page.wait_for_timeout(600)

    # 公司代號
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[3].click()")
    await page.wait_for_timeout(800)
    await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim() === target) {
                    item.click();
                }
            }
        }
    """, "3711 日月光投控")
    await page.wait_for_timeout(600)

    # 點擊查詢
    btn = await page.query_selector('button:has-text("查詢")')
    if btn:
        await btn.click()
        await page.wait_for_timeout(3000)

    print("✓ 條件選取和查詢完成")


async def find_expand_button(page):
    """尋找該行的展開按鈕。"""
    print("\n【尋找展開機制】")

    # 方法 1：該行前面可能有展開箭頭
    print("  方法 1：尋找該行前的展開箭頭...")
    result = await page.evaluate('''
        () => {
            const rows = document.querySelectorAll('tr, [class*="row"]');
            for (let row of rows) {
                if (row.textContent.includes('3711')) {
                    // 該行前面可能有展開箭頭
                    const prevEl = row.previousElementSibling;
                    if (prevEl) {
                        const buttons = prevEl.querySelectorAll('button');
                        if (buttons.length > 0) {
                            return {
                                type: 'prev_element',
                                element: 'button',
                                found: true
                            };
                        }
                    }

                    // 或者該行本身的第一個元素是按鈕
                    const firstCell = row.querySelector('td, [role="gridcell"]');
                    if (firstCell) {
                        const btn = firstCell.querySelector('button');
                        if (btn) {
                            btn.click();
                            return { type: 'first_cell_button', found: true };
                        }
                    }
                }
            }
            return { found: false };
        }
    ''')

    if result['found']:
        print(f"    ✓ 找到展開按鈕：{result['type']}")
        await page.wait_for_timeout(1500)
        return True

    # 方法 2：嘗試雙擊該行
    print("  方法 2：嘗試雙擊該行...")
    rows = await page.query_selector_all('tr, [class*="row"]')
    for row in rows:
        txt = await row.inner_text()
        if '3711' in txt:
            try:
                await row.dblclick()
                await page.wait_for_timeout(1500)
                print(f"    ✓ 雙擊該行")
                return True
            except Exception as e:
                print(f"    × 雙擊失敗：{e}")

    # 方法 3：嘗試按右鍵（可能有上下文菜單）
    print("  方法 3：嘗試按右鍵...")
    rows = await page.query_selector_all('tr, [class*="row"]')
    for row in rows:
        txt = await row.inner_text()
        if '3711' in txt:
            try:
                await row.click(button='right')
                await page.wait_for_timeout(1500)
                print(f"    ✓ 右鍵點擊該行")
                return True
            except Exception:
                pass

    # 方法 4：尋找任何按鈕並嘗試點擊
    print("  方法 4：在該行內尋找並點擊按鈕...")
    rows = await page.query_selector_all('tr, [class*="row"]')
    for row in rows:
        txt = await row.inner_text()
        if '3711' in txt:
            buttons = await row.query_selector_all('button')
            if buttons:
                for btn in buttons:
                    try:
                        await btn.click()
                        await page.wait_for_timeout(1500)
                        print(f"    ✓ 點擊行內按鈕")
                        return True
                    except Exception:
                        pass

    print("  × 未找到展開機制")
    return False


async def check_for_pdf_content(page):
    """檢查是否有中文版報告書內容。"""
    content = await page.content()
    if '中文版報告書' in content or '中文版' in content or '報告書' in content:
        print("✓ 頁面中偵測到報告書相關內容")
        return True
    else:
        print("× 頁面中未偵測到報告書內容")
        return False


async def dump_page_structure(page):
    """輸出頁面完整結構。"""
    print("\n【完整頁面結構（前2000字）】")
    html = await page.content()

    # 找「中文版」的位置
    if '中文版' in html:
        idx = html.find('中文版')
        print(f"\n  找到「中文版」於位置 {idx}，前後500字：")
        start = max(0, idx - 250)
        end = min(len(html), idx + 250)
        snippet = html[start:end]
        print(f"    {snippet}")
    else:
        print("  頁面中未包含「中文版」文本")
        # 輸出前 2000 字
        print(f"\n  HTML 前2000字：")
        print(f"    {html[:2000]}")


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 60)
        print("【步驟 1-3】頁面載入、選條件、查詢")
        print("=" * 60)
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)

        await select_and_query(page)
        await page.screenshot(path="sc_agg_query.png")
        print("  截圖：sc_agg_query.png")

        print("\n" + "=" * 60)
        print("【步驟 4】展開該行詳情")
        print("=" * 60)
        expand_ok = await find_expand_button(page)
        await page.screenshot(path="sc_agg_after_expand.png")
        print("  截圖：sc_agg_after_expand.png")

        print("\n" + "=" * 60)
        print("【步驟 5】檢查是否有報告書內容")
        print("=" * 60)
        has_content = await check_for_pdf_content(page)

        if not has_content:
            print("\n【診斷：輸出頁面結構】")
            await dump_page_structure(page)

        print("\n" + "=" * 60)
        print("全部步驟完成，按 Enter 關閉...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
