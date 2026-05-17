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
            
            # Fill in form fields
            await page.locator('input[placeholder="市場別*"]').fill('上市')
            await page.locator('input[placeholder="報告年度*"]').fill('2024')
            await page.locator('input[placeholder="公司代號"]').fill(code)
            
            # Wait for query button to be enabled
            query_btn = page.locator('button:has-text("查詢")')
            await query_btn.wait_for(timeout=5000)
            await query_btn.click()
            
            # Wait for results
            result_text = f'{code}-{company}'
            await page.locator(f'text={result_text}').wait_for(timeout=10000)
            
            # Expand the result
            await page.click(f'text={result_text}')
            await page.wait_for_timeout(1500)
            
            # Wait for download link and click
            # Find the first "下載 PDF" link under "中文版報告書："
            chinese_section = page.locator('text=中文版報告書：')
            download_link = chinese_section.locator('xpath=following-sibling::table//button:has-text("下載")')
            
            # Set up download listener and click
            async with page.expect_download() as download_info:
                await download_link.click()
            
            download = await download_info.value
            
            # Save with company name
            filename = f'{company}_{code}_2024_zh.pdf'
            filepath = os.path.join(r'C:\Users\Sam Joseph\esg-agent\report\2024', filename)
            await download.save_as(filepath)
            
            await browser.close()
            return True
    except Exception as e:
        print(f"Failed to download {company}: {str(e)}")
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
        await asyncio.sleep(1)  # 延遲避免過快請求
    
    print(f"\n成功: {success}/{len(STOCK_CODES)}")
    print(f"失敗: {fail}/{len(STOCK_CODES)}")

asyncio.run(main())