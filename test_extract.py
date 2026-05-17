from app.services.company_service import CompanyService

print("🚀 測試 extract_company")

cs = CompanyService()

tests = [
    "台積電的股價如何？",
    "2330 表現不錯",
    "鴻海精密工業股份有限公司",
    "聯發科 mediatek",
    "宏碁 acer 電腦",
    "台達電 delta 電子",
    "隨便說說公司"
]

for t in tests:
    print(f"\n🔍 輸入: {t}")
    result = cs.extract_company(t)

    if result:
        print(f"✅ 辨識: {result['code']} | {result['name']}")
    else:
        print("❌ 無辨識結果")
