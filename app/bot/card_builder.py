"""
app/bot/card_builder.py
將 LLM 回答拆解成 Carousel Flex Message 卡片
"""

import json
import logging
from openai import AzureOpenAI
from app.core.config import get_config

logger = logging.getLogger(__name__)

CARD_COLORS = [
    "#27ACB2",  # 青綠
    "#FF6B6E",  # 珊瑚紅
    "#A17DF5",  # 紫
    "#F5A623",  # 橘
    "#4CAF50",  # 綠
]

PROGRESS_COLORS = [
    "#0D8186",
    "#DE5658",
    "#7D51E4",
    "#C47D0E",
    "#2E7D32",
]


def _get_client():
    cfg = get_config()["azure_openai"]
    return AzureOpenAI(
        azure_endpoint=cfg["endpoint"],
        api_key=cfg["api_key"],
        api_version=cfg["api_version"],
    ), cfg["deployment"]


def extract_key_points(answer: str, query: str, persona_name: str) -> list[dict]:
    """
    用 LLM 從回答中抽取與 query 直接相關的重點製作卡片，回傳結構化 JSON。
    """
    client, deployment = _get_client()

    prompt = f"""從以下回答中，抽取與「{query}」直接相關的重點製作卡片。

回答內容：
{answer}

規則：
1. title 必須是問題核心關鍵字（問薪資福利 → 薪資/福利/假期/補助/健康）
2. value 可以是數字（371萬）、文字評級（業界最高）、項目（14個月）、狀態（已提供）
3. 沒有明確數字時，用文字描述如「多項補助」「優於法令」「已提供」
4. progress：有具體數字按比例；文字性描述給75（代表有做但無法量化）
5. 絕對禁止：持股比例、女性比例、離職率、新進率 出現在薪資福利問題的卡片中
6. 若回答中真的沒有相關數據，回傳空陣列[]

問「薪資結構與員工福利」的卡片範例：
[
  {{"title":"薪資水準","value":"市場競爭力","progress":75,"summary":"薪資具競爭力","detail":"①薪資福利公平透明，定期檢視市場水準。②優於同業平均，連續入選台灣高薪100指數。③求職者可期待具市場競爭力的薪資待遇。④(2024-p.96)"}},
  {{"title":"年終保障","value":"14個月","progress":85,"summary":"保障年終獎金","detail":"①保障年終14個月，另有績效獎金依個人表現加發。②優於多數同業僅保障12個月。③實際年收入比月薪推算高出約17%。④(2024-p.xx)"}},
  {{"title":"健康支持","value":"已提供","progress":75,"summary":"員工身心健康","detail":"①提供心理諮商、健康檢查、視障按摩、健身設施等多項福利。②補助金額及項目數優於法令最低要求。③有助降低員工健康風險與離職意願。④(2024-p.xx)"}},
  {{"title":"休假制度","value":"優於法令","progress":80,"summary":"特休優於勞基法","detail":"①特休天數優於勞基法規定，並提供陪產假、育嬰留停等彈性假別。②同業中屬中上水準。③對需要工作生活平衡的求職者友善。④(2024-p.xx)"}}
]

只回傳JSON陣列（2~5個），格式：
{{"title":"6字內","value":"8字內","progress":0-100,"summary":"20字內","detail":"詳細說明150字以內，必須包含：①具體數字或政策內容 ②與同業或法令比較 ③對使用者的實際意義 ④頁碼來源(2024-p.xx)"}}

如果不是 JSON 陣列，必須修正後只回傳 JSON 陣列。"""

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1,
        )
        content = response.choices[0].message.content.strip()

        # 兼容：移除 code fence，並擷取第一個 JSON array
        content = content.replace("```json", "").replace("```", "").strip()
        if "[" in content and "]" in content:
            start = content.find("[")
            end = content.rfind("]")
            content = content[start : end + 1]

        parsed = json.loads(content)
        if not isinstance(parsed, list):
            return []
        result = parsed[:5]
        return [p for p in result if isinstance(p, dict)]
    except Exception as e:
        logger.error(f"extract_key_points error: {e}")
        return []


def build_carousel(points: list[dict], user_id: str) -> dict | None:
    """
    將重點清單轉為 LINE Carousel Flex Message dict
    """
    if not points:
        return None

    bubbles = []
    for i, point in enumerate(points):
        color = CARD_COLORS[i % len(CARD_COLORS)]
        progress_color = PROGRESS_COLORS[i % len(PROGRESS_COLORS)]
        progress_pct = max(5, min(100, int(point.get("progress", 50))))

        bubble = {
            "type": "bubble",
            "size": "nano",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": point["title"],
                        "color": "#ffffff",
                        "align": "start",
                        "size": "md",
                        "gravity": "center",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": point["value"],
                        "color": "#ffffff",
                        "align": "start",
                        "size": "xs",
                        "gravity": "center",
                        "margin": "lg",
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [{"type": "filler"}],
                                "width": f"{progress_pct}%",
                                "backgroundColor": progress_color,
                                "height": "6px",
                            }
                        ],
                        "backgroundColor": "#FFFFFF40",
                        "height": "6px",
                        "margin": "sm",
                    },
                ],
                "backgroundColor": color,
                "paddingTop": "19px",
                "paddingAll": "12px",
                "paddingBottom": "16px",
                "action": {
                    "type": "postback",
                    "label": point["title"],
                    "data": f"card_detail={i}&uid={user_id}",
                    "displayText": f"告訴我更多關於「{point['title']}」",
                },
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": point["summary"],
                                "color": "#8C8C8C",
                                "size": "xxs",
                                "wrap": True,
                            }
                        ],
                        "flex": 1,
                    }
                ],
                "spacing": "md",
                "paddingAll": "12px",
            },
            "styles": {"footer": {"separator": False}},
        }
        bubbles.append(bubble)

    return {
        "type": "carousel",
        "contents": bubbles,
    }
