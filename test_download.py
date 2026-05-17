import asyncio
from playwright.async_api import async_playwright

async def download_esg_report():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)
            print("Page loaded")
            
            await page.wait_for_selector('select')
            print("Select found")
            
            # Select market: 上市
            await page.locator('select').nth(0).select_option('上市')
            print("Market selected")
            
            # Fill year: 2024
            await page.fill('input[placeholder="報告年度*"]', '2024')
            print("Year filled")
            
            # Fill company code
            await page.fill('input[placeholder="公司代號"]', '2330')
            print("Code filled")
            
            # Click query
            await page.click('button:has-text("查詢")')
            print("Query clicked")
            
            await page.wait_for_selector('text=2330-台積電')
            print("Result appeared")
            
            # Expand result
            await page.click('text=2330-台積電')
            print("Expanded")
            await page.wait_for_timeout(1000)
            
            count = await page.locator('text=下載 PDF').count()
            print(f"Download links count: {count}")
            
            if count > 0:
                # Click download Chinese PDF
                download_promise = page.wait_for_event('download', timeout=10000)
                await page.locator('text=下載 PDF').nth(0).click()
                print("Clicked download")
                download = await download_promise
                await download.save_as('C:\\Users\\Sam Joseph\\esg-agent\\report\\2024\\test_tsmc.pdf')
                print("Downloaded")
            
            await browser.close()
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

asyncio.run(download_esg_report())