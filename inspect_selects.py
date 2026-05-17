import asyncio
from playwright.async_api import async_playwright
import re
import sys

async def inspect_selects():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)

        content = await page.content()

        options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]+)</option>', content)

        lines = ["所有下拉選單選項："]
        for value, text in options[:80]:
            lines.append(f'  value="{value}" -> {text.strip()}')

        # Also use Playwright to get selects directly
        lines.append("\n=== 用 Playwright 取得 select 元素 ===")
        selects = await page.query_selector_all('select')
        lines.append(f"找到 {len(selects)} 個 <select> 元素")
        for i, sel in enumerate(selects):
            name = await sel.get_attribute('name') or ""
            id_ = await sel.get_attribute('id') or ""
            lines.append(f"\nSelect {i+1}: name={name!r} id={id_!r}")
            opts = await sel.query_selector_all('option')
            for opt in opts:
                val = await opt.get_attribute('value') or ""
                txt = await opt.inner_text()
                lines.append(f"  value={val!r} -> {txt.strip()}")

        await browser.close()

        output = "\n".join(lines)
        with open("inspect_output.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to inspect_output.txt")

asyncio.run(inspect_selects())
