# -*- coding: utf-8 -*-
"""
修正版：展開後向下滾動找中文版報告書的下載連結
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW"
DOWNLOAD_DIR = "data/reports/日月光投控"

async def select_dropdown(page, index, target_text, label):
    """點開第 index 個 dropdown 並選取 target_text 的選項。"""
    try:
        await page.evaluate(f"""
            () => document.querySelectorAll('._dropdown-content-box_1tpm0_9')[{index}].click()
        """)
        await page.wait_for_timeout(800)

        clicked = await page.evaluate(f"""
            (target) => {{
                const items = document.querySelectorAll('.option-item');
                for (const item of items) {{
                    if (item.offsetParent !== null && item.textContent.trim() === target) {{
                        item.click();
                        return true;
                    }}
                }}
                return false;
            }}
        """, target_text)

        await page.wait_for_timeout(600)
        if clicked:
            print(f"  ✓ {label} 選取成功：{target_text!r}")
        else:
            print(f"  ✗ {label} 找不到選項：{target_text!r}")
        return clicked
    except Exception as e:
        print(f"  ✗ {label} 操作異常：{e}")
        return False


async def click_query_button(page):
    """點擊查詢按鈕。"""
    try:
        btn = await page.query_selector('button:has-text("查詢")')
        if btn:
            await btn.click()
            await page.wait_for_timeout(2500)
            print(f"  ✓ 查詢按鈕點擊成功")
            return True
        print("  ✗ 找不到查詢按鈕")
        return False
    except Exception as e:
        print(f"  ✗ 查詢按鈕異常：{e}")
        return False


async def expand_and_find_pdf(page):
    """展開該列，向下滾動找到中文版報告書的下載連結。"""
    await page.wait_for_timeout(1500)

    print("  【步驟 1】點擊該列展開...")
    try:
        rows = await page.query_selector_all('tr, [class*="row"]')
        for row in rows:
            txt = await row.inner_text()
            if '3711' in txt:
                print(f"    找到該公司列，點擊展開...")
                await row.click()
                await page.wait_for_timeout(1500)
                break
    except Exception as e:
        print(f"    點擊行失敗：{e}")

    print("  【步驟 2】向下滾動到頁面底部...")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1500)
    await page.screenshot(path="sc_after_scroll.png")
    print(f"    截圖：sc_after_scroll.png")

    print("  【步驟 3】尋找中文版報告書的下載連結...")

    # 方法 1：直接找文本「中文版報告書」附近的下載連結
    result = await page.evaluate('''
        () => {
            const sections = document.querySelectorAll('*');
            for (let el of sections) {
                const text = el.textContent || '';
                if (text.includes('中文版報告書')) {
                    console.log('找到中文版報告書元素');
                    // 找該元素及其父元素內的連結
                    let container = el;
                    while (container && container.tagName !== 'BODY') {
                        const links = container.querySelectorAll('a[href]');
                        for (let link of links) {
                            const href = link.getAttribute('href') || '';
                            const linkText = link.textContent.trim();
                            if (href.includes('pdf') || linkText.includes('下載')) {
                                return {
                                    href: href,
                                    text: linkText,
                                    found: true
                                };
                            }
                        }
                        container = container.parentElement;
                    }
                }
            }

            // 方法 2：fallback - 找所有 PDF 連結
            const allLinks = document.querySelectorAll('a[href*="pdf"]');
            if (allLinks.length > 0) {
                return {
                    href: allLinks[0].getAttribute('href'),
                    text: allLinks[0].textContent.trim(),
                    found: true
                };
            }

            return { found: false, href: null, text: null };
        }
    ''')

    if result['found']:
        print(f"    ✓ 找到下載連結")
        print(f"    文字：{result['text']!r}")
        print(f"    URL：{result['href']!r}")
        return result['href']
    else:
        print(f"    ✗ 未找到下載連結")
        # 列出頁面上所有 <a> 標籤
        anchors = await page.query_selector_all('a[href]')
        print(f"    頁面上有 {len(anchors)} 個連結，前10個：")
        for i, a in enumerate(anchors[:10]):
            href = await a.get_attribute('href')
            text = (await a.inner_text()).strip()[:40]
            print(f"      [{i}] {text!r} -> {href[:60]}")
        return None


async def download_pdf(page, url, dest_dir, filename):
    """使用 expect_download 方式下載 PDF。"""
    os.makedirs(dest_dir, exist_ok=True)
    filepath = os.path.join(dest_dir, filename)

    try:
        # 方法 1：如果是直接 URL，用 requests 下載
        if url.startswith('http'):
            import requests
            print(f"    用 requests 下載：{url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            return filepath
    except Exception as e:
        print(f"    requests 下載失敗：{e}")

    # 方法 2：用 Playwright expect_download
    try:
        print(f"    嘗試用 Playwright expect_download...")
        async with page.expect_download() as dl_info:
            # 假設 url 是 href，點擊對應的連結
            found = await page.evaluate(f'''
                (href) => {{
                    const links = document.querySelectorAll('a[href]');
                    for (let link of links) {{
                        if (link.href === href) {{
                            link.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
            ''', url)

            if not found:
                print(f"    未找到對應的連結元素")
                return None

        download = await dl_info.value
        await download.save_as(filepath)
        return filepath
    except Exception as e:
        print(f"    Playwright 下載失敗：{e}")
        return None


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 60)
        print("【步驟 1】開啟查詢頁面")
        print("=" * 60)
        await page.goto(BASE_URL, timeout=30000)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        print(f"  ✓ 頁面載入完成")

        print("\n" + "=" * 60)
        print("【步驟 2】選取查詢條件")
        print("=" * 60)
        await select_dropdown(page, 0, "上市", "市場別")
        await select_dropdown(page, 1, "2024", "報告年度")
        await select_dropdown(page, 3, "3711 日月光投控", "公司代號")
        print("  ✓ 條件選取完成")

        print("\n" + "=" * 60)
        print("【步驟 3】點擊查詢")
        print("=" * 60)
        query_ok = await click_query_button(page)
        await page.screenshot(path="sc_query_result_fixed.png")
        print(f"  截圖：sc_query_result_fixed.png")

        print("\n" + "=" * 60)
        print("【步驟 4】展開並找到 PDF 下載連結")
        print("=" * 60)
        pdf_url = await expand_and_find_pdf(page)

        if pdf_url:
            print("\n" + "=" * 60)
            print("【步驟 5】下載 PDF")
            print("=" * 60)
            saved = await download_pdf(page, pdf_url, DOWNLOAD_DIR, "日月光投控_ESG_2024.pdf")
            if saved:
                abs_path = os.path.abspath(saved)
                size_kb = os.path.getsize(saved) // 1024
                print(f"  ✓ 下載成功")
                print(f"  存檔路徑：{abs_path}")
                print(f"  檔案大小：{size_kb} KB")
            else:
                print(f"  ✗ 下載失敗")
        else:
            print("\n  ✗ 未找到 PDF 下載連結，無法下載")

        print("\n" + "=" * 60)
        print("全部步驟完成，按 Enter 關閉瀏覽器...")
        input()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
