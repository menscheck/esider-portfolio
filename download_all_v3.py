import asyncio
from playwright.async_api import async_playwright
import os

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
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW", 
                          wait_until='networkidle')
            
            await page.wait_for_timeout(2000)  # Wait for JS to fully load
            
            # Click on market dropdown and select "上市"
            market_input = page.locator('input[placeholder="市場別*"]')
            await market_input.click()
            await page.wait_for_timeout(500)
            await page.keyboard.type('上市')
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(500)
            
            # Click on year field and enter 2024
            year_input = page.locator('input[placeholder="報告年度*"]')
            await year_input.click()
            await page.wait_for_timeout(300)
            await page.keyboard.type('2024')
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(500)
            
            # Enter company code
            code_input = page.locator('input[placeholder="公司代號"]')
            await code_input.click()
            await page.wait_for_timeout(300)
            await page.keyboard.type(code)
            await page.wait_for_timeout(500)
            
            # Click query button (should be enabled now)
            query_btn = page.locator('button:has-text("查詢")')
            await query_btn.wait_for(state='visible', timeout=5000)
            await page.wait_for_timeout(1000)  # Extra wait to ensure button is enabled
            await query_btn.click()
            
            # Wait for results
            result_text = f'{code}-{company}'
            await page.wait_for_selector(f'text={result_text}', timeout=10000)
            
            # Expand the result
            await page.click(f'text={result_text}')
            await page.wait_for_timeout(1500)
            
            # Find and click the first "下載 PDF" (Chinese version)
            download_links = page.locator('text=下載 PDF')
            count = await download_links.count()
            
            if count > 0:
                async with page.expect_download() as download_info:
                    await download_links.first.click()
                
                download = await download_info.value
                
                # Save with company name
                filename = f'{company}_{code}_2024_zh.pdf'
                filepath = os.path.join(r'C:\Users\Sam Joseph\esg-agent\report\2024', filename)
                await download.save_as(filepath)
                
                await browser.close()
                return True
            else:
                await browser.close()
                return False
                
    except Exception as e:
        print(f"Error for {company}: {str(e)}")
        return False

async def main():
    success = 0
    fail = 0
    
    for company, code in STOCK_CODES.items():
        print(f"處理 {company} ({code})...")
        if await download_esg_report(company, code):
            success += 1
            print(f"  ✓ 成功")
        else:
            fail += 1
            print(f"  ✗ 失敗")
    
    print(f"\n成功: {success}/{len(STOCK_CODES)}")
    print(f"失敗: {fail}/{len(STOCK_CODES)}")

asyncio.run(main())