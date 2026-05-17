import pandas as pd

# =========================
# 台灣上市公司
# =========================
listed_url = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"

# =========================
# 台灣上櫃公司
# =========================
otc_url = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"

print("下載上市公司資料...")
listed_df = pd.read_csv(listed_url)

print("下載上櫃公司資料...")
otc_df = pd.read_csv(otc_url)

# 保留欄位
listed_df = listed_df[["公司代號", "公司名稱"]]
otc_df = otc_df[["公司代號", "公司名稱"]]

# 增加市場別
listed_df["市場別"] = "上市"
otc_df["市場別"] = "上櫃"

# 合併
df = pd.concat([listed_df, otc_df], ignore_index=True)

# 排序
df["公司代號"] = df["公司代號"].astype(str)
df = df.sort_values("公司代號")

# 輸出 Excel
output_file = "tw_all_listed_otc_companies.xlsx"

df.to_excel(output_file, index=False)

print("=" * 50)
print(f"完成輸出: {output_file}")
print(f"總公司數: {len(df)}")
print("=" * 50)

print(df.head())
