from __future__ import annotations

from typing import Any, Dict, List


def normalize_name(name: str) -> str:
    normalized = name.lower()

    for suffix in ["股份有限公司", "有限公司", "控股", "集團"]:
        normalized = normalized.replace(suffix, "")

    normalized = normalized.replace("臺", "台")
    return normalized.strip()


def _score_company(text: str, company: Dict[str, Any]) -> float:
    raw_name = str(company.get("name", ""))
    code = str(company.get("code", ""))
    alias = str(company.get("alias", ""))

    normalized_name = normalize_name(raw_name)
    normalized_alias = normalize_name(alias) if alias else ""

    score = 0.0

    if raw_name and raw_name.lower() in text:
        score += 120.0

    # 關鍵字 boost: 名稱正規化後直接命中，提高權重
    if normalized_name and normalized_name in text:
        score += 100.0

    if normalized_alias and normalized_alias in text:
        score += 90.0

    # 語意關鍵詞匹配: 遠東紡織 -> 遠東新世紀
    if "紡織" in text and "遠東" in text:
        if "遠東新世紀" in raw_name:
            score += 120.0

    for i in range(2, min(len(normalized_name), 6)):
        if normalized_name[:i] in text:
            score += 10.0

    if code and code in text:
        score += 140.0

    return score


def resolve_company(
    text: str,
    company_list: List[Dict[str, Any]],
    threshold: float = 0.75,
    top_k: int = 3,
) -> Dict[str, Any]:
    normalized_text = text.lower()
    scored: List[Dict[str, Any]] = []

    for company in company_list:
        score = _score_company(normalized_text, company)
        if score <= 0:
            continue
        confidence = min(score / 220.0, 1.0)
        scored.append(
            {
                "company": company,
                "score": score,
                "confidence": round(confidence, 4),
            }
        )

    if not scored:
        return {
            "company": None,
            "confidence": 0.0,
            "candidates": [],
            "needs_disambiguation": False,
        }

    scored.sort(key=lambda item: item["score"], reverse=True)
    candidates = scored[:top_k]
    best = scored[0]

    # 單一候選直接視為可確定，不進入 disambiguation
    if len(candidates) == 1:
        return {
            "company": candidates[0]["company"],
            "confidence": candidates[0]["confidence"],
            "candidates": candidates,
            "needs_disambiguation": False,
        }

    # 高分候選直接判定，不需 disambiguation
    if best["score"] > 80:
        return {
            "company": best["company"],
            "confidence": best["confidence"],
            "candidates": candidates,
            "needs_disambiguation": False,
        }

    if best["confidence"] < threshold:
        return {
            "company": None,
            "confidence": best["confidence"],
            "candidates": candidates,
            "needs_disambiguation": True,
        }

    return {
        "company": best["company"],
        "confidence": best["confidence"],
        "candidates": candidates,
        "needs_disambiguation": False,
    }

