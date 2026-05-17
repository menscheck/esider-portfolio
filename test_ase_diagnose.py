# -*- coding: utf-8 -*-
"""
診斷版本：輸出頁面完整結構和所有互動元素
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 打開頁面並執行查詢
        print("【開啟頁面】")
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)

        print("【選取條件】")
        # 市場別=上市
        await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[0].click()")
        await page.wait_for_timeout(800)
        await page.evaluate("""
            (target) => {
                const items = document.querySelectorAll('.option-item');
                for (const item of items) {
                    if (item.offsetParent !== null && item.textContent.trim() === target) {
                        item.click();
                        return;
                    }
                }
            }
        """, "上市")
        await page.wait_for_timeout(600)

        # 報告年度=2024
        await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[1].click()")
        await page.wait_for_timeout(800)
        await page.evaluate("""
            (target) => {
                const items = document.querySelectorAll('.option-item');
                for (const item of items) {
                    if (item.offsetParent !== null && item.textContent.trim() === target) {
                        item.click();
                        return;
                    }
                }
            }
        """, "2024")
        await page.wait_for_timeout(600)

        # 公司代號=3711
        await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[3].click()")
        await page.wait_for_timeout(800)
        await page.evaluate("""
            (target) => {
                const items = document.querySelectorAll('.option-item');
                for (const item of items) {
                    if (item.offsetParent !== null && item.textContent.trim() === target) {
                        item.click();
                        return;
                    }
                }
            }
        """, "3711 日月光投控")
        await page.wait_for_timeout(600)

        # 點擊查詢
        print("【點擊查詢】")
        btn = await page.query_selector('button:has-text("查詢")')
        if btn:
            await btn.click()
            await page.wait_for_timeout(3000)

        # ── 診斷：列出頁面結構 ──────────────────────────
        print("\n【診斷：頁面元素分析】\n")

        # 列出所有表格行
        print("=== 表格行（可能是結果） ===")
        rows = await page.query_selector_all('tr, [class*="row"], [class*="item"]')
        print(f"找到 {len(rows)} 個行級元素")
        for i, row in enumerate(rows[:5]):
            txt = await row.inner_text()
            cls = await row.get_attribute('class') or ''
            print(f"  [{i}] class={cls[:50]!r}  text={txt[:80]!r}")

        # 列出所有可點擊元素
        print("\n=== 可點擊元素 ===")
        clickables = await page.query_selector_all('a, button, [role="button"], [onclick]')
        print(f"找到 {len(clickables)} 個可點擊元素")
        for i, elem in enumerate(clickables[:20]):
            tag = await page.evaluate("(el) => el.tagName", elem)
            txt = (await elem.inner_text()).strip()[:40]
            href = await elem.get_attribute('href') or ''
            onclick = await elem.get_attribute('onclick') or ''
            print(f"  [{i}] <{tag}> text={txt!r} href={href[:40]!r} onclick={onclick[:40]!r}")

        # 列出所有含關鍵字的元素
        print("\n=== 含關鍵字的元素 ===")
        keywords = ['下載', '報告', 'PDF', 'download', 'report']
        for kw in keywords:
            els = await page.query_selector_all(f'*')
            matched = []
            for el in els:
                txt = await el.inner_text()
                if kw.lower() in txt.lower():
                    matched.append(el)
            if matched:
                print(f"  含 '{kw}' 的元素數：{len(matched)}")
                for el in matched[:3]:
                    txt = (await el.inner_text()).strip()[:60]
                    tag = await page.evaluate("(el) => el.tagName", el)
                    print(f"    <{tag}> {txt!r}")

        # 輸出原始 HTML 到檔案（用於進一步分析）
        print("\n【輸出原始 HTML】")
        html = await page.content()
        with open("page_source_diagnostic.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("  已儲存至 page_source_diagnostic.html")

        # 嘗試點擊該列（可能會展開詳細資訊）
        print("\n【嘗試點擊結果列】")
        rows = await page.query_selector_all('tr, [class*="result"], [class*="row"]')
        for row in rows:
            txt = await row.inner_text()
            if '3711' in txt:
                print(f"  找到包含 3711 的列，點擊它...")
                await row.click()
                await page.wait_for_timeout(2000)
                break

        # 滾動看更多內容
        print("\n【向下滾動】")
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="sc_diagnostic.png")
        print("  截圖：sc_diagnostic.png")

        # 再次列出元素
        print("\n【滾動後的元素】")
        clickables = await page.query_selector_all('a, button, [role="button"]')
        print(f"現在有 {len(clickables)} 個可點擊元素")
        for i, elem in enumerate(clickables[-10:]):
            tag = await page.evaluate("(el) => el.tagName", elem)
            txt = (await elem.inner_text()).strip()[:40]
            href = await elem.get_attribute('href') or ''
            print(f"  [{i}] <{tag}> text={txt!r} href={href[:60]!r}")

        print("\n按 Enter 關閉...")
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
