"""
download_p3_batch.py
P3批次公司 ESG報告書下載（54家）
流程：市場別 → 報告年度 → (產業別跳過) → 公司代號輸入 → autocomplete點擊 → 查詢 → 展開結果 → 下載PDF
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

P3_COMPANIES = {
    "富邦金":   ("2881", "上市"),
    "中信金":   ("2891", "上市"),
    "新光金":   ("2888", "上市"),
    "國票金":   ("2889", "上市"),
    "中壽":     ("2823", "上市"),
    "三商壽":   ("2867", "上市"),
    "京城銀":   ("2809", "上市"),
    "裕融":     ("9941", "上市"),
    "世芯-KY":  ("3661", "上市"),
    "京元電子": ("2449", "上市"),
    "華邦電":   ("2344", "上市"),
    "創意":     ("3443", "上市"),
    "台勝科":   ("3532", "上市"),
    "超豐":     ("2441", "上市"),
    "新唐":     ("4919", "上市"),
    "盛群":     ("6202", "上市"),
    "台燿":     ("2383", "上市"),
    "金像電":   ("2368", "上市"),
    "華通":     ("2313", "上市"),
    "健策":     ("3653", "上市"),
    "敬鵬":     ("2355", "上市"),
    "信邦":     ("3023", "上市"),
    "京鼎":     ("3413", "上市"),
    "致茂":     ("2360", "上市"),
    "啟碁":     ("6285", "上市"),
    "旭隼":     ("6409", "上市"),
    "群電":     ("6412", "上市"),
    "智邦":     ("2345", "上市"),
    "聯強":     ("2347", "上市"),
    "藍天":     ("2362", "上市"),
    "技嘉":     ("2376", "上市"),
    "貿聯-KY":  ("3665", "上市"),
    "富邦媒":   ("8454", "上市"),
    "敦陽科":   ("2480", "上市"),
    "士電":     ("1503", "上市"),
    "中興電":   ("1513", "上市"),
    "華城":     ("1519", "上市"),
    "中鼎":     ("9933", "上市"),
    "裕民":     ("2606", "上市"),
    "萬海":     ("2615", "上市"),
    "裕隆":     ("2201", "上市"),
    "中華":     ("2204", "上市"),
    "長興":     ("1717", "上市"),
    "亞聚":     ("1308", "上市"),
    "中化生":   ("1762", "上市"),
    "東和鋼鐵": ("2006", "上市"),
    "聚陽":     ("1477", "上市"),
    "聯華":     ("1229", "上市"),
    "鴻勁":     ("7769", "上市"),
    "億豐":     ("8464", "上市"),
    "信義":     ("9940", "上市"),
    "潤泰新":   ("9945", "上市"),
    "興富發":   ("2542", "上市"),
    "群益期":   ("6024", "上市"),
}

REPORTS_DIR = Path(r"C:\Users\Sam Joseph\esg-agent\data\reports")


def should_skip(company: str) -> bool:
    company_dir = REPORTS_DIR / company
    if company_dir.exists():
        pdfs = list(company_dir.glob("*.pdf"))
        if pdfs:
            sizes = [p.stat().st_size for p in pdfs]
            if any(s > 1_000_000 for s in sizes):
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
                wait_until="networkidle"
            )
            await page.wait_for_timeout(2000)

            # 步驟1：市場別
            await page.locator('div').filter(
                has=page.locator('input[placeholder="市場別*"]')
            ).first.click()
            await page.wait_for_timeout(800)
            await page.evaluate(f"""
                () => {{
                    const els = [...document.querySelectorAll('div[role="option"], .v-list-item')].filter(
                        el => el.textContent.trim() === '{market}' && el.offsetParent !== null
                    );
                    if (els.length > 0) els[0].click();
                }}
            """)
            await page.wait_for_timeout(500)

            # 步驟2：報告年度
            await page.locator('div').filter(
                has=page.locator('input[placeholder="報告年度*"]')
            ).first.click()
            await page.wait_for_timeout(800)
            await page.evaluate("""
                () => {
                    const els = [...document.querySelectorAll('div[role="option"], .v-list-item')].filter(
                        el => el.textContent.trim() === '2024' && el.offsetParent !== null
                    );
                    if (els.length > 0) els[0].click();
                }
            """)
            await page.wait_for_timeout(500)

            # 步驟3：產業別跳過

            # 步驟4：公司代號 輸入 → 等autocomplete → 點擊第一個結果
            code_input = page.locator('input[placeholder="公司代號"]')
            await code_input.click()
            await page.wait_for_timeout(300)
            await code_input.fill(code)
            await page.wait_for_timeout(1200)

            # 點擊 autocomplete 下拉出現的完整名稱（含代碼）
            autocomplete = page.locator('div[role="option"]').filter(has_text=code).first
            try:
                await autocomplete.wait_for(state="visible", timeout=5000)
                await autocomplete.click()
            except Exception:
                # fallback：直接點第一個 option
                await page.locator('div[role="option"]').first.click()
            await page.wait_for_timeout(500)

            # 步驟5：查詢（等按鈕變可用）
            query_btn = page.locator('button:has-text("查詢"):not([disabled])')
            await query_btn.wait_for(state="visible", timeout=8000)
            await query_btn.click()
            await page.wait_for_timeout(3000)

            # 步驟6：點擊結果列展開
            found = False
            for text in [f"{code}", company, f"{code}-{company}"]:
                try:
                    loc = page.locator(f'text={text}').first
                    await loc.wait_for(state="visible", timeout=3000)
                    await loc.click()
                    found = True
                    print(f"  找到結果：'{text}'")
                    break
                except Exception:
                    continue

            if not found:
                print(f"  [WARN] 找不到查詢結果，截圖存檔")
                await page.screenshot(path=f"error_{company}.png")
                await browser.close()
                return False

            await page.wait_for_timeout(1500)

            # 步驟7：下載PDF（優先修正後報告書）
            company_dir = REPORTS_DIR / company
            company_dir.mkdir(parents=True, exist_ok=True)

            revised = page.locator('tr:has-text("修正後報告書")').locator('text=下載 PDF')
            if await revised.count() > 0:
                print(f"  [INFO] 使用修正後報告書")
                async with page.expect_download() as dl_info:
                    await revised.first.click()
            else:
                dl_links = page.locator('text=下載 PDF')
                if await dl_links.count() == 0:
                    print(f"  [WARN] 找不到PDF連結")
                    await page.screenshot(path=f"error_{company}.png")
                    await browser.close()
                    return False
                async with page.expect_download() as dl_info:
                    await dl_links.first.click()

            download = await dl_info.value
            filepath = company_dir / f"{company}_ESG_2024.pdf"
            await download.save_as(str(filepath))
            size = filepath.stat().st_size

            if size < 1_000_000:
                print(f"  [WARN] PDF偏小（{size//1024}KB），請確認")
            else:
                print(f"  [OK] {filepath.name}（{size//1024//1024}MB）")

            await browser.close()
            return True

    except Exception as e:
        print(f"  [ERROR] {company}({code}): {e}")
        try:
            await page.screenshot(path=f"error_{company}.png")
        except Exception:
            pass
        return False


async def main():
    print("=" * 55)
    print("P3 批次公司 ESG 報告書下載（54家）")
    print("=" * 55)

    to_download = []
    skipped = 0
    for company, (code, market) in P3_COMPANIES.items():
        if should_skip(company):
            skipped += 1
        else:
            to_download.append((company, code, market))
            print(f"  [待下載] {company} ({code})")

    print(f"\n共 {len(to_download)} 家待下載，{skipped} 家跳過")
    input("\n確認後按 Enter 開始下載...")

    success, fail = 0, 0
    failed_list = []
    for company, code, market in to_download:
        print(f"\n▶ {company} ({code})...")
        ok = await download_one(company, code, market)
        if ok:
            success += 1
        else:
            fail += 1
            failed_list.append(f"{company}({code})")

    print(f"\n{'='*55}")
    print(f"完成：成功 {success} 家，失敗 {fail} 家")
    if failed_list:
        print(f"失敗清單：{', '.join(failed_list)}")
    print(f"{'='*55}")


asyncio.run(main())
