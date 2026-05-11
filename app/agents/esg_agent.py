import asyncio
from typing import Dict, Any, List

from app.services.embedding_service import embed_text
from app.services.vector_service import search_similar_chunks
from app.services.pdf_ingestion_service import ingest_company_pdf
from app.services.scoring_service import llm_score
from app.services.llm_service import generate_esg_summary
from app.services.twse_service import get_twse_esg_data

class ESGAgent:
    async def run(self, company: str, role: str, topic: str):

        query_emb = await asyncio.to_thread(embed_text, f"{company} {topic}")

        results = await asyncio.to_thread(search_similar_chunks, query_emb, 5)

        if not results:
            print("📥 Auto ingestion trigger")
            await asyncio.to_thread(ingest_company_pdf, company)
            results = await asyncio.to_thread(search_similar_chunks, query_emb, 5)

        context = "\n\n".join([r["text"] for r in results])

        prompt = f"""
You are an ESG analyst.

Company: {company}
Role: {role}
Focus: {topic}

Context:
{context[:4000]}

Please provide:
1. Key ESG insights
2. Risks
3. Opportunities
4. Short summary
"""
        
        summary = await asyncio.to_thread(
            generate_esg_summary,
            {"prompt": prompt}
        )

        scores = await asyncio.to_thread(llm_score, context)
        
        # -------------------------
        # Step6: fetch TWSE data (keep existing behavior)
        # -------------------------
        print("🔍 Step6: fetch TWSE data")
        try:
            twse_data = await asyncio.to_thread(
                get_twse_esg_data,
                company
            )
        except Exception as e:
            print("⚠️ TWSE error:", e)
            twse_data = {}

        overall_score = (scores["E"]["score"] + scores["S"]["score"] + scores["G"]["score"]) / 3

        return {
            "company_name": company,
            "overall_score": round(overall_score, 2),
            "esg_scores": [
                {"pillar": "E", "score": scores["E"]["score"], "justification": scores["E"]["reason"]},
                {"pillar": "S", "score": scores["S"]["score"], "justification": scores["S"]["reason"]},
                {"pillar": "G", "score": scores["G"]["score"], "justification": scores["G"]["reason"]},
            ],
            "summary": summary,
            "context_used": [r["text"][:200] for r in results],
            "source_data": twse_data
        }
