from typing import Dict


def calculate_esg_score(summary: str) -> Dict:
    """
    Simple ESG scoring based on keyword heuristics.
    This is a V3 baseline version (rule-based, later可升級成AI scoring)
    """

    summary_lower = summary.lower()

    # --- Environmental (E) ---
    e_score = 50
    if any(k in summary_lower for k in ["carbon", "emission", "climate", "energy", "water"]):
        e_score += 10
    if any(k in summary_lower for k in ["risk", "scarcity", "transition"]):
        e_score -= 5

    # --- Social (S) ---
    s_score = 50
    if any(k in summary_lower for k in ["employee", "human rights", "safety", "diversity"]):
        s_score += 10
    if any(k in summary_lower for k in ["incident", "injury", "violation"]):
        s_score -= 5

    # --- Governance (G) ---
    g_score = 50
    if any(k in summary_lower for k in ["board", "governance", "compliance", "ethics"]):
        g_score += 10
    if any(k in summary_lower for k in ["lack", "missing", "no disclosure"]):
        g_score -= 10

    # clamp score between 0–100
    e_score = max(0, min(100, e_score))
    s_score = max(0, min(100, s_score))
    g_score = max(0, min(100, g_score))

    overall = round((e_score + s_score + g_score) / 3, 2)

    return {
        "E": e_score,
        "S": s_score,
        "G": g_score,
        "overall": overall
    }