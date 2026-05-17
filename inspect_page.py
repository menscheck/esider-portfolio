import asyncio
from playwright.async_api import async_playwright

async def inspect_esg_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW", timeout=15000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)
        
        # 檢查下拉選單
        selects = await page.query_selector_all('select')
        print(f"找到 {len(selects)} 個下拉選單\n")
        
        for i, sel in enumerate(selects):
            placeholder = await sel.get_attribute('placeholder') or ""
            print(f"下拉選單 {i+1}: {placeholder}")
            
            options = await sel.query_selector_all('option')
            print(f"  選項數: {len(options)}")
            for opt in options[:5]:
                text = await opt.inner_text()
                print(f"    - {text}")
            print()
        
        # 保持瀏覽器開啟30秒讓你手動操作看
        print("瀏覽器將保持開啟30秒，請手動操作看正確步驟")
        await page.wait_for_timeout(30000)
        await browser.close()

asyncio.run(inspect_esg_page())
