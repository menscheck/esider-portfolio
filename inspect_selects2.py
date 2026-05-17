import asyncio
from playwright.async_api import async_playwright

async def inspect_selects():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(5000)

        lines = []

        # Get full HTML
        content = await page.content()
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(content)
        lines.append("HTML saved to page_source.html")

        # Check for various dropdown-like elements
        for selector in ['select', '[role="listbox"]', '[role="option"]', '[role="combobox"]',
                         '.el-select', '.el-option', 'v-select', '.multiselect',
                         '[class*="select"]', '[class*="dropdown"]', 'input[list]']:
            els = await page.query_selector_all(selector)
            if els:
                lines.append(f"\nFound {len(els)} elements matching: {selector!r}")
                for i, el in enumerate(els[:5]):
                    outer = await el.evaluate("el => el.outerHTML")
                    lines.append(f"  [{i}] {outer[:200]}")

        # Check all inputs
        inputs = await page.query_selector_all('input')
        lines.append(f"\nTotal <input> elements: {len(inputs)}")
        for inp in inputs:
            t = await inp.get_attribute('type') or 'text'
            name = await inp.get_attribute('name') or ''
            id_ = await inp.get_attribute('id') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            lines.append(f"  type={t!r} name={name!r} id={id_!r} placeholder={placeholder!r}")

        # Check all buttons
        buttons = await page.query_selector_all('button')
        lines.append(f"\nTotal <button> elements: {len(buttons)}")
        for btn in buttons[:10]:
            txt = await btn.inner_text()
            lines.append(f"  {txt.strip()!r}")

        await browser.close()

        output = "\n".join(lines)
        with open("inspect_output2.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to inspect_output2.txt")

asyncio.run(inspect_selects())
