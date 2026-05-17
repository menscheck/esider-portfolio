from app.services.company_service import CompanyService

print("🚀 測試模糊搜尋")

cs = CompanyService()

tests = [
    "台",
    "台積",
    "2330",
    "宏",
    "acer",
    "聯發",
    "2317"
]

for t in tests:
    print(f"\n🔍 查詢: {t}")
    results = cs.search(t)

    if not results:
        print("❌ 無結果")
        continue

    for r in results:
        print(f"- {r['code']} | {r['name']}")
