from app.services.company_service import CompanyService

print("🔥 RUNNING TEST FILE")

cs = CompanyService()

print("🔥 LENGTH:", len(cs.company_list))
