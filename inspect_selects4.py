import asyncio
import re
from playwright.async_api import async_playwright

async def inspect_selects():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)

        lines = []

        async def open_and_read_options(placeholder, screenshot_name):
            dd_selector = f'._dropdown-content-box_1tpm0_9:has(input[placeholder="{placeholder}"])'
            dd = await page.query_selector(dd_selector)
            if not dd:
                return [f"ERROR: could not find dropdown {placeholder!r}"]
            await dd.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"{screenshot_name}.png")

            result = []
            for sel in ['[class*="option-item"]', '[class*="options"] [class*="item"]',
                        '[class*="option"]:not([class*="content-box"])']:
                opts = await page.query_selector_all(sel)
                visible = []
                for opt in opts:
                    if await opt.is_visible():
                        txt = (await opt.inner_text()).strip()
                        if txt:
                            visible.append(txt)
                if visible:
                    result = visible
                    break

            # Also try HTML regex as fallback
            if not result:
                html = await page.content()
                result = re.findall(r'class="[^"]*option[^"]*"[^>]*>([^<\n]+)<', html)

            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            return result

        # Step 1: get 市場別 options (no prior selection needed)
        lines.append("=== 市場別 ===")
        opts = await open_and_read_options("市場別*", "sc_market")
        for t in opts:
            lines.append(f"  {t!r}")

        # Step 2: Select 上市 from 市場別
        dd = await page.query_selector('._dropdown-content-box_1tpm0_9:has(input[placeholder="市場別*"])')
        await dd.click()
        await page.wait_for_timeout(800)
        all_opts = await page.query_selector_all('[class*="option"]')
        for opt in all_opts:
            if await opt.is_visible():
                txt = (await opt.inner_text()).strip()
                if txt == '上市':
                    await opt.click()
                    lines.append("\n[Selected 市場別=上市]")
                    break
        await page.wait_for_timeout(2000)

        # Step 3: get 報告年度 options
        lines.append("\n=== 報告年度 ===")
        opts2 = await open_and_read_options("報告年度*", "sc_year")
        for t in opts2:
            lines.append(f"  {t!r}")

        # Step 4: get 產業別 options
        lines.append("\n=== 產業別 (after 上市 selected) ===")
        opts3 = await open_and_read_options("產業別", "sc_industry")
        for t in opts3:
            lines.append(f"  {t!r}")

        # If still empty, dump HTML snippet around the dropdown
        if not opts3:
            html = await page.content()
            idx = html.find('產業別')
            if idx >= 0:
                snippet = html[max(0, idx-200):idx+2000]
                with open("industry_html_snippet.txt", "w", encoding="utf-8") as f:
                    f.write(snippet)
                lines.append("  [Saved HTML snippet to industry_html_snippet.txt]")

        await browser.close()

        output = "\n".join(lines)
        with open("inspect_output4.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to inspect_output4.txt")

asyncio.run(inspect_selects())
