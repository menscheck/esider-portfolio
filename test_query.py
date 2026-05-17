from app.services.company_service import CompanyService

queries = [
    "萬海航運的減碳策略",
    "統一企業的薪酬福利",
    "正隆紙業的水資源管理政策"
]

cs = CompanyService()

for query in queries:
    print("=" * 30)
    print("Query:", query)

    company = cs.extract_company(query)

    if not company:
        print("No company found.")
    else:
        print("Company:", company)