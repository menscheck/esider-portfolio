"""
app/core/pipeline.py
完整查詢 Pipeline：query + persona → answer

資料流設計：
- ESG chunks：四個角色都會查，永遠執行
- FinMind 財務數據：散戶/機構投資人額外補充，不取代 ESG
- 大盤查詢（無公司）：散戶/機構偵測到大盤關鍵字時補充市場摘要
- Out-of-scope：天氣/娛樂/排行榜等直接攔截
"""

import os
import logging
from openai import AzureOpenAI

from app.core.tag_parser import parse_tags
from app.core.company_resolver import resolve_company, resolve_companies_from_query
from app.core.retriever import ESGRetriever
from app.core.reranker import rerank
from app.core.persona_router import Persona, route
from app.core.text_postprocess import fix_source_annotation
from app.core.intent_detector import detect_intent

logger = logging.getLogger(__name__)

from app.core.config import get_config


def _get_azure_config():
    cfg = get_config()["azure_openai"]
    return {
        "endpoint": cfg["endpoint"],
        "api_key": cfg["api_key"],
        "deployment": cfg["deployment"],
        "api_version": cfg["api_version"],
    }


# 單例 retriever
_retriever: ESGRetriever | None = None


def get_retriever() -> ESGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = ESGRetriever()
    return _retriever


# ── Out-of-scope 攔截關鍵字 ────────────────────────────────────────────────────
_OOS_KEYWORDS = [
    # 天氣氣象
    "天氣", "氣象", "颱風", "下雨", "降雨", "溫度", "幾度", "會下雨",
    "紫外線", "空氣品質", "AQI", "PM2.5", "地震",
    # 股市即時排行（非個股查詢）
    "股王", "股后", "漲幅排行", "跌幅排行", "今日漲停", "今日跌停",
    "漲停板", "跌停板", "熱門股", "飆股",
    # 新聞 / 娛樂 / 雜項
    "新聞", "頭條", "今天發生", "八卦", "美食", "餐廳", "電影",
    "球賽", "比賽結果", "今彩", "樂透", "星座", "運勢",
]

# FinMind 支援的角色
_FINMIND_PERSONAS = {Persona.RETAIL_INVESTOR, Persona.INSTITUTIONAL_INVESTOR}

# 機構投資人額外財務關鍵字
_INSTITUTIONAL_EXTRA_KEYWORDS = [
    "ROE", "ROA", "ROIC", "毛利率", "淨利率", "營業利益",
    "自由現金流", "FCF", "資本支出", "CAPEX",
    "負債", "資產", "財務結構", "EPS", "獲利",
]


def _is_out_of_scope(user_query: str) -> bool:
    for kw in _OOS_KEYWORDS:
        if kw in user_query:
            return True
    return False


def _get_finmind_functions():
    """根據環境變數決定使用 v1 或 v2 FinMind client"""
    use_v2 = os.getenv("FINMIND_USE_MONGO_CACHE", "0") == "1"
    if use_v2:
        from app.core.finmind_client_v2 import (
            get_financial_summary,
            detect_financial_intent,
            get_market_index_summary,
            detect_market_intent,
        )
    else:
        from app.core.finmind_client import (
            get_financial_summary,
            detect_financial_intent,
            get_market_index_summary,
            detect_market_intent,
        )
    return get_financial_summary, detect_financial_intent, get_market_index_summary, detect_market_intent


def query(
    user_query: str,
    persona: Persona,
    company: str | None = None,
    top_k: int = 5,
    intent: str | None = None,
) -> dict:
    """
    完整查詢流程

    Returns:
        {
            "answer": str,
            "chunks": list[dict],
            "tags": list[str],
            "persona": str,
            "company": str | None,
            "out_of_scope": bool  # 僅 OOS 時存在
        }
    """
    # ── Step 0: Out-of-scope 攔截 ──────────────────────────────────────────────
    if _is_out_of_scope(user_query):
        return {
            "answer": (
                "抱歉，這個問題超出我的資料範圍 😅\n"
                "我專注於台灣上市櫃公司的 ESG 永續報告書內容，"
                "以及個股的財務數據查詢（散戶/機構角色）。\n"
                "你可以問我公司的環境績效、勞工政策、治理結構，"
                "或是指定公司的營收、EPS、配息等財務指標喔！"
            ),
            "chunks": [],
            "tags": [],
            "persona": persona.value,
            "company": None,
            "out_of_scope": True,
        }

    # ── Step 1: Tag parsing ────────────────────────────────────────────────────
    matched_tags = parse_tags(user_query)
    logger.info(f"matched_tags={matched_tags}")

    # ── Step 2: Company resolution ─────────────────────────────────────────────
    retriever = get_retriever()
    resolved_company = None
    if company:
        resolved_company = resolve_company(company)
    if not resolved_company:
        detected = resolve_companies_from_query(user_query)
        resolved_company = detected[0] if detected else None

    logger.warning(f"DEBUG pipeline: persona={persona.value}, company={resolved_company}")

    # ── 先判斷 query_intent，後續 Step 3/4 都需要 ────────────────────────────
    query_intent = intent if intent else detect_intent(user_query)
    if intent == "esg":
        detected_intent = detect_intent(user_query)
        if detected_intent == "finmind":
            query_intent = "finmind"
            logger.warning(f"[intent] 外部傳入 esg 但問題偵測為 finmind，以 finmind 為準")
    if query_intent == "ambiguous":
        query_intent = intent if intent and intent != "ambiguous" else "esg"
    logger.warning(f"[intent] 最終 query_intent={query_intent}")

    if query_intent == "oos":
        return {
            "answer": "我是 eSider ESG 永續洞察助理，這個問題超出我的服務範圍。",
            "chunks": [],
            "tags": [],
            "persona": persona.value,
            "company": None,
        }

    # ── Step 3: ESG 檢索 ────────────────────────────────────────────────────────
    # finmind + 無公司 = 純大盤查詢，不需要 ESG chunks
    skip_esg = (query_intent == "finmind" and not resolved_company and persona in _FINMIND_PERSONAS)

    if skip_esg:
        chunks = []
        logger.warning(f"[pipeline] finmind+無公司，跳過 ESG 檢索")
    else:
        chunks = retriever.search(user_query, company=resolved_company, top_k=top_k * 3)
        logger.info(f"retrieved {len(chunks)} candidate chunks for company={resolved_company}")

        if chunks:
            chunks = rerank(user_query, chunks, top_k=top_k)
            logger.info(f"reranked to {len(chunks)} chunks")

        # 鎖定公司沒資料 → fallback 全域搜尋
        if not chunks:
            chunks = retriever.search(user_query, company=None, top_k=top_k * 3)
            if chunks:
                chunks = rerank(user_query, chunks, top_k=top_k)
            logger.info(f"fallback global retrieval: {len(chunks)} chunks")

    # ── Step 4: FinMind 財務補充（僅散戶/機構）───────────────────────────────
    financial_context = ""

    if persona in _FINMIND_PERSONAS:
        logger.warning(f"[FinMind] Step4 開始, persona={persona.value}, intent={query_intent}, company={resolved_company}")
        try:
            get_financial_summary, _, get_market_index_summary, detect_market_intent = _get_finmind_functions()
            from app.core.company_resolver import get_company_info

            if query_intent == "finmind":
                logger.warning(f"[FinMind] intent=finmind 確認")

                # (A) 大盤/市場總覽（無公司 → force 查最新指數）
                if not resolved_company:
                    logger.warning(f"[FinMind] 無公司，查大盤")
                    market_ctx = get_market_index_summary(user_query, force=True)
                    logger.warning(f"[FinMind] get_market_index_summary 回傳長度={len(market_ctx) if market_ctx else 0}")
                    if market_ctx:
                        financial_context = market_ctx

                # (B) 個股財務數據（有公司）
                else:
                    info = get_company_info(resolved_company)
                    stock_id = info.get("stock_id") if info else None
                    logger.warning(f"[FinMind] 查個股 company={resolved_company}, stock_id={stock_id}")

                    if stock_id:
                        augmented_query = user_query
                        if persona == Persona.INSTITUTIONAL_INVESTOR:
                            augmented_query = user_query + " " + " ".join(_INSTITUTIONAL_EXTRA_KEYWORDS)

                        fin_ctx = get_financial_summary(stock_id, augmented_query)
                        logger.warning(f"[FinMind] get_financial_summary 回傳長度={len(fin_ctx) if fin_ctx else 0}")
                        if fin_ctx:
                            financial_context = (
                                fin_ctx if not financial_context
                                else financial_context + "\n\n" + fin_ctx
                            )
            else:
                logger.warning(f"[FinMind] intent={query_intent}，跳過FinMind查詢")

        except Exception:
            logger.exception("[FinMind] 取得財務數據失敗，忽略並繼續流程")

    # ── Step 5: 組 prompt 並呼叫 LLM ──────────────────────────────────────────
    prompts = route(user_query, persona, chunks, matched_tags, financial_context,
                    intent=query_intent if persona in _FINMIND_PERSONAS else "esg")

    az = _get_azure_config()
    client = AzureOpenAI(
        azure_endpoint=az["endpoint"],
        api_key=az["api_key"],
        api_version=az["api_version"],
    )
    response = client.chat.completions.create(
        model=az["deployment"],
        messages=[
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ],
        max_tokens=1024,
        temperature=0.3,
    )

    answer = fix_source_annotation(response.choices[0].message.content)

    return {
        "answer": answer,
        "chunks": chunks,
        "tags": matched_tags,
        "persona": persona.value,
        "company": resolved_company,
    }
