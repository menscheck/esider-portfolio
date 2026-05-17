import asyncio
from playwright.async_api import async_playwright

STOCK_CODES = {
    "台積電": "2330", "日月光投控": "3711", "元太科技": "8069",
    "鴻海精密": "2317", "矽品精密工業": "2325", "欣興電子": "3037",
    "玉山金控": "2884", "中國信託銀行": "2891", "國泰金控": "2882",
    "台北富邦銀行": "2881", "合作金庫銀行": "5880", "第一銀行": "2892",
    "彰化銀行": "2801", "台新金控": "2887", "亞洲水泥": "1102",
    "遠東新世紀": "1402", "榮成紙業": "1909", "宏遠興業": "1460",
    "中鋼公司": "2002", "統一超商": "2912", "全家便利商店": "5903",
    "台電公司": "9935", "台灣中油": "9907", "永豐銀行": "2890",
    "崇越科技": "5434", "長榮航空": "2618", "佳世達集團": "2352",
    "富邦產險": "2881", "新光人壽": "2888", "南山產物": "2867"
}

async def download_esg_report(company, code):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
            
            # Select market: 上市
            await page.locator('select').nth(0).select_option('上市')
            
            # Fill year: 2024
            await page.fill('input[placeholder="報告年度*"]', '2024')
            
            # Fill company code
            await page.fill('input[placeholder="公司代號"]', code)
            
            # Click query
            await page.click('button:has-text("查詢")')
            await page.wait_for_selector(f'text={code}-{company}')
            
            # Expand result
            await page.click(f'text={code}-{company}')
            await page.wait_for_timeout(1000)
            
            # Click download Chinese PDF
            download_promise = page.wait_for_event('download')
            await page.locator('text=下載 PDF').nth(0).click()  # first one is chinese
            download = await download_promise
            await download.save_as(f'C:\\Users\\Sam Joseph\\esg-agent\\report\\2024\\{company}_2024_zh.pdf')
            
            await browser.close()
        return True
    except Exception as e:
        print(f"Failed to download {company}: {e}")
        return False

async def main():
    success = 0
    fail = 0
    for company, code in STOCK_CODES.items():
        print(f"處理 {company} ({code})...")
        if await download_esg_report(company, code):
            success += 1
        else:
            fail += 1
    print(f"成功: {success}/{len(STOCK_CODES)}")
    print(f"失敗: {fail}/{len(STOCK_CODES)}")

asyncio.run(main())