# -*- coding: utf-8 -*-
"""
正確版：直接在 table[aria-label="查詢結果"] 中找下載連結
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
DOWNLOAD_DIR = "data/reports/日月光投控"

async def select_and_query(page):
    """選取條件並查詢。"""
    print("【選取查詢條件】")

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
    print("  ✓ 市場別 = 上市")

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
    print("  ✓ 報告年度 = 2024")

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
    print("  ✓ 公司代號 = 3711 日月光投控")

    # 點擊查詢
    print("【點擊查詢】")
    btn = await page.query_selector('button:has-text("查詢")')
    if btn:
        await btn.click()
        await page.wait_for_timeout(3000)
        print("  ✓ 查詢按鈕點擊成功")

    await page.screenshot(path="sc_correct_query.png")


async def download_pdf_from_table(page):
    """在 table[aria-label="查詢結果"] 中找下載連結並下載。"""
    print("\n【在查詢結果表格中找下載連結】")

    # 雙擊該行展開詳情
    print("  1. 雙擊該公司列展開詳情...")
    rows = await page.query_selector_all('tr, [class*="row"]')
    for row in rows:
        txt = await row.inner_text()
        if '3711' in txt:
            await row.dblclick()
            await page.wait_for_timeout(1500)
            print("    ✓ 雙擊展開成功")
            break

    # 滾動
    print("  2. 向下滾動...")
    await page.evaluate("window.scrollBy(0, 500)")
    await page.wait_for_timeout(1000)
    print("    ✓ 滾動完成")

    await page.screenshot(path="sc_correct_before_download.png")

    # 找所有查詢結果表格
    print("  3. 找查詢結果表格...")
    tables = await page.query_selector_all('table[aria-label="查詢結果"]')
    print(f"    找到 {len(tables)} 個查詢結果表格")

    if len(tables) == 0:
        print("    ✗ 沒有找到表格，嘗試其他 selector...")
        # 診斷：列出所有 table
        all_tables = await page.query_selector_all('table')
        print(f"    頁面上共有 {len(all_tables)} 個 table")
        for i, t in enumerate(all_tables[:3]):
            label = await t.get_attribute('aria-label') or '(無標籤)'
            print(f"      [table {i}] {label}")
        return None

    # 第一個 table = 中文版
    print("  4. 在第一個表格（中文版）中找下載連結...")
    zh_table = tables[0]

    # 找「下載 PDF」連結
    pdf_link = await zh_table.query_selector('a:has-text("下載 PDF")')

    if pdf_link:
        print("    ✓ 找到「下載 PDF」連結")
        href = await pdf_link.get_attribute('href')
        print(f"    連結: {href}")

        # 使用 expect_download 方式下載
        print("  5. 點擊下載...")
        try:
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            filepath = os.path.join(DOWNLOAD_DIR, "日月光投控_ESG_2024.pdf")

            async with page.expect_download() as dl_info:
                await pdf_link.click()

            download = await dl_info.value
            await download.save_as(filepath)

            abs_path = os.path.abspath(filepath)
            size_kb = os.path.getsize(filepath) // 1024
            print(f"    ✓ 下載成功")
            print(f"    存檔：{abs_path}")
            print(f"    大小：{size_kb} KB")
            return filepath
        except Exception as e:
            print(f"    ✗ 下載失敗：{e}")
            return None
    else:
        print("    ✗ 未找到「下載 PDF」連結")
        print("    表格內所有連結：")
        links = await zh_table.query_selector_all('a')
        for i, link in enumerate(links):
            text = (await link.inner_text()).strip()[:40]
            href = await link.get_attribute('href') or ''
            print(f"      [{i}] {text!r} → {href[:60]}")

        # 列出所有有 href 的元素
        print("    表格內所有有 href 的元素：")
        elements = await zh_table.query_selector_all('[href]')
        for i, elem in enumerate(elements[:10]):
            text = (await elem.inner_text()).strip()[:40]
            href = await elem.get_attribute('href') or ''
            print(f"      [{i}] {text!r} → {href[:60]}")

        return None


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 60)
        print("【步驟 1】開啟頁面")
        print("=" * 60)
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        print("✓ 頁面載入完成")

        print("\n" + "=" * 60)
        print("【步驟 2-3】選條件 + 查詢")
        print("=" * 60)
        await select_and_query(page)

        print("\n" + "=" * 60)
        print("【步驟 4-5】展開 + 下載")
        print("=" * 60)
        result = await download_pdf_from_table(page)

        print("\n" + "=" * 60)
        if result:
            print("✓ 所有步驟完成，PDF 下載成功！")
        else:
            print("✗ 下載失敗")
        print("=" * 60)
        print("\n按 Enter 關閉瀏覽器...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
