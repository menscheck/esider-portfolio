import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
        
        # 等待更長時間讓 SPA render
        await page.wait_for_timeout(5000)
        
        # 截圖看現在狀態
        await page.screenshot(path="debug_twse_1.png")
        print("截圖1已存")
        
        # 印出頁面所有 input（不等待）
        inputs = await page.locator('input').all()
        print(f"input 數量: {len(inputs)}")
        for i, inp in enumerate(inputs):
            ph = await inp.get_attribute('placeholder')
            aria = await inp.get_attribute('aria-label')
            cls = await inp.get_attribute('class')
            print(f"  input[{i}] placeholder={ph!r} aria-label={aria!r}")
        
        # 印出所有有文字的 label
        labels = await page.locator('label').all()
        print(f"\nlabel 數量: {len(labels)}")
        for i, lb in enumerate(labels):
            txt = await lb.inner_text()
            print(f"  label[{i}]: {txt!r}")
        
        # 印出所有 button
        buttons = await page.locator('button').all()
        print(f"\nbutton 數量: {len(buttons)}")
        for i, btn in enumerate(buttons):
            txt = await btn.inner_text()
            print(f"  button[{i}]: {txt!r}")
        
        input("按 Enter 關閉...")
        await browser.close()

asyncio.run(main())