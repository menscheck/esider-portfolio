import asyncio
from playwright.async_api import async_playwright
import os

BASE_DIR = r"C:\Users\Sam Joseph\esg-agent\data\reports"

COMPANIES = {
    "2330": ("台積電", "半導體業"),
    "3711": ("日月光投控", "半導體業"),
    "8069": ("元太科技", "光電業"),
    "2317": ("鴻海精密", "其他電子業"),
    "2325": ("矽品精密工業", "半導體業"),
    "3037": ("欣興電子", "電子零組件業"),
    "2884": ("玉山金控", "金融保險業"),
    "2891": ("中國信託銀行", "金融保險業"),
    "2882": ("國泰金控", "金融保險業"),
    "2881": ("台北富邦銀行", "金融保險業"),
    "5880": ("合作金庫銀行", "金融保險業"),
    "2892": ("第一銀行", "金融保險業"),
    "2801": ("彰化銀行", "金融保險業"),
    "2887": ("台新金控", "金融保險業"),
    "1102": ("亞洲水泥", "水泥工業"),
    "1402": ("遠東新世紀", "紡織纖維"),
    "1909": ("榮成紙業", "造紙工業"),
    "1460": ("宏遠興業", "紡織纖維"),
    "2002": ("中鋼公司", "鋼鐵工業"),
    "2912": ("統一超商", "貿易百貨"),
    "5903": ("全家便利商店", "貿易百貨"),
    "9907": ("台灣中油", "油電燃氣業"),
    "2890": ("永豐銀行", "金融保險業"),
    "5434": ("崇越科技", "電子通路業"),
    "2618": ("長榮航空", "航運業"),
    "2352": ("佳世達集團", "電腦及週邊設備業"),
    "2888": ("新光人壽", "金融保險業"),
    "2867": ("南山產物", "金融保險業"),
    "2883": ("開發金控", "金融保險業"),
    "2308": ("台達電", "電機機械"),
    "2412": ("中華電信", "通信網路業"),
    "1301": ("台塑", "塑膠工業"),
    "2303": ("聯電", "半導體業"),
    "2382": ("廣達", "電腦及週邊設備業")
}

async def download_esg_report(company_name, stock_code, industry, year):
    page_log = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Step 1: Navigate to the page
            await page.goto("https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW")
            await page.wait_for_timeout(2000)
            page_log.append("Step 1: 頁面加載完成")
            
            # Step 2: Select market type: 上市
            await page.click('input[placeholder="市場別*"]')
            await page.wait_for_timeout(500)
            await page.click('text=上市')
            await page.wait_for_timeout(500)
            page_log.append("Step 2: 選擇市場別 (上市)")
            
            # Step 3: Fill report year
            await page.click('input[placeholder="報告年度*"]')
            await page.wait_for_timeout(500)
            await page.click(f'text={year}')
            await page.wait_for_timeout(500)
            page_log.append(f"Step 3: 選擇年度 ({year})")
            
            # Step 4: Fill company code
            await page.click('input[placeholder="公司代號"]')
            await page.fill('input[placeholder="公司代號"]', stock_code)
            await page.wait_for_timeout(1000)
            await page.click(f'text={stock_code} {company_name}')
            await page.wait_for_timeout(500)
            page_log.append(f"Step 4: 選擇公司 ({company_name})")
            
            # Step 4b: Click search and wait for network idle
            await page.click('button:has-text("查詢")')
            page_log.append("Step 4b: 點擊查詢按鈕")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)
            page_log.append("Step 4c: 等待網路空閒完成")
            
            # Step 5a: Wait for results
            await page.wait_for_selector(f'text={stock_code}-{company_name}', timeout=15000)
            page_log.append("Step 5a: 找到查詢結果")
            
            # Step 5b: Try different selectors to expand result
            expand_selectors = [
                f'text={stock_code}-{company_name}',
                'img[class*="arrow"]',
                'svg[class*="arrow"]',
                'button[class*="expand"]',
                '[class*="expand-icon"]'
            ]
            
            expanded = False
            for selector in expand_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        await element.click()
                        await page.wait_for_timeout(2000)
                        page_log.append(f"Step 5b: 使用 '{selector}' 展開結果成功")
                        expanded = True
                        break
                except Exception as ex:
                    pass
            
            if not expanded:
                page_log.append("Step 5b: Warning - 未找到展開按鈕，嘗試繼續")
            
            # Step 5c: Wait a bit more for content to load after expansion
            await page.wait_for_timeout(2000)
            page_log.append("Step 5c: 等待展開後的內容加載")
            
            # Step 6: Scroll down in multiple steps to find download section
            for i in range(3):
                await page.evaluate(f'window.scrollBy(0, 400)')
                await page.wait_for_timeout(800)
            page_log.append("Step 6: 向下滾動頁面多次")
            
            # Step 7: Try to find download button with multiple selectors
            download_selectors = [
                'text=下載 PDF',
                'button:has-text("下載")',
                'a:has-text("下載")',
                '[class*="download"]',
                'text=下載',
                'text=PDF',
                '[class*="pdf"]'
            ]
            
            download_button = None
            for selector in download_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=5000):
                        download_button = btn
                        page_log.append(f"Step 7a: 找到下載按鈕，使用selector '{selector}'")
                        break
                except:
                    pass
            
            if not download_button:
                page_log.append("Step 7a: ERROR - 無法找到任何下載按鈕")
                raise Exception("Download button not found with any selector")
            
            # Step 7b: Click download button
            try:
                download_promise = page.wait_for_event('download')
                await download_button.click()
                page_log.append("Step 7b: 點擊下載按鈕成功")
            except Exception as e:
                page_log.append(f"Step 7b: 第一次點擊失敗: {str(e)}")
                # Try to scroll into view and click again
                try:
                    await download_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    download_promise = page.wait_for_event('download')
                    await download_button.click()
                    page_log.append("Step 7b: 滾動後第二次點擊成功")
                except Exception as e2:
                    raise Exception(f"Failed to click download button: {str(e2)}")
            
            download = await download_promise
            page_log.append("Step 8: 下載事件完成")
            
            # Step 9: Save file
            company_dir = f"{BASE_DIR}\\{industry}\\{company_name}_{stock_code}"
            os.makedirs(company_dir, exist_ok=True)
            save_path = f"{company_dir}\\{year}.pdf"
            await download.save_as(save_path)
            page_log.append(f"Step 9: 檔案保存於 {company_dir}\\{year}.pdf")
            
            await browser.close()
            
            # Print all steps
            for log in page_log:
                print(f"  {log}")
            
            return True, None
        
    except Exception as e:
        # Print all steps completed before error
        for log in page_log:
            print(f"  {log}")
        print(f"  ERROR: {str(e)}")
        return False, str(e)

async def main():
    print("開始下載 ESG 報告書...\n")
    print("測試模式：只下載日月光投控 (3711)\n")
    year = "2024"
    success_count = 0
    failed_count = 0
    failed_list = []
    
    # 測試日月光投控
    test_companies = {"3711": COMPANIES["3711"]}
    total = 1
    
    for stock_code, (company_name, industry) in test_companies.items():
        print(f"正在下載 {company_name}({stock_code})...")
        
        success, error = await download_esg_report(company_name, stock_code, industry, year)
        
        if success:
            print(f"✓ {industry}\\{company_name}_{stock_code}\\{year}.pdf\n")
            success_count += 1
        else:
            print(f"✗ {company_name} → {error}\n")
            failed_count += 1
            failed_list.append((company_name, error))
    
    print("\n" + "="*60)
    print(f"成功: {success_count}/{total}")
    print(f"失敗: {failed_count}/{total}")
    
    if failed_list:
        print("\n失敗詳情：")
        for company, error in failed_list:
            print(f"  - {company}: {error}")

if __name__ == "__main__":
    asyncio.run(main())