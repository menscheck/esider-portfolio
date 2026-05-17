# -*- coding: utf-8 -*-
"""
診斷版：列出表格內的所有元素，找「下載 PDF」的容器結構
"""
import asyncio
import os
import json
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"

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


async def diagnose_tables(page):
    """診斷表格內的元素結構。"""
    print("【診斷表格元素結構】\n")

    # 雙擊展開
    rows = await page.query_selector_all('tr, [class*="row"]')
    for row in rows:
        txt = await row.inner_text()
        if '3711' in txt:
            await row.dblclick()
            await page.wait_for_timeout(1500)
            break

    # 滾動
    await page.evaluate("window.scrollBy(0, 500)")
    await page.wait_for_timeout(1000)

    # 找所有表格
    tables = await page.query_selector_all('table[aria-label="查詢結果"]')
    print(f"找到 {len(tables)} 個表格\n")

    for table_idx, table in enumerate(tables):
        print(f"【表格 {table_idx + 1}】")

        # 列出表格內的所有元素（不只是 <a>）
        all_elements = await table.query_selector_all('*')
        print(f"  總元素數：{len(all_elements)}")

        # 找包含「下載」的元素
        for elem in all_elements:
            text = await elem.inner_text()
            if '下載' in text or 'PDF' in text or 'download' in text.lower():
                tag = await page.evaluate("(el) => el.tagName", elem)
                cls = await elem.get_attribute('class') or ''
                role = await elem.get_attribute('role') or ''
                onclick = await elem.get_attribute('onclick') or ''
                href = await elem.get_attribute('href') or ''
                data_attrs = await page.evaluate(
                    "(el) => Object.keys(el.dataset).map(k => `${k}=${el.dataset[k]}`)",
                    elem
                )

                print(f"\n  找到「{text[:40].strip()}」")
                print(f"    tag={tag}  class={cls[:60]}")
                print(f"    role={role}  onclick={onclick[:60]}")
                print(f"    href={href[:60]}")
                if data_attrs:
                    print(f"    data-attrs={data_attrs}")

                # 如果是按鈕，嘗試點擊
                if tag in ['BUTTON', 'A'] or onclick or role == 'button':
                    print(f"    → 可點擊元素！")

        # 輸出表格的完整 HTML（前 500 字）
        html = await table.get_attribute('outerHTML') or ''
        print(f"\n  HTML（前500字）：")
        print(f"    {html[:500]}")
        print()


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 60)
        print("【開啟頁面 + 查詢】")
        print("=" * 60 + "\n")
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        await select_and_query(page)

        await diagnose_tables(page)

        # 保存完整頁面 HTML
        html = await page.content()
        with open("page_full_diagnostic.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("【已保存完整 HTML 到 page_full_diagnostic.html】\n")

        await page.screenshot(path="sc_diagnostic_full.png")
        print("【已保存截圖 sc_diagnostic_full.png】\n")

        print("\n按 Enter 關閉...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
