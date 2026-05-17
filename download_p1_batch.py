"""
download_p1_batch.py
P2批次公司 ESG報告書下載
- 自動判斷市場別（上市/上櫃）
- 跳過已有PDF的公司
- 存檔到 data/reports/{公司名}/
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

# P2 批次公司（兩個指數上榜）+ 市場別
P2_COMPANIES = {
    # 台灣50 + 公司治理100
    "仁寶": ("2324", "上市"),
    "鴻準": ("2354", "上市"),
    "群光": ("2385", "上市"),
    "南亞科": ("2408", "上市"),
    "友達": ("2409", "上市"),
    "可成": ("2474", "上市"),
    "華航": ("2610", "上市"),
    "台灣高鐵": ("2633", "上市"),
    "文曄": ("3036", "上市"),
    "健鼎": ("3044", "上市"),
    "群創": ("3481", "上市"),
    "大聯大": ("3702", "上市"),
    "力成": ("6239", "上市"),
    "南電": ("8046", "上市"),
    "寶成": ("9904", "上市"),
    "豐泰": ("9910", "上市"),
    "巨大": ("9921", "上市"),
    # 台灣50 + 高薪100
    "奇鋐": ("3017", "上市"),
    "光寶科": ("2301", "上市"),
    "和碩": ("4938", "上市"),
    # 公司治理100 + 高薪100
    "儒鴻": ("1476", "上市"),
    "東元": ("1504", "上市"),
    "正新": ("2105", "上市"),
    "和泰車": ("2207", "上市"),
    "宏碁": ("2353", "上市"),
    "微星": ("2377", "上市"),
    "研華": ("2395", "上市"),
    "京城銀": ("2809", "上市"),
    "臺企銀": ("2834", "上市"),
    "中租": ("5871", "上市"),
    "上海商銀": ("5876", "上市"),
    "群益證": ("6005", "上市"),
    "國巨": ("2327", "上市"),
}

REPORTS_DIR = Path(r"C:\Users\Sam Joseph\esg-agent\data\reports")


def should_skip(company: str) -> bool:
    company_dir = REPORTS_DIR / company
    if company_dir.exists():
        pdfs = list(company_dir.glob("*.pdf"))
        if pdfs:
            sizes = [p.stat().st_size for p in pdfs]
            if any(s > 1_000_000 for s in sizes):  # >1MB才算有效
                print(f"  [SKIP] 已有PDF：{pdfs[0].name}（{sizes[0]//1024}KB）")
                return True
    return False


async def download_one(company: str, code: str, market: str) -> bool:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(
                "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW",
                wait_until='networkidle'
            )
            await page.wait_for_timeout(2000)

            # 市場別 - 下拉選單
            market_dropdown = page.locator('div').filter(has=page.locator('input[placeholder="市場別*"]')).first
            await market_dropdown.click()
            await page.wait_for_timeout(1000)

            option = page.get_by_role("option", name=market)
            if await option.count() > 0:
                await option.first.click()
            else:
                # fallback：直接找頁面上精確文字
                try:
                    await page.locator(f'div.v-select__content >> text="{market}"').click()
                except Exception:
                    # 更暴力的方式
                    await page.locator('input[placeholder="市場別*"]').click()
                    await page.wait_for_timeout(1000)
                    await page.evaluate(f"""
                        () => {{
                            const els = [...document.querySelectorAll('div')].filter(el => 
                                el.textContent.trim() === '{market}' && 
                                el.offsetParent !== null
                            );
                            if (els.length > 0) els[0].click();
                        }}
                    """)
            await page.wait_for_timeout(500)

            # 報告年度 - 下拉選單
            year_dropdown = page.locator('div').filter(has=page.locator('input[placeholder="報告年度*"]')).first
            await year_dropdown.click()
            await page.wait_for_timeout(1000)

            year_option = page.get_by_role("option", name="2024")
            if await year_option.count() > 0:
                await year_option.first.click()
            else:
                try:
                    await page.locator(f'div.v-select__content >> text="2024"').click()
                except Exception:
                    await page.locator('input[placeholder="報告年度*"]').click()
                    await page.wait_for_timeout(1000)
                    await page.evaluate("""
                        () => {
                            const els = [...document.querySelectorAll('div')].filter(el => 
                                el.textContent.trim() === '2024' && 
                                el.offsetParent !== null
                            );
                            if (els.length > 0) els[0].click();
                        }
                    """)
            await page.wait_for_timeout(500)

            # 公司代號 - 文字輸入 + autocomplete 選項
            code_input = page.locator('input[placeholder="公司代號"]')
            await code_input.click()
            await page.wait_for_timeout(300)
            await page.keyboard.type(code)
            await page.wait_for_timeout(1000)  # 等 autocomplete 出現

            autocomplete_item = page.locator(f'text={code}').last
            await autocomplete_item.wait_for(state='visible', timeout=5000)
            await autocomplete_item.click()
            await page.wait_for_timeout(500)

            # 查詢
            query_btn = page.locator('button:has-text("查詢")')
            await query_btn.wait_for(state='visible', timeout=5000)
            await page.wait_for_timeout(1000)

            # 截圖 debug（在按下查詢前）
            await page.screenshot(path=f"debug_{company}.png")
            print(f"  截圖已存：debug_{company}.png")

            # 只點擊可用的查詢按鈕
            enabled_query_btn = page.locator('button:has-text("查詢"):not([disabled])')
            await enabled_query_btn.wait_for(state='visible', timeout=5000)
            await enabled_query_btn.click()
            await page.wait_for_timeout(3000)

            # 嘗試多種格式找結果列
            found = False
            for text in [f'{code}-{company}', f'{code} {company}', code, company]:
                try:
                    locator = page.locator(f'text={text}').first
                    await locator.wait_for(state='visible', timeout=3000)
                    await locator.click()
                    found = True
                    print(f"  找到結果：'{text}'")
                    break
                except:
                    continue

            await page.wait_for_timeout(1500)

            # 先檢查頁面上所有的 button、div 文本內容
            all_buttons = await page.locator('button').all_text_contents()
            print(f"  頁面上的按鈕: {all_buttons[:15]}")

            # 列出頁面上所有含「下載」「PDF」「報告」的文本
            all_text = await page.locator('*').all_text_contents()
            pdf_items = [t for t in all_text if '下載' in t or 'PDF' in t or '報告' in t]
            print(f"  含下載/PDF/報告的文本: {pdf_items[:20]}")

            # 直接點擊結果項目展開
            result_item = page.locator(f'text="{code}-{company}"')
            await result_item.click()
            await page.wait_for_timeout(1500)

            # 再次檢查是否有下載連結出現
            all_text_after = await page.locator('*').all_text_contents()
            pdf_items_after = [t for t in all_text_after if '下載' in t or 'PDF' in t or '報告' in t]
            print(f"  點擊後含下載/PDF/報告的文本: {pdf_items_after[:20]}")

            # 在右側結果區域 scroll down 到下載連結
            await page.evaluate("""
                () => {
                    const resultPanel = document.querySelector('[class*="result-content"], [class*="right-panel"], .layout-box');
                    if (resultPanel) {
                        resultPanel.scrollTop += 1000;
                    }
                }
            """)
            await page.wait_for_timeout(800)

            # 截圖看展開後的結果
            await page.screenshot(path=f"debug_expanded_{company}.png")
            print(f"  截圖已存：debug_expanded_{company}.png")

            # 優先找「修正後報告書」的下載PDF，沒有才用原始版
            revised_links = page.locator('tr:has-text("修正後報告書") >> text=下載 PDF')
            revised_count = await revised_links.count()
            company_dir = REPORTS_DIR / company
            company_dir.mkdir(parents=True, exist_ok=True)

            if revised_count > 0:
                print(f"  [INFO] 找到修正後報告書，優先下載")
                async with page.expect_download() as dl_info:
                    await revised_links.first.click()
            else:
                # fallback：下載原始版
                download_links = page.locator('text=下載 PDF')
                count = await download_links.count()
                if count == 0:
                    print(f"  [WARN] 找不到PDF連結")
                    await browser.close()
                    return False
                async with page.expect_download() as dl_info:
                    await download_links.first.click()
            download = await dl_info.value

            filepath = company_dir / f"{company}_ESG_2024.pdf"
            await download.save_as(str(filepath))

            size = filepath.stat().st_size
            if size < 1_000_000:
                print(f"  [WARN] PDF太小（{size//1024}KB），請人工確認")
            else:
                print(f"  [OK] {filepath.name}（{size//1024//1024}MB）")

            await browser.close()
            return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        try:
            await page.screenshot(path=f"error_{company}.png")
            print(f"  錯誤截圖已存：error_{company}.png")
        except Exception:
            pass
        return False


async def main():
    print("=" * 55)
    print("P2 批次公司 ESG 報告書下載")
    print("=" * 55)

    # 預覽
    to_download = []
    for company, (code, market) in P2_COMPANIES.items():
        if should_skip(company):
            pass
        else:
            to_download.append((company, code, market))
            print(f"  [待下載] {company} ({code}) [{market}]")

    print(f"\n共 {len(to_download)} 家待下載，{len(P2_COMPANIES)-len(to_download)} 家跳過")
    input("\n確認後按 Enter 開始下載...")

    success, fail = 0, 0
    for company, code, market in to_download:
        print(f"\n處理 {company} ({code})...")
        if await download_one(company, code, market):
            success += 1
        else:
            fail += 1

    print(f"\n{'='*55}")
    print(f"完成：成功 {success} 家，失敗 {fail} 家")
    print(f"{'='*55}")


asyncio.run(main())
