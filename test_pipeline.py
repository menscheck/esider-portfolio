import os
import sys
sys.path.insert(0, ".")

from app.core.pipeline import query
from app.core.persona_router import Persona

tests = [
    ("台積電碳排放目標是什麼", Persona.INSTITUTIONAL_INVESTOR, "台積電"),
    ("這家公司員工福利好嗎", Persona.JOB_SEEKER, "中信金控"),
    ("鴻海供應鏈ESG風險管控如何", Persona.ESG_PRACTITIONER, "鴻海"),
]

for q, persona, company in tests:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"Persona: {persona.value} | 公司: {company}")
    print(f"{'='*60}")
    result = query(q, persona=persona, company=company)
    print(f"Tags: {result['tags']}")
    print(f"Answer:\n{result['answer']}")


# ---- debug: resolve + retriever pipeline ----
# 目標：確認公司解析與檢索 chunks 的解析流程
from app.core.company_resolver import resolve_company
from app.core.retriever import ESGRetriever

r = ESGRetriever()

for raw in ["中信金控", "鴻海"]:
    resolved = resolve_company(raw)
    print(f'input={raw} -> resolved={resolved}')
    chunks = r.search("供應鏈ESG", company=resolved, top_k=3)
    print(f"  chunks returned: {len(chunks)}")
    for c in chunks:
        print(f'  - {c["company"]} p{c["page"]} score={c["score"]:.4f}')
