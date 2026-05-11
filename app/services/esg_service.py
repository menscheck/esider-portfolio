from functools import lru_cache
import asyncio
import os
import shutil

from app.agents.esg_agent import ESGAgent
from app.models.schemas import QueryRequest, ESGAssessmentResult
from app.services.company_service import normalize_company
from app.services.query_pipeline import handle_query
from app.services.intent_classifier import classify_query
from app.services.intent_data_map import INTENT_DATA_MAP
from app.services.query_builder import build_vector_query
from app.services.metric_extractor import extract_metric
from app.services.company_resolver import resolve_company
from app.services.embedding_service import embed_text
from app.services.vector_service import search_similar_chunks
from app.services.report_fetcher import download_report
from app.services.pdf_ingestion_service import ingest_company_pdf


def vector_search(query: str, top_k: int = 5):
    query_embedding = embed_text(query)
    return search_similar_chunks(query_embedding, top_k=top_k)


def ingest_pdf(company_code: str, pdf_path: str):
    """
    Bridge function matching desired pipeline call shape.
    Stores/normalizes the fetched PDF then reuses existing ingestion flow.
    """
    os.makedirs("./report/2024", exist_ok=True)
    target_path = os.path.join("./report/2024", f"{company_code}.pdf")
    if pdf_path != target_path and os.path.exists(pdf_path):
        shutil.copyfile(pdf_path, target_path)
    ingest_company_pdf(company_code)


def handle_intent_pipeline_query(query: str, company_list):
    # 1 resolve company
    company_result = resolve_company(query, company_list)

    if not company_result.get("company"):
        return {"error": "company not found"}

    company = company_result["company"]

    # 2 classify
    cls = classify_query(query)
    intent = cls["intent"]

    # 3 mapping
    route = INTENT_DATA_MAP.get(intent)

    if not route:
        return {"error": "intent not supported"}

    # 4 build query
    vector_query = build_vector_query(query, company, intent, INTENT_DATA_MAP)

    # 5 vector search
    results = vector_search(vector_query, top_k=5)

    # If no vector hit, auto fetch report, ingest, and retry once.
    if not results:
        pdf_path = download_report(company.get("name", ""))
        if pdf_path:
            ingest_pdf(company["code"], pdf_path)
            results = vector_search(vector_query, top_k=5)

    context = "\n".join([r["text"] for r in results])

    # 6 extract
    metric = extract_metric(context)

    if metric.get("value") is None:
        return {
            "status": "not_found",
            "company": company,
            "intent": intent,
        }

    return {
        "company": company,
        "role": cls["role"],
        "pillar": cls["pillar"],
        "intent": intent,
        "metric": metric,
    }


class ESGService:
    def __init__(self, agent: ESGAgent) -> None:
        self._agent = agent

    async def process_query(self, payload: QueryRequest) -> ESGAssessmentResult:
        company = normalize_company(payload.company)

        result = await self._agent.run(
            company,
            payload.role,
            payload.topic
        )

        return result

    async def process_pipeline_query(self, query: str) -> dict:
        return await asyncio.to_thread(handle_query, query)

    async def process_intent_pipeline_query(self, query: str) -> dict:
        company_list = getattr(getattr(self, "_agent", None), "company_list", None)
        if not company_list:
            from app.services.company_service import get_company_service

            company_list = get_company_service().company_list
        return await asyncio.to_thread(handle_intent_pipeline_query, query, company_list)


@lru_cache
def get_esg_service() -> ESGService:
    return ESGService(agent=ESGAgent())
