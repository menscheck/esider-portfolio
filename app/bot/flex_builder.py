"""
app/bot/flex_builder.py
Flex Message 與 Quick Reply 建構工具
（此檔案目前為保留模組，主要邏輯已整合至 line_handler.py）
"""


def build_answer_with_menu(answer: str, user_id: str) -> dict:
    """
    回答 + 底部三個選項的 Quick Reply dict
    （供未來擴充使用，目前 line_handler 直接用 _text_with_qr）
    """
    return {
        "type": "text",
        "text": answer,
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "🔍 延伸問題",
                        "data": f"menu=followup&uid={user_id}",
                        "displayText": "延伸問題",
                    },
                },
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "🏢 同類公司",
                        "data": f"menu=similar&uid={user_id}",
                        "displayText": "同類型公司",
                    },
                },
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "👤 換角色",
                        "data": f"menu=persona&uid={user_id}",
                        "displayText": "換角色",
                    },
                },
            ]
        },
    }


def build_options_quick_reply(options: list[str], postback_prefix: str) -> dict:
    """
    通用選項 Quick Reply dict
    options: 最多3個選項文字
    postback_prefix: postback data 前綴，例如 "ask" / "company_select"
    """
    items = []
    for opt in options[:3]:
        label = opt[:20]
        items.append({
            "type": "action",
            "action": {
                "type": "postback",
                "label": label,
                "data": f"{postback_prefix}={opt}",
                "displayText": opt,
            },
        })
    return {
        "type": "text",
        "text": "請選擇：",
        "quickReply": {"items": items},
    }


def build_persona_quick_reply(current_persona: str) -> dict:
    """
    換角色選單 dict（排除當前角色）
    """
    all_personas = [
        ("求職者",   "💼", "job_seeker"),
        ("機構投資人", "👔", "institutional"),
        ("散戶投資人", "📈", "retail"),
        ("ESG從業者", "🌱", "esg_pro"),
    ]
    items = []
    for name, icon, key in all_personas:
        if name == current_persona:
            continue
        items.append({
            "type": "action",
            "action": {
                "type": "postback",
                "label": f"{icon} {name}",
                "data": f"persona={key}",
                "displayText": f"切換為{name}",
            },
        })
    return {
        "type": "text",
        "text": "請選擇新的身份：",
        "quickReply": {"items": items},
    }


def build_persona_select_flex() -> dict:
    """
    身份選擇 Flex Message bubble dict
    （與 line_handler.py 的 get_persona_select_flex 相同，統一放這裡）
    """
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "eSider ESG 查詢助理",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF",
                }
            ],
            "backgroundColor": "#0a2342",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": "請選擇您的身份，獲得最適合您的 ESG 資訊",
                    "wrap": True,
                    "size": "sm",
                    "color": "#555555",
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "👔 機構投資人",
                        "data": "persona=institutional",
                        "displayText": "我是機構投資人",
                    },
                    "style": "primary",
                    "color": "#0a2342",
                    "margin": "md",
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "📈 散戶投資人",
                        "data": "persona=retail",
                        "displayText": "我是散戶投資人",
                    },
                    "style": "primary",
                    "color": "#1a6b3c",
                    "margin": "sm",
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "💼 求職者",
                        "data": "persona=job_seeker",
                        "displayText": "我是求職者",
                    },
                    "style": "primary",
                    "color": "#8b4513",
                    "margin": "sm",
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🌱 ESG 從業者",
                        "data": "persona=esg_pro",
                        "displayText": "我是ESG從業者",
                    },
                    "style": "primary",
                    "color": "#4b0082",
                    "margin": "sm",
                },
            ],
        },
    }