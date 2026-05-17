"""
app/core/finmind_client.py

FinMind API 客戶端 + 快取（24 小時）
- 目前專案沒有 `[mongodb]` 設定區塊，避免直接依賴 MongoDB 導致匯入失敗
- 因此先提供「記憶體快取」；未來若補上 MongoDB 設定，可再擴充為 MongoDB 快取
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable

import requests

from app.core.config import get_config

logger = logging.getLogger(__name__)

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

# 財務關鍵字 → dataset 對應
FINANCIAL_KEYWORDS: dict[str, str] = {
    # 營收
    "營收": "TaiwanStockMonthRevenue",
    "月營收": "TaiwanStockMonthRevenue",
    "業績": "TaiwanStockMonthRevenue",

    # 損益/獲利
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

    # 配息股利
    "配息": "TaiwanStockDividend",
    "股利": "TaiwanStockDividend",
    "除息": "TaiwanStockDividend",
    "除權": "TaiwanStockDividend",
    "發放": "TaiwanStockDividend",
    "配多少": "TaiwanStockDividend",

    # 法人
    "法人": "TaiwanStockInstitutionalInvestorsBuySell",
    "外資": "TaiwanStockInstitutionalInvestorsBuySell",
    "三大法人": "TaiwanStockInstitutionalInvestorsBuySell",
    "投信": "TaiwanStockInstitutionalInvestorsBuySell",
    "自營商": "TaiwanStockInstitutionalInvestorsBuySell",
    "買超": "TaiwanStockInstitutionalInvestorsBuySell",
    "賣超": "TaiwanStockInstitutionalInvestorsBuySell",

    # 估值
    "本益比": "TaiwanStockPER",
    "殖利率": "TaiwanStockPER",
    "PBR": "TaiwanStockPER",
    "便宜": "TaiwanStockPER",
    "貴不貴": "TaiwanStockPER",

    # 股價/技術面
    "股價": "TaiwanStockPrice",
    "收盤價": "TaiwanStockPrice",
    "收盤": "TaiwanStockPrice",
    "開盤價": "TaiwanStockPrice",
    "開盤": "TaiwanStockPrice",
    "最高價": "TaiwanStockPrice",
    "最低價": "TaiwanStockPrice",
    "現在股價": "TaiwanStockPrice",
    "目前股價": "TaiwanStockPrice",
    "今天股價": "TaiwanStockPrice",
    "昨天股價": "TaiwanStockPrice",
    "漲跌": "TaiwanStockPrice",
    "成交量": "TaiwanStockPrice",
    "成交": "TaiwanStockPrice",
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

    # 資產負債
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

    # 現金流量
    "自由現金流": "TaiwanStockCashFlowsStatement",
    "現金流": "TaiwanStockCashFlowsStatement",
    "FCF": "TaiwanStockCashFlowsStatement",
    "資本支出": "TaiwanStockCashFlowsStatement",
    "CAPEX": "TaiwanStockCashFlowsStatement",
    "營業活動": "TaiwanStockCashFlowsStatement",
    "投資活動": "TaiwanStockCashFlowsStatement",

    # 融資融券
    "融券": "TaiwanStockMarginPurchaseSell",
    "融資": "TaiwanStockMarginPurchaseSell",
    "借券": "TaiwanStockMarginPurchaseSell",
    "融券張數": "TaiwanStockMarginPurchaseSell",
    "融資張數": "TaiwanStockMarginPurchaseSell",
    "融券餘額": "TaiwanStockMarginPurchaseSell",
    "融資餘額": "TaiwanStockMarginPurchaseSell",
    "空單": "TaiwanStockMarginPurchaseSell",
    "信用交易": "TaiwanStockMarginPurchaseSell",

    # 委買委賣
    "委買": "TaiwanStockPrice",
    "委賣": "TaiwanStockPrice",
    "委買張數": "TaiwanStockPrice",
    "委賣張數": "TaiwanStockPrice",
    "委買单": "TaiwanStockPrice",
    "委賣單": "TaiwanStockPrice",
    "買壓": "TaiwanStockPrice",
    "賣壓": "TaiwanStockPrice",
    "淨委買": "TaiwanStockPrice",

    # 公司基本資料（TaiwanStockInfo 實際欄位：industry_category, stock_id, stock_name, type, date）
    "產業別": "TaiwanStockInfo",
    "產業類別": "TaiwanStockInfo",
    "股票名稱": "TaiwanStockInfo",
    "市場別": "TaiwanStockInfo",
    "上市別": "TaiwanStockInfo",
    "上市股": "TaiwanStockInfo",
    "上櫃股": "TaiwanStockInfo",
    # 資本額/股本 實際在 TaiwanStockBalanceSheet 的 CapitalStock 欄位
    "資本額": "TaiwanStockBalanceSheet",
    "股本": "TaiwanStockBalanceSheet",
    "市値": "TaiwanStockPER",
}

# ========== 24h In-Memory Cache ==========
_CACHE_TTL_HOURS = 24


@dataclass(frozen=True)
class CacheKey:
    stock_id: str
    dataset: str


@dataclass
class CacheEntry:
    data: list[dict[str, Any]]
    updated_at: datetime


_MEMORY_CACHE: dict[CacheKey, CacheEntry] = {}


def detect_financial_intent(query: str) -> list[str]:
    """從查詢文字偵測需要哪些財務資料集"""
    datasets: set[str] = set()
    for kw, dataset in FINANCIAL_KEYWORDS.items():
        if kw in query:
            datasets.add(dataset)
    return list(datasets)


def _get_cached(stock_id: str, dataset: str) -> list[dict[str, Any]] | None:
    key = CacheKey(stock_id=stock_id, dataset=dataset)
    entry = _MEMORY_CACHE.get(key)
    if not entry:
        return None

    cutoff = datetime.now() - timedelta(hours=_CACHE_TTL_HOURS)
    if entry.updated_at < cutoff:
        _MEMORY_CACHE.pop(key, None)
        return None

    logger.info("[FinMind cache(memory)] %s %s", stock_id, dataset)
    return entry.data


def _save_cache(stock_id: str, dataset: str, data: list[dict[str, Any]]) -> None:
    key = CacheKey(stock_id=stock_id, dataset=dataset)
    _MEMORY_CACHE[key] = CacheEntry(data=data, updated_at=datetime.now())


def fetch_financial_data(
    stock_id: str,
    dataset: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    從 FinMind API 取得財務資料（含快取）

    Args:
        stock_id:   股票代碼（或市場代碼，例如 TAIEX）
        dataset:    FinMind dataset 名稱
        start_date: 查詢起始日（預設近 1 年）
        end_date:   查詢結束日（預設今天）

    Returns:
        資料列表
    """
    cached = _get_cached(stock_id, dataset)
    if cached is not None:
        return cached

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

        # FinMind 通常回傳 status: 200 / data: [...]
        if payload.get("status") == 200:
            data = payload.get("data", [])
            if isinstance(data, list):
                typed_data: list[dict[str, Any]] = [d for d in data if isinstance(d, dict)]
            else:
                typed_data = []

            _save_cache(stock_id, dataset, typed_data)
            logger.info("[FinMind API] %s %s %d 筆", stock_id, dataset, len(typed_data))
            return typed_data

        logger.error("[FinMind API error] %s", payload)
        return []
    except Exception:
        logger.exception("[FinMind error] dataset=%s stock_id=%s", dataset, stock_id)
        return []


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _pick_latest_points(points: list[dict[str, Any]], key: str, n: int) -> list[dict[str, Any]]:
    # 避免原始回傳未排序
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


def detect_market_intent(query: str) -> list[str]:
    """偵測是否需要台股大盤/市場總覽"""
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
        "股票",
        "股市",
        "台股今天",
        "今日股市",
        "整體股票",
        "股票市場",
    ]
    return [p for p in patterns if p in query]


AMBIGUOUS_KEYWORDS = [
    "有漲", "有跌", "漲了嗎", "跌了嗎", "漲嗎", "跌嗎",
    "上漲", "下跌", "漲多少", "跌多少",
]


def detect_ambiguous_intent(query: str) -> bool:
    """偵測模糊意圖（可能是薪資也可能是股票）"""
    return any(kw in query for kw in AMBIGUOUS_KEYWORDS)


def detect_compare_windows(query: str) -> dict[str, bool]:
    """
    偵測使用者要比較的時間窗：DOD / WOW / MOM / SOS / YOY
    """
    q = query.replace(" ", "")
    return {
        "DOD": any(x in q for x in ["DOD", "日對日", "昨日", "前一日", "當日比昨日", "與昨天",
                                     "昨天", "前天", "今天", "今日", "當日", "最新", "現在", "目前"]),
        "WOW": any(x in q for x in ["WOW", "週對週", "上週", "近一週", "一週", "這週", "本週"]),
        "MOM": any(x in q for x in ["MOM", "月對月", "上月", "近一個月", "本月比上月"]),
        "SOS": any(x in q for x in ["SOS", "半年對半年", "上半年", "近半年", "半年度"]),
        "YOY": any(x in q for x in ["YOY", "年對年", "去年", "近一年", "一年內"]),
    }


def fetch_taiwan_index_series(
    data_id: str,
    dataset: str = "TaiwanStockTotalReturnIndex",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    取得台股指數序列（用於 DOD/WOW/MOM/SOS/YOY 計算）
    TaiwanStockTotalReturnIndex: columns: price, stock_id, date
    """
    return fetch_financial_data(stock_id=data_id, dataset=dataset, start_date=start_date, end_date=end_date)


def _format_index_summary(
    latest: dict[str, Any],
    prev: dict[str, Any] | None,
    window_name: str,
    pct: float | None,
) -> str:
    date_str = str(latest.get("date", ""))
    latest_price = _safe_float(latest.get("price"))
    base_price = _safe_float(prev.get("price")) if prev else None
    if latest_price is None or base_price is None or pct is None:
        return f"{window_name}：資料不足（{date_str}）"

    return f"{window_name}：{date_str} {latest_price:.2f}（較前值 {base_price:.2f}：{pct:+.2f}%）"


def get_market_index_summary(
    query: str,
    *,
    force: bool = False,
    index_data_id: str = "TAIEX",
    today: datetime | None = None,
) -> str:
    """
    根據查詢取得台股總覽/大盤指數摘要（支援 DOD/WOW/MOM/SOS/YOY）
    force=True：跳過關鍵字 guard，直接查最新指數
    """
    windows = detect_compare_windows(query)
    if not force and not any(windows.values()) and not detect_market_intent(query):
        return ""

    now = today or datetime.now()
    # 取足夠多的交易日/自然日，避免挑不到對應點
    start_date = (now - timedelta(days=370)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    points = fetch_taiwan_index_series(
        data_id=index_data_id,
        start_date=start_date,
        end_date=end_date,
    )
    if not points:
        return ""

    # 取最近約 120 個點（台股大約每週 5 天）
    recent = _pick_latest_points(points, key="price", n=120)
    if not recent:
        return ""

    latest = recent[-1]

    # WOW/MOM/SOS/DOD 用近似交易日距離比對；YOY 則改用「日期往前約一年，找最近一期」避免資料不足
    offsets = {
        "DOD": 1,
        "WOW": 5,
        "MOM": 20,
        "SOS": 100,
    }

    summaries: list[str] = [f"【台股指數({index_data_id})】"]

    # 預先算 YOY 基準日期（用最接近的交易日）
    yoy_target = (now - timedelta(days=365)).strftime("%Y-%m-%d")

    def _closest_point(target_date: str) -> dict[str, Any] | None:
        # recent 已排序，直接找最接近的 date
        def date_as_str(item: dict[str, Any]) -> str:
            return str(item.get("date", ""))
        best: dict[str, Any] | None = None
        best_dist: int | None = None
        for p in recent:
            d = date_as_str(p)
            if not d:
                continue
            # 字串 YYYY-MM-DD 可直接轉成日期差（不需 parse 到 datetime 也能簡化，但這裡穩妥 parse）
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

    # 若沒偵測到任何 window，但偵測到市場意圖：至少提供最新
    if len(summaries) == 1:
        latest_price = _safe_float(latest.get("price"))
        date_str = str(latest.get("date", ""))
        if latest_price is not None:
            summaries.append(f"最新：{date_str} 指數 {latest_price:.2f}")

    return "\n".join(summaries)


def get_financial_summary(stock_id: str, query: str) -> str:
    """
    根據查詢意圖，抓取相關財務資料並格式化為文字摘要
    供 LLM 使用

    Returns:
        財務數據摘要文字
    """
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

        elif dataset == "TaiwanStockBalanceSheet":
            if data:
                # 按日期取最新一筆
                latest_date = max(d.get('date', '') for d in data)
                latest = [d for d in data if d.get('date') == latest_date]
                row = {d['type']: d.get('value', 0) or 0 for d in latest}

                lines = [f"【資產負債（{latest_date}）】"]

                def fmt(v):
                    try:
                        return f"{float(v)/1e8:.1f}億"
                    except:
                        return str(v)

                if 'CapitalStock' in row:
                    lines.append(f"  股本：{fmt(row['CapitalStock'])}")
                if 'TotalAssets' in row:
                    lines.append(f"  總資產：{fmt(row['TotalAssets'])}")
                if 'Liabilities' in row:
                    lines.append(f"  總負債：{fmt(row['Liabilities'])}")
                if 'Equity' in row:
                    lines.append(f"  股東權益：{fmt(row['Equity'])}")
                if 'Liabilities' in row and 'TotalAssets' in row and float(row['TotalAssets']) > 0:
                    debt_ratio = float(row['Liabilities']) / float(row['TotalAssets']) * 100
                    lines.append(f"  負債比：{debt_ratio:.1f}%")
                if 'RetainedEarnings' in row:
                    lines.append(f"  保留盈餘：{fmt(row['RetainedEarnings'])}")
                if 'CashAndCashEquivalents' in row:
                    lines.append(f"  現金及約當現金：{fmt(row['CashAndCashEquivalents'])}")
                if 'CurrentAssets' in row:
                    lines.append(f"  流動資產：{fmt(row['CurrentAssets'])}")
                if 'CurrentLiabilities' in row:
                    lines.append(f"  流動負債：{fmt(row['CurrentLiabilities'])}")

                if len(lines) > 1:
                    summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockMarginPurchaseSell":
            if recent:
                d = recent[-1]
                lines = ["【融資融券（最新）】"]
                lines.append(f"  日期：{d.get('date', 'N/A')}")
                lines.append(f"  融資餘額：{d.get('MarginPurchaseBalance', 'N/A')}張")
                lines.append(f"  融券餘額：{d.get('ShortSaleBalance', 'N/A')}張")
                lines.append(f"  融資買進：{d.get('MarginPurchaseBuy', 'N/A')}張")
                lines.append(f"  融券賣出：{d.get('ShortSaleSell', 'N/A')}張")
                summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockCashFlowsStatement":
            if data:
                # 按季分組，取最近4季
                from collections import defaultdict
                by_date = defaultdict(dict)
                for d in data:
                    by_date[d['date']][d['type']] = d.get('value', 0) or 0
                quarters = sorted(by_date.keys(), reverse=True)[:4]
                lines = ["【現金流量（近4季）】"]
                for q in reversed(quarters):
                    row = by_date[q]
                    op = row.get('CashFlowsFromOperatingActivities') or row.get('NetCashInflowFromOperatingActivities') or 0
                    capex = row.get('PropertyAndPlantAndEquipment') or 0
                    fcf = op - abs(capex)
                    op_b = op / 1e8
                    capex_b = abs(capex) / 1e8
                    fcf_b = fcf / 1e8
                    lines.append(
                        f"  {q[:7]}｜營業現金流：{op_b:,.1f}億 ｜資本支出：{capex_b:,.1f}億 ｜自由現金流(FCF)：{fcf_b:,.1f}億"
                    )
                summaries.append("\n".join(lines))

        elif dataset == "TaiwanStockInfo":
            if data:
                d = data[0]
                lines = ["【公司基本資料】"]
                lines.append(f"  股票代號：{d.get('stock_id', 'N/A')}")
                lines.append(f"  公司名稱：{d.get('stock_name', 'N/A')}")
                lines.append(f"  產業別：{d.get('industry_category', 'N/A')}")
                lines.append(f"  市場：{'上市(TWSE)' if d.get('type') == 'twse' else '上櫃(TPEx)' if d.get('type') == 'tpex' else d.get('type', 'N/A')}")
                lines.append(f"  資料日期：{d.get('date', 'N/A')}")
                summaries.append("\n".join(lines))

    return "\n\n".join(summaries) if summaries else ""
