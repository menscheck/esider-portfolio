# -*- coding: utf-8 -*-
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

        # Get all dropdowns in order (by JS, avoiding CSS selector encoding issues)
        dd_count = await page.evaluate("""
            () => document.querySelectorAll('._dropdown-content-box_1tpm0_9').length
        """)
        lines.append(f"Found {dd_count} dropdowns")

        for i in range(dd_count):
            placeholder = await page.evaluate(f"""
                () => {{
                    const boxes = document.querySelectorAll('._dropdown-content-box_1tpm0_9');
                    const inp = boxes[{i}].querySelector('input');
                    return inp ? inp.placeholder : '';
                }}
            """)
            lines.append(f"\n=== Dropdown {i}: {placeholder} ===")

            # Click via JS
            await page.evaluate(f"""
                () => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[{i}].click()
            """)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"sc_dd_{i}.png")

            # Read visible option-item elements
            options = await page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.option-item');
                    const result = [];
                    for (const item of items) {
                        const style = window.getComputedStyle(item);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            const val = item.getAttribute('data-value') || item.getAttribute('value') || '';
                            result.push({ val, text: item.textContent.trim() });
                        }
                    }
                    return result;
                }
            """)

            if options:
                for opt in options:
                    lines.append(f"  val={opt['val']!r}  text={opt['text']!r}")
            else:
                lines.append("  (no .option-item elements visible)")
                # Dump all visible text in .mt-3 containers or lists
                misc = await page.evaluate("""
                    () => {
                        const result = [];
                        document.querySelectorAll('[class*="options"], [class*="list"], [class*="dropdown-list"]').forEach(el => {
                            if (el.offsetParent !== null) {
                                result.push(el.className + ': ' + el.textContent.trim().slice(0, 200));
                            }
                        });
                        return result;
                    }
                """)
                for m in misc:
                    lines.append(f"  [misc] {m!r}")

            # Close dropdown by pressing Escape
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)

            # If this is 市場別 (index 0), also select first non-empty option
            if i == 0 and options:
                first_opt_text = options[0]['text'] if options else ''
                lines.append(f"\n  [Will select first option: {first_opt_text!r}]")
                # Click it via JS
                await page.evaluate(f"""
                    () => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[{i}].click()
                """)
                await page.wait_for_timeout(800)
                # Click first visible option-item
                await page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('.option-item');
                        for (const item of items) {
                            if (item.offsetParent !== null && item.textContent.trim()) {
                                item.click();
                                return;
                            }
                        }
                    }
                """)
                await page.wait_for_timeout(1500)

        await browser.close()

        output = "\n".join(lines)
        with open("inspect_output6.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to inspect_output6.txt")

asyncio.run(inspect_selects())
