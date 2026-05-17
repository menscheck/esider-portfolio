# -*- coding: utf-8 -*-
"""
直接找 div[class*="_link-icon-button-box"] 下載按鈕
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
DOWNLOAD_DIR = "data/reports/日月光投控"

async def select_and_query(page):
    """選取條件並查詢。"""
    print("【步驟 1-2：選條件 + 查詢】")

    # 市場別
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[0].click()")
    await page.wait_for_timeout(800)
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
    await page.wait_for_timeout(600)
    print("  ✓ 市場別 = 上市")

    # 報告年度
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[1].click()")
    await page.wait_for_timeout(800)
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
    await page.wait_for_timeout(600)
    print("  ✓ 報告年度 = 2024")

    # 公司代號
    await page.evaluate("() => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[3].click()")
    await page.wait_for_timeout(800)
    await page.evaluate("""
        (target) => {
            const items = document.querySelectorAll('.option-item');
            for (const item of items) {
                if (item.offsetParent !== null && item.textContent.trim() === target) {
                    item.click();
                }
            }
        }
    """, "3711 日月光投控")
    await page.wait_for_timeout(600)
    print("  ✓ 公司代號 = 3711 日月光投控")

    # 點擊查詢
    btn = await page.query_selector('button:has-text("查詢")')
    if btn:
        await btn.click()
        await page.wait_for_timeout(3000)
        print("  ✓ 查詢成功")


async def download_pdf(page):
    """找下載按鈕並下載。"""
    print("\n【步驟 3：找下載按鈕】")

    # 直接找下載按鈕（不需要滾動）
    download_btns = await page.query_selector_all('div[class*="_link-icon-button-box"]')
    print(f"  找到 {len(download_btns)} 個下載按鈕")

    if len(download_btns) == 0:
        print("  ✗ 未找到下載按鈕")
        # 診斷：列出頁面上所有 div[class*="_link"]
        divs = await page.query_selector_all('div[class*="_link"]')
        print(f"  診斷：找到 {len(divs)} 個包含 '_link' 的 div")
        for i, d in enumerate(divs[:5]):
            cls = await d.get_attribute('class') or ''
            txt = (await d.inner_text()).strip()[:40]
            print(f"    [{i}] class={cls[:50]!r}  text={txt!r}")
        return None

    # 列出所有按鈕
    print("  下載按鈕列表：")
    for i, btn in enumerate(download_btns):
        text = (await btn.inner_text()).strip()
        cls = await btn.get_attribute('class') or ''
        print(f"    [{i}] {text[:30]!r}  (class: {cls[:50]})")

    # 第一個是中文版
    print(f"\n【步驟 4：點擊第 1 個按鈕（中文版）下載】")
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        filepath = os.path.join(DOWNLOAD_DIR, "日月光投控_ESG_2024.pdf")

        async with page.expect_download(timeout=15000) as dl_info:
            await download_btns[0].click()

        download = await dl_info.value
        await download.save_as(filepath)

        abs_path = os.path.abspath(filepath)
        size_kb = os.path.getsize(filepath) // 1024
        print(f"  ✓ 下載成功")
        print(f"  存檔：{abs_path}")
        print(f"  大小：{size_kb} KB")
        return filepath
    except Exception as e:
        print(f"  ✗ 下載失敗：{e}")
        return None


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 60)
        print("【日月光投控(3711) ESG 報告書下載】")
        print("=" * 60 + "\n")

        # 開啟頁面
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        print("【步驟 0：頁面載入】")
        print("  ✓ ESGGenPlus 平台載入完成\n")

        # 選條件 + 查詢
        await select_and_query(page)

        # 下載
        result = await download_pdf(page)

        # 結果
        print("\n" + "=" * 60)
        if result:
            print("✓ 下載完成！")
        else:
            print("✗ 下載失敗")
        print("=" * 60)

        print("\n按 Enter 關閉瀏覽器...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
