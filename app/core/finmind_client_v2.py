"""
FinMind client v2
- Uses MongoDB-backed cache (app/core/finmind_mongo_cache.py)
- Does NOT modify existing app/core/finmind_client.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import requests

from app.core.config import get_config
from app.core.finmind_mongo_cache import CacheKey as MongoCacheKey
from app.core.finmind_mongo_cache import ensure_indexes as mongo_ensure_indexes
from app.core.finmind_mongo_cache import get_cached as mongo_get_cached
from app.core.finmind_mongo_cache import save_cached as mongo_save_cached

logger = logging.getLogger(__name__)

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

FINANCIAL_KEYWORDS: dict[str, str] = {
    "營收": "TaiwanStockMonthRevenue",
    "月營收": "TaiwanStockMonthRevenue",
    "業績": "TaiwanStockMonthRevenue",
    "EPS": "TaiwanStockFinancialStatements",
    "獲利": "TaiwanStockFinancialStatements",
    "賺多少": "TaiwanStockFinancialStatements",
    "損益": "TaiwanStockFinancialStatements",
    "淨利": "TaiwanStockFinancialStatements",
    "稅前": "TaiwanStockFinancialStatements",
    "稅後": "TaiwanStockFinancialStatements",
    "盈餘": "TaiwanStockFinancialStatements",
    "虧損": "TaiwanStockFinancialStatements",
    "獲利能力": "TaiwanStockFinancialStatements",
    "配息": "TaiwanStockDividend",
    "股利": "TaiwanStockDividend",
    "除息": "TaiwanStockDividend",
    "除權": "TaiwanStockDividend",
    "發放": "TaiwanStockDividend",
    "配多少": "TaiwanStockDividend",
    "法人": "TaiwanStockInstitutionalInvestorsBuySell",
    "外資": "TaiwanStockInstitutionalInvestorsBuySell",
    "三大法人": "TaiwanStockInstitutionalInvestorsBuySell",
    "投信": "TaiwanStockInstitutionalInvestorsBuySell",
    "自營商": "TaiwanStockInstitutionalInvestorsBuySell",
    "買超": "TaiwanStockInstitutionalInvestorsBuySell",
    "賣超": "TaiwanStockInstitutionalInvestorsBuySell",
    "本益比": "TaiwanStockPER",
    "殖利率": "TaiwanStockPER",
    "PBR": "TaiwanStockPER",
    "便宜": "TaiwanStockPER",
    "貴不貴": "TaiwanStockPER",
    "股價": "TaiwanStockPrice",
    "漲跌": "TaiwanStockPrice",
    "K線": "TaiwanStockPrice",
    "月K": "TaiwanStockPrice",
    "週K": "TaiwanStockPrice",
    "日K": "TaiwanStockPrice",
    "走勢": "TaiwanStockPrice",
    "高點": "TaiwanStockPrice",
    "低點": "TaiwanStockPrice",
    "均線": "TaiwanStockPrice",
    "MA": "TaiwanStockPrice",
    "抱股": "TaiwanStockPrice",
    "持股": "TaiwanStockPrice",
    "賣出": "TaiwanStockPrice",
    "買進": "TaiwanStockPrice",
    "再出": "TaiwanStockPrice",
    "漲停": "TaiwanStockPrice",
    "跌停": "TaiwanStockPrice",
    "波動": "TaiwanStockPrice",
    "區間": "TaiwanStockPrice",
    "反彈": "TaiwanStockPrice",
    "突破": "TaiwanStockPrice",
    "整理": "TaiwanStockPrice",
    "支撐": "TaiwanStockPrice",
    "壓力": "TaiwanStockPrice",
    "負債": "TaiwanStockBalanceSheet",
    "資產": "TaiwanStockBalanceSheet",
    "財務結構": "TaiwanStockBalanceSheet",
    "負債比": "TaiwanStockBalanceSheet",
    "ROE": "TaiwanStockFinancialStatements",
    "ROA": "TaiwanStockFinancialStatements",
    "ROIC": "TaiwanStockFinancialStatements",
    "毛利率": "TaiwanStockFinancialStatements",
    "淨利率": "TaiwanStockFinancialStatements",
    "營業利益": "TaiwanStockFinancialStatements",
    "自由現金流": "TaiwanStockBalanceSheet",
    "FCF": "TaiwanStockBalanceSheet",
    "資本支出": "TaiwanStockBalanceSheet",
    "CAPEX": "TaiwanStockBalanceSheet",
}

DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_INDEX_DATA_ID = "TAIEX"
DEFAULT_INDEX_DATASET = "TaiwanStockTotalReturnIndex"

_FINMIND_PERSONAS = {
    "散戶投資人",
    "機構投資人",
}


def detect_financial_intent(query: str) -> list[str]:
    datasets: set[str] = set()
    for kw, dataset in FINANCIAL_KEYWORDS.items():
        if kw in query:
            datasets.add(dataset)
    return list(datasets)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def fetch_financial_data(
    stock_id: str,
    dataset: str,
    start_date: str | None = None,
    end_date: str | None = None,
    *,
    cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS,
) -> list[dict[str, Any]]:
    """
    Fetch dataset from FinMind, cache via Mongo.
    """
    # cache read
    try:
        mongo_ensure_indexes()
        cached = mongo_get_cached(MongoCacheKey(stock_id=stock_id, dataset=dataset), ttl_hours=cache_ttl_hours)
        if cached is not None:
            return cached
    except Exception:
        # if mongo fails, ignore and proceed to fetch from API
        logger.exception("[FinMind v2] cache read failed; fallback to API")

    cfg = get_config()
    finmind_cfg = cfg["finmind"]
    token = finmind_cfg.get("token")
    if not token:
        logger.error("FinMind token not found in config.ini [finmind].token")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now()
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")
    if not start_date:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")

    params: dict[str, Any] = {
        "dataset": dataset,
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        resp = requests.get(FINMIND_URL, headers=headers, params=params, timeout=10)
        payload: dict[str, Any] = resp.json()

        if payload.get("status") == 200:
            data = payload.get("data", [])
            typed: list[dict[str, Any]] = [d for d in data if isinstance(d, dict)]
            try:
                mongo_save_cached(MongoCacheKey(stock_id=stock_id, dataset=dataset), typed)
            except Exception:
                logger.exception("[FinMind v2] cache write failed; continue")
            return typed

        logger.error("[FinMind v2 API error] %s", payload)
        return []
    except Exception:
        logger.exception("[FinMind v2 error] dataset=%s stock_id=%s", dataset, stock_id)
        return []


def get_financial_summary(stock_id: str, query: str) -> str:
    datasets = detect_financial_intent(query)
    if not datasets:
        return ""

    summaries: list[str] = []
    for dataset in datasets:
        data = fetch_financial_data(stock_id, dataset)
        if not data:
            continue

        recent = data[-5:]

        if dataset == "TaiwanStockMonthRevenue":
            lines = ["【月營收】"]
            for d in recent[-3:]:
                rev = d.get("revenue", 0)
                year = d.get("revenue_year", "")
                month = d.get("revenue_month", 0)
                try:
                    month_int = int(month)
                except Exception:
                    month_int = 0
                lines.append(f"  {year}/{month_int:02d} 營收：{(rev / 1e8):.1f}億元")
            summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockFinancialStatements":
            eps_data = [d for d in recent if d.get("type") == "EPS"]
            if eps_data:
                lines = ["【EPS】"]
                for d in eps_data[-3:]:
                    lines.append(f"  {d.get('date', '')} EPS：{d.get('value', 'N/A')}元")
                summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockDividend":
            lines = ["【股利政策】"]
            for d in recent[-3:]:
                cash = d.get("CashEarningsDistribution", 0)
                date_str = str(d.get("date", ""))
                lines.append(f"  {date_str[:4]} 現金股利：{cash}元")
            summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockInstitutionalInvestorsBuySell":
            lines = ["【三大法人（最近）】"]
            for d in recent[-2:]:
                buy = d.get("buy", 0) or 0
                sell = d.get("sell", 0) or 0
                net = buy - sell
                sign = "買超" if net > 0 else "賣超"
                lines.append(f"  {d.get('date', '')} {d.get('name', '')} {sign} {abs(net) // 1000}張")
            summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockPER":
            if recent:
                d = recent[-1]
                lines = ["【估值】"]
                lines.append(f"  本益比(PER)：{d.get('PER', 'N/A')}x")
                lines.append(f"  股價淨值比(PBR)：{d.get('PBR', 'N/A')}x")
                lines.append(f"  殖利率：{d.get('dividend_yield', 'N/A')}%")
                summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockPrice":
            if recent:
                d = recent[-1]
                prices = [r.get("close", 0) for r in recent if r.get("close")]
                high = max(prices) if prices else "N/A"
                low = min(prices) if prices else "N/A"

                lines = ["【股價走勢（近5日）】"]
                lines.append(f"  最新收盤：{d.get('close','N/A')}元")
                lines.append(f"  近期高點：{high}元 / 低點：{low}元")
                lines.append(f"  成交量：{d.get('Trading_Volume','N/A')}張")
                summaries.append("\n".join(lines))

    return "\n\n".join(summaries) if summaries else ""


def detect_market_intent(query: str) -> list[str]:
    patterns = [
        "大盤",
        "台股總覽",
        "台股",
        "加權",
        "加權指數",
        "指數",
        "市場",
        "整體市場",
        "盤勢",
    ]
    return [p for p in patterns if p in query]


def detect_compare_windows(query: str) -> dict[str, bool]:
    q = query.replace(" ", "")
    return {
        "DOD": any(x in q for x in ["DOD", "日對日", "昨日", "前一日", "當日比昨日", "與昨天"]),
        "WOW": any(x in q for x in ["WOW", "週對週", "上週", "近一週", "一週"]),
        "MOM": any(x in q for x in ["MOM", "月對月", "上月", "近一個月", "本月比上月"]),
        "SOS": any(x in q for x in ["SOS", "半年對半年", "上半年", "近半年", "半年度"]),
        "YOY": any(x in q for x in ["YOY", "年對年", "去年", "近一年", "一年內"]),
    }


def _pick_latest_points(points: list[dict[str, Any]], key: str, n: int) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> Any:
        return item.get("date") or item.get(key) or ""

    ordered = sorted(points, key=sort_key)
    if not ordered:
        return []
    return ordered[-n:]


def _pct_change(latest: float, base: float) -> float | None:
    if base == 0:
        return None
    return (latest - base) / base * 100.0


def _format_index_summary(latest: dict[str, Any], prev: dict[str, Any] | None, window_name: str, pct: float | None) -> str:
    date_str = str(latest.get("date", ""))
    latest_price = _safe_float(latest.get("price"))
    base_price = _safe_float(prev.get("price")) if prev else None
    if latest_price is None or base_price is None or pct is None:
        return f"{window_name}：資料不足（{date_str}）"
    return f"{window_name}：{date_str} {latest_price:.2f}（較前值 {base_price:.2f}：{pct:+.2f}%）"


def get_market_index_summary(
    query: str,
    *,
    index_data_id: str = DEFAULT_INDEX_DATA_ID,
    index_dataset: str = DEFAULT_INDEX_DATASET,
    today: datetime | None = None,
) -> str:
    windows = detect_compare_windows(query)
    if not any(windows.values()) and not detect_market_intent(query):
        return ""

    now = today or datetime.now()
    start_date = (now - timedelta(days=370)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    points = fetch_financial_data(
        stock_id=index_data_id,
        dataset=index_dataset,
        start_date=start_date,
        end_date=end_date,
    )
    if not points:
        return ""

    recent = _pick_latest_points(points, key="price", n=120)
    if not recent:
        return ""

    latest = recent[-1]
    offsets = {"DOD": 1, "WOW": 5, "MOM": 20, "SOS": 100}

    yoy_target = (now - timedelta(days=365)).strftime("%Y-%m-%d")

    def _closest_point(target_date: str) -> dict[str, Any] | None:
        best: dict[str, Any] | None = None
        best_dist: int | None = None
        for p in recent:
            d = str(p.get("date", ""))
            if not d:
                continue
            try:
                dd = datetime.strptime(d, "%Y-%m-%d")
                tt = datetime.strptime(target_date, "%Y-%m-%d")
                dist = abs((dd - tt).days)
            except Exception:
                continue
            if best is None or (best_dist is not None and dist < best_dist):
                best = p
                best_dist = dist
        return best

    summaries: list[str] = [f"【台股指數({index_data_id})】"]

    for window_name, enabled in windows.items():
        if not enabled:
            continue

        if window_name == "YOY":
            base = _closest_point(yoy_target)
            if not base:
                summaries.append(_format_index_summary(latest, None, window_name, None))
                continue

            latest_price = _safe_float(latest.get("price"))
            base_price = _safe_float(base.get("price"))
            pct = _pct_change(latest_price or 0.0, base_price or 0.0) if latest_price is not None and base_price is not None else None
            summaries.append(_format_index_summary(latest, base, window_name, pct))
            continue

        offset = offsets.get(window_name)
        if not offset or len(recent) <= offset:
            summaries.append(_format_index_summary(latest, None, window_name, None))
            continue

        base = recent[-1 - offset]
        latest_price = _safe_float(latest.get("price"))
        base_price = _safe_float(base.get("price"))
        pct = _pct_change(latest_price or 0.0, base_price or 0.0) if latest_price is not None and base_price is not None else None
        summaries.append(_format_index_summary(latest, base, window_name, pct))

    if len(summaries) == 1:
        latest_price = _safe_float(latest.get("price"))
        date_str = str(latest.get("date", ""))
        if latest_price is not None:
            summaries.append(f"最新：{date_str} 指數 {latest_price:.2f}")

    return "\n".join(summaries)
