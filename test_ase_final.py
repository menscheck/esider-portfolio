# -*- coding: utf-8 -*-
"""
最終版：雙擊展開 + 滾動 + 改進的 PDF 掃描
"""
import asyncio
import os
import requests
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
DOWNLOAD_DIR = "data/reports/日月光投控"

async def select_and_query(page):
    """選取條件並查詢。"""
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

    # 點擊查詢
    btn = await page.query_selector('button:has-text("查詢")')
    if btn:
        await btn.click()
        await page.wait_for_timeout(3000)

    print("✓ 條件選取和查詢完成")


async def expand_and_scan(page):
    """雙擊展開 + 滾動 + 掃描 PDF。"""
    print("\n【展開並掃描 PDF】")

    # 雙擊該行
    print("  1. 雙擊該公司列...")
    rows = await page.query_selector_all('tr, [class*="row"]')
    for row in rows:
        txt = await row.inner_text()
        if '3711' in txt:
            await row.dblclick()
            await page.wait_for_timeout(1500)
            print("    ✓ 雙擊成功")
            break

    # 滾動到底部
    print("  2. 向下滾動...")
    for i in range(10):
        await page.evaluate("window.scrollBy(0, 300)")
        await page.wait_for_timeout(200)
    await page.wait_for_timeout(1000)
    print("    ✓ 滾動完成")

    # 掃描 PDF 連結
    print("  3. 掃描 PDF 連結...")

    # 方法 1：直接掃描所有 <a> 標籤
    pdfs = []
    anchors = await page.query_selector_all('a[href]')
    for a in anchors:
        href = await a.get_attribute('href') or ''
        text = (await a.inner_text()).strip()
        if 'pdf' in href.lower() or 'pdf' in text.lower() or '下載' in text or '報告' in text:
            pdfs.append({'href': href, 'text': text})

    # 方法 2：掃描原始碼中的 PDF URL
    import re
    content = await page.content()
    for m in re.findall(r'https?://[^\s"\'<>]+\.pdf', content, re.IGNORECASE):
        if not any(p['href'] == m for p in pdfs):
            pdfs.append({'href': m, 'text': 'source_scan'})

    if pdfs:
        print(f"    ✓ 找到 {len(pdfs)} 個 PDF 候選")
        for i, p in enumerate(pdfs[:5]):
            print(f"      [{i}] {p['text'][:40]!r} -> {p['href'][:60]}")
        return pdfs
    else:
        print("    ✗ 未找到任何 PDF")
        # 列出所有連結供診斷
        print("    頁面上所有連結：")
        for i, a in enumerate(anchors[:10]):
            href = await a.get_attribute('href') or ''
            text = (await a.inner_text()).strip()[:40]
            print(f"      [{i}] {text!r} -> {href[:60]}")
        return []


async def download_pdf(url):
    """下載 PDF。"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filepath = os.path.join(DOWNLOAD_DIR, "日月光投控_ESG_2024.pdf")

    try:
        print(f"\n  下載：{url}")
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(resp.content)

        abs_path = os.path.abspath(filepath)
        size_kb = os.path.getsize(filepath) // 1024
        print(f"  ✓ 下載成功")
        print(f"  路徑：{abs_path}")
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
        print("【步驟 1-3】頁面載入、選條件、查詢")
        print("=" * 60)
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        await select_and_query(page)

        print("\n" + "=" * 60)
        print("【步驟 4-5】展開並掃描 PDF")
        print("=" * 60)
        pdfs = await expand_and_scan(page)
        await page.screenshot(path="sc_final_after_scan.png")
        print("  截圖：sc_final_after_scan.png")

        if pdfs:
            print("\n" + "=" * 60)
            print("【步驟 6】下載 PDF")
            print("=" * 60)
            # 選最合適的（優先選有 https 的、或最長的 URL）
            best = next((p for p in pdfs if p['href'].startswith('https')), pdfs[0])
            await download_pdf(best['href'])
        else:
            print("\n✗ 未找到 PDF，無法下載")

        print("\n" + "=" * 60)
        print("全部步驟完成，按 Enter 關閉...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
