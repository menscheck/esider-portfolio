"""
app/core/intent_detector.py
用 LLM 判斷使用者查詢意圖，取代關鍵字清單
關鍵字庫直接從 finmind_client 動態載入，保持同步
"""

import logging
from openai import AzureOpenAI
from app.core.config import get_config

logger = logging.getLogger(__name__)


def _build_finmind_keywords() -> str:
    """從 finmind_client 動態取得所有台股關鍵字，組成 prompt 用字串"""
    try:
        from app.core.finmind_client import FINANCIAL_KEYWORDS, detect_market_intent
        keys = list(FINANCIAL_KEYWORDS.keys())
        # 加上大盤/市場關鍵字
        market_keys = [
            "大盤", "台股", "加權", "加權指數", "指數", "市場", "盤勢",
            "股市", "股票市場", "TAIEX", "台指", "台指期",
        ]
        all_keys = list(dict.fromkeys(keys + market_keys))  # 去重保序
        # 每10個一組，用頓號分隔
        groups = ["「" + "」「".join(all_keys[i:i+10]) + "」" for i in range(0, len(all_keys), 10)]
        return "\n  ".join(groups)
    except Exception:
        return "「股價」「成交量」「法人」「配息」「營收」「EPS」「獲利」「大盤」「台股」「委買」「委賣」「融資」「融券」"


def detect_intent(query: str) -> str:
    """
    判斷查詢意圖
    回傳: "finmind" / "esg" / "ambiguous" / "oos"
    """
    # 「短時間段」快速路徑：不經 LLM，直接判 finmind
    # 今天/昨天/本週等對应即時漲跌，不可能是薪資或碳費
    _SHORT_TIME_KEYWORDS = [
        "今天", "昨天", "今日", "昨日", "前天",
        "本週", "這週", "上週", "週一", "週二", "週三", "週四", "週五",
        "近期", "最新", "現在", "目前", "目前股價", "即時",
    ]
    q = query.replace(" ", "")
    if any(kw in q for kw in _SHORT_TIME_KEYWORDS):
        logger.info(f"[intent_detector] 短時間段快速路徑 query={query!r} → finmind")
        return "finmind"

    try:
        cfg = get_config()["azure_openai"]
        client = AzureOpenAI(
            azure_endpoint=cfg["endpoint"],
            api_key=cfg["api_key"],
            api_version=cfg["api_version"],
        )

        finmind_keywords = _build_finmind_keywords()

        prompt = f"""判斷以下問題的意圖類型，只回傳一個英文單字。

判斷優先順序（依序檢查，第一個符合就停止）：

【第一優先：有明確台股/財務主詞】→ finmind
以下任何關鍵字出現即判定為 finmind：
  {finmind_keywords}

⚠️ 注意：單純的漲跌動詞（有漲、有跌、漲了、跌了、漲嗎、跌嗎、上漲、下跌、漲多少、跌多少）本身不算台股關鍵字，不可單獨觸發 finmind。必須搭配明確台股主詞（如股價、收盤、成交量、EPS、法人等）才算。

【第二優先：有明確 ESG 主詞】→ esg
含「薪水」「薪資」「待遇」「特休」「員工福利」「職涯」「碳排」「ESG」「永續」「GRI」「TCFD」「供應鏈管理」「治理」「環境績效」「社會責任」「永續報告」→ esg

【第三優先：無明確主詞，看時間線索】
- 含「今天」「今日」「昨天」「這週」「本週」「近期」「最新」「目前」「現在」→ finmind
- 含「今年」「去年」「這幾年」且無明確主詞 → ambiguous

【第四優先：完全超出台股/ESG/財務/企業範圍】→ oos
以下任一情況直接判 oos：
- 科幻/娛樂/八卦：外星人、UFO、鬼怪、星座、電影、音樂、遊戲、動漫
- 人物評論：政治人物言論、名人八卦、體育明星
- 生活類：天氣、食物、料理、寵物、旅遊、健康、醫療
- 無意義輸入：單一表情符號、影片/圖片描述、短句完全無上下文（如「牠在幹嘛」「那是什麼」）
- 其他與台股/ESG/財務/企業完全無關的問題

【第五優先：都不符合】→ ambiguous

問題：「{query}」

只回傳：finmind 或 esg 或 ambiguous 或 oos"""

        response = client.chat.completions.create(
            model=cfg["deployment"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0,
        )
        result = response.choices[0].message.content.strip().lower()
        if result not in ("finmind", "esg", "ambiguous", "oos"):
            result = "esg"
        logger.info(f"[intent_detector] query={query!r} → {result}")
        return result
    except Exception:
        logger.exception("[intent_detector] 失敗，fallback 到 esg")
        return "esg"
