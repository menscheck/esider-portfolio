import asyncio
from playwright.async_api import async_playwright

async def inspect_selects():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)

        lines = []
        dropdowns = await page.query_selector_all('._dropdown-content-box_1tpm0_9')
        lines.append(f"Found {len(dropdowns)} custom dropdowns\n")

        for i, dd in enumerate(dropdowns):
            inp = await dd.query_selector('input')
            placeholder = await inp.get_attribute('placeholder') if inp else f"dropdown_{i}"
            lines.append(f"=== Dropdown: {placeholder} ===")

            # Click to open
            await dd.click()
            await page.wait_for_timeout(1500)

            # Capture HTML after opening
            full_html = await page.content()

            # Look for list items / option items that appeared
            option_selectors = [
                '[class*="option"]', '[class*="item"]', '[class*="list"] li',
                'li', '[role="option"]', '[role="listitem"]'
            ]
            found_opts = False
            for sel in option_selectors:
                opts = await page.query_selector_all(sel)
                visible_opts = []
                for opt in opts:
                    is_visible = await opt.is_visible()
                    if is_visible:
                        txt = await opt.inner_text()
                        if txt.strip():
                            visible_opts.append(txt.strip())
                if visible_opts:
                    lines.append(f"  (selector: {sel!r})")
                    for t in visible_opts[:30]:
                        lines.append(f"  - {t!r}")
                    found_opts = True
                    break

            if not found_opts:
                lines.append("  (no visible options found after clicking)")

            # Take screenshot
            await page.screenshot(path=f"dropdown_{i}.png")
            lines.append(f"  screenshot: dropdown_{i}.png\n")

            # Click elsewhere to close
            await page.click('body', position={"x": 10, "y": 10})
            await page.wait_for_timeout(500)

        await browser.close()

        output = "\n".join(lines)
        with open("inspect_output3.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to inspect_output3.txt")

asyncio.run(inspect_selects())
