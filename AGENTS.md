# eSider ESG 專案開發筆記

## PDF 下載方式（TWSE ESG數位平台）

### 網址
https://esggenplus.twse.com.tw/inquiry/report?lang=zh-TW

### 重要規則
- 市場別、報告年度為**必填下拉選單**，不填查詢按鈕不會啟用
- 產業別可以不選（預設全選）
- 公司代號輸入後會出現 autocomplete，**必須點選下拉選項**才算確認
- 上市/上櫃公司都可以在此平台下載
- 未上市、國營事業（台電、台糖）無法在此平台下載

### Playwright 操作關鍵步驟
1. **市場別**：點開下拉後，用 `page.evaluate()` 找 `div` 文字精確匹配點選
   ```python
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
   ```
2. **報告年度**：同上，用 `evaluate` 點選 `"2024"`
3. **公司代號**：輸入代碼後等 1000ms，autocomplete 出現後點選第一個選項
4. **查詢**：等按鈕變藍（不是灰色 disabled）再點
5. **結果展開**：點選 `{code}-{公司名}` 展開詳細資訊
6. **下載**：點「下載 PDF」，用 `expect_download()` 攔截

### 下載腳本
- `download_p1_batch.py`：P1批次下載腳本（含跳過已下載邏輯）
- 存檔路徑：`data/reports/{公司名}/{公司名}_ESG_2024.pdf`
- 有效PDF大小：>1MB（小於1MB代表下載錯誤）

### 已知問題
- 台灣中油曾下載到行銷簡報而非永續報告書，下載後需確認檔案內容
- 矽品精密已下市，無法下載
- 未上市公司（新光人壽等）無法在此平台下載

### 公司擴充計畫
- 現有：30家（2024年完成）
- P1新增：19家（台灣50+公司治理100+高薪100三指數都上榜）
- 目標：100家
- 參考清單：`ESG_Company_Download_List.xlsx`
