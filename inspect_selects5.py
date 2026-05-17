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

        async def close_any_open_dropdown():
            # Click on a safe area (the page title / header)
            try:
                await page.click('h1, .title, header', timeout=500)
            except Exception:
                pass
            await page.wait_for_timeout(400)
            # Make sure no option-item is visible
            for _ in range(3):
                opts = await page.query_selector_all('.option-item')
                visible = [o for o in opts if await o.is_visible()]
                if not visible:
                    break
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(300)

        async def open_and_read(placeholder, screenshot_name):
            await close_any_open_dropdown()
            dd_selector = f'._dropdown-content-box_1tpm0_9:has(input[placeholder="{placeholder}"])'
            dd = await page.wait_for_selector(dd_selector, timeout=5000)
            await dd.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"{screenshot_name}.png")

            opts = await page.query_selector_all('.option-item')
            result = []
            for opt in opts:
                if await opt.is_visible():
                    txt = (await opt.inner_text()).strip()
                    if txt:
                        result.append(txt)
            return result

        # --- 市場別 ---
        lines.append("=== 市場別 ===")
        opts = await open_and_read("市場別*", "sc_market")
        for t in opts:
            lines.append(f"  {t!r}")

        # Select 上市
        for opt in await page.query_selector_all('.option-item'):
            if await opt.is_visible() and (await opt.inner_text()).strip() == '上市':
                await opt.click()
                lines.append("\n[Selected 市場別=上市]")
                break
        await page.wait_for_timeout(1000)

        # --- 報告年度 ---
        lines.append("\n=== 報告年度 ===")
        opts2 = await open_and_read("報告年度*", "sc_year")
        for t in opts2:
            lines.append(f"  {t!r}")
        await close_any_open_dropdown()

        # --- 產業別 ---
        lines.append("\n=== 產業別 (after 上市) ===")
        opts3 = await open_and_read("產業別", "sc_industry")
        for t in opts3:
            lines.append(f"  {t!r}")
        if not opts3:
            lines.append("  (no options found — may need API call or dynamic loading)")
            # Try clicking the arrow icon specifically
            dd = await page.query_selector('._dropdown-content-box_1tpm0_9:has(input[placeholder="產業別"])')
            if dd:
                icon = await dd.query_selector('.dropdown-icon')
                if icon:
                    await icon.click()
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path="sc_industry2.png")
                    all_opts = await page.query_selector_all('.option-item')
                    for opt in all_opts:
                        if await opt.is_visible():
                            txt = (await opt.inner_text()).strip()
                            if txt:
                                lines.append(f"  [icon click] {txt!r}")

        await browser.close()

        output = "\n".join(lines)
        with open("inspect_output5.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to inspect_output5.txt")

asyncio.run(inspect_selects())
