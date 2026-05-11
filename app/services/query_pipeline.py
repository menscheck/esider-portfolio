from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.company_service import get_company_service
from app.services.intent_classifier import classify_intent, classify_pillar, classify_role


def route_data(intent: str, company: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map intent to data source and target sections."""
    mapping: Dict[str, Dict[str, Any]] = {
        "salary": {
            "source": "sustainability_report",
            "sections": ["員工薪酬", "人才"],
        },
        "workforce_compensation": {
            "source": "sustainability_report",
            "sections": ["員工薪酬", "人才吸引與留任"],
        },
        "turnover": {
            "source": "sustainability_report",
            "sections": ["人才"],
        },
        "workforce_turnover": {
            "source": "sustainability_report",
            "sections": ["人才吸引與留任"],
        },
        "harassment": {
            "source": "sustainability_report",
            "sections": ["人權", "DEI"],
        },
        "harassment_ethics": {
            "source": "sustainability_report",
            "sections": ["人權管理", "DEI"],
        },
        "grievance_mechanism": {
            "source": "sustainability_report",
            "sections": ["人權管理"],
        },
        "shareholding": {
            "source": "annual_report",
            "sections": ["股權結構"],
        },
        "executive_shareholding": {
            "source": "annual_report",
            "sections": ["股權結構", "公司治理"],
        },
        "training": {
            "source": "sustainability_report",
            "sections": ["人才發展"],
        },
        "training_development": {
            "source": "sustainability_report",
            "sections": ["人才培育與職涯發展"],
        },
        "ghg_emissions": {
            "source": "sustainability_report",
            "sections": ["氣候變遷與溫室氣體"],
        },
        "climate": {
            "source": "sustainability_report",
            "sections": ["氣候變遷與溫室氣體", "氣候風險"],
        },
        "risk_management": {
            "source": "sustainability_report",
            "sections": ["風險管理"],
        },
        "governance": {
            "source": "annual_report",
            "sections": ["公司治理"],
        },
        "financial": {
            "source": "annual_report",
            "sections": ["財務摘要", "財務風險"],
        },
        "energy": {
            "source": "sustainability_report",
            "sections": ["能源管理"],
        },
        "water": {
            "source": "sustainability_report",
            "sections": ["水資源"],
        },
    }
    return mapping.get(intent)


def retrieve_data(company: Dict[str, Any], route: Dict[str, Any]) -> Dict[str, Any]:
    """
    Data retrieval placeholder.
    Hook this into your real report parser / vector search / APIs.
    """
    return {
        "company_code": company.get("code"),
        "company_name": company.get("name"),
        "source": route.get("source"),
        "sections": route.get("sections", []),
        "records": [],
    }


def extract_answer(query: str, data: Dict[str, Any]) -> str:
    """
    Answer generation placeholder.
    Hook this into your RAG summarizer / LLM answer generator.
    """
    sections = ", ".join(data.get("sections", []))
    source = data.get("source", "unknown")
    company_name = data.get("company_name", "unknown")
    return (
        f"已定位 {company_name} 的資料來源為 {source}，"
        f"將優先檢索章節：{sections}。"
    )


def structured_output(
    company: Dict[str, Any],
    role: str,
    pillar: str,
    intent: str,
    route: Dict[str, Any],
    answer: str,
) -> Dict[str, Any]:
    return {
        "company": company,
        "role": role,
        "pillar": pillar,
        "intent": intent,
        "route": route,
        "answer": answer,
    }


def handle_query(query: str) -> Dict[str, Any]:
    company = get_company_service().extract_company(query)
    if not company:
        return {"error": "company not found"}

    role = classify_role(query)
    pillar = classify_pillar(query, role)
    intent = classify_intent(query, role, pillar)

    route = route_data(intent, company)
    if not route:
        return {"error": "intent not supported"}

    data = retrieve_data(company, route)
    answer = extract_answer(query, data)

    return structured_output(
        company=company,
        role=role,
        pillar=pillar,
        intent=intent,
        route=route,
        answer=answer,
    )

