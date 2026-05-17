# -*- coding: utf-8 -*-
"""
批量下載 34 家公司的 2024 年 ESG 報告書
基於 test_ase_button_fixed.py 的成功邏輯
"""
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
BASE_DIR = "C:\\Users\\Sam Joseph\\esg-agent\\data\\reports"

COMPANIES = [
    ("2330", "台積電"), ("3711", "日月光投控"), ("8069", "元太科技"),
    ("2317", "鴻海精密"), ("2325", "矽品精密工業"), ("3037", "欣興電子"),
    ("2884", "玉山金控"), ("2891", "中國信託銀行"), ("2882", "國泰金控"),
    ("2881", "台北富邦銀行"), ("5880", "合作金庫銀行"), ("2892", "第一銀行"),
    ("2801", "彰化銀行"), ("2887", "台新金控"), ("1102", "亞洲水泥"),
    ("1402", "遠東新世紀"), ("1909", "榮成紙業"), ("1460", "宏遠興業"),
    ("2002", "中鋼公司"), ("2912", "統一超商"), ("5903", "全家便利商店"),
    ("9907", "台灣中油"), ("2890", "永豐銀行"), ("5434", "崇越科技"),
    ("2618", "長榮航空"), ("2352", "佳世達集團"), ("2888", "新光人壽"),
    ("2867", "南山產物"), ("2308", "台達電"), ("2412", "中華電信"),
    ("1301", "台塑"), ("2303", "聯電"), ("2382", "廣達"), ("2883", "開發金控")
]


async def select_and_query(page, company_code, company_name):
    """選取條件並查詢。"""
    # 市場別 = 上市
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[0].click()")
    await page.wait_for_timeout(600)
    await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim() === target) {
                    item.click();
                }
            }
        }
    """, "上市")
    await page.wait_for_timeout(400)

    # 報告年度 = 2024
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[1].click()")
    await page.wait_for_timeout(600)
    await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim() === target) {
                    item.click();
                }
            }
        }
    """, "2024")
    await page.wait_for_timeout(400)

    # 公司代號 - 使用代號查詢
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[3].click()")
    await page.wait_for_timeout(600)

    # 在下拉菜單中尋找該公司代號
    search_text = f"{company_code} {company_name}"
    found = await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim().includes(target)) {
                    item.click();
                    return true;
                }
            }
            return false;
        }
    """, company_code)

    await page.wait_for_timeout(400)

    if not found:
        return False

    # 點擊查詢
    try:
        btn = await page.query_selector('button:has-text("查詢")')
        if btn:
            await btn.click()
            await page.wait_for_timeout(2500)
            return True
    except Exception:
        pass

    return False


async def download_pdf(page, company_name):
    """找下載按鈕並下載。"""
    try:
        # 找「下載 PDF」按鈕
        all_buttons = await page.query_selector_all('div[class*="_link-icon-button-box"]')

        download_buttons = []
        for btn in all_buttons:
            text = (await btn.inner_text()).strip()
            if '下載 PDF' in text or text == '下載 PDF':
                download_buttons.append(btn)

        if len(download_buttons) == 0:
            return None

        # 第一個是中文版
        company_dir = os.path.join(BASE_DIR, company_name)
        os.makedirs(company_dir, exist_ok=True)
        filepath = os.path.join(company_dir, f"{company_name}_ESG_2024.pdf")

        async with page.expect_download(timeout=10000) as dl_info:
            await download_buttons[0].click()

        download = await dl_info.value
        await download.save_as(filepath)

        return filepath
    except Exception as e:
        return None


async def process_company(browser, company_code, company_name, index, total):
    """處理單家公司。"""
    page = await browser.new_page()
    try:
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(1000)

        # 選條件 + 查詢
        query_ok = await select_and_query(page, company_code, company_name)
        if not query_ok:
            print(f"  [{index:2d}/{total}] ✗ {company_name:15s} (查詢失敗)")
            return False

        # 下載
        filepath = await download_pdf(page, company_name)
        if filepath:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  [{index:2d}/{total}] ✓ {company_name:15s} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  [{index:2d}/{total}] ✗ {company_name:15s} (下載失敗)")
            return False

    except Exception as e:
        print(f"  [{index:2d}/{total}] ✗ {company_name:15s} ({str(e)[:30]})")
        return False
    finally:
        await page.close()


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        print("=" * 70)
        print("【批量下載 34 家公司的 2024 年 ESG 報告書】")
        print("=" * 70)
        print(f"開始時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        results = []
        for i, (code, name) in enumerate(COMPANIES, 1):
            success = await process_company(browser, code, name, i, len(COMPANIES))
            results.append((code, name, success))

            # 每 5 家暫停一下，避免伺服器問題
            if i % 5 == 0:
                await asyncio.sleep(2)

        await browser.close()

        # 統計結果
        print("\n" + "=" * 70)
        print("【下載統計】")
        print("=" * 70)

        success_count = sum(1 for _, _, success in results if success)
        fail_count = len(COMPANIES) - success_count

        print(f"\n成功：{success_count}/{len(COMPANIES)}")
        print(f"失敗：{fail_count}/{len(COMPANIES)}")

        if fail_count > 0:
            print("\n【失敗列表】")
            for code, name, success in results:
                if not success:
                    print(f"  • {name} ({code})")

        print(f"\n結束時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run())
