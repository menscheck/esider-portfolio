"""
app/bot/line_handler.py
LINE Bot 訊息處理邏輯（含遞迴選單）
"""

from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ShowLoadingAnimationRequest,
    ReplyMessageRequest, TextMessage, FlexMessage,
    FlexContainer, QuickReply, QuickReplyItem,
    PostbackAction, MessageAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent

from app.core.pipeline import query
from app.core.persona_router import Persona
from app.core.config import get_config
from app.core.finmind_client import detect_market_intent, detect_financial_intent
from app.core.company_resolver import resolve_companies_from_query
import logging

from app.bot.suggestion_engine import (
    generate_followup_questions,
    generate_similar_companies,
    generate_persona_questions,
)
from app.bot.card_builder import build_carousel, extract_key_points

cfg = get_config()["line_bot"]
configuration = Configuration(access_token=cfg["channel_access_token"])

user_sessions: dict[str, dict] = {}

PERSONA_OPTIONS = {
    "job_seeker": Persona.JOB_SEEKER,
    "institutional": Persona.INSTITUTIONAL_INVESTOR,
    "retail": Persona.RETAIL_INVESTOR,
    "esg_pro": Persona.ESG_PRACTITIONER,
}

PERSONA_NAMES = {
    Persona.JOB_SEEKER: "求職者",
    Persona.INSTITUTIONAL_INVESTOR: "機構投資人",
    Persona.RETAIL_INVESTOR: "散戶投資人",
    Persona.ESG_PRACTITIONER: "ESG從業者",
}

PERSONA_ICONS = {
    "求職者": "💼",
    "機構投資人": "👔",
    "散戶投資人": "📈",
    "ESG從業者": "🌱",
}

_FINMIND_PERSONAS = {Persona.RETAIL_INVESTOR, Persona.INSTITUTIONAL_INVESTOR}


def get_persona_select_flex() -> dict:
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "eSider ESG 永續洞察",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#F5F0EB",
                },
                {
                    "type": "text",
                    "text": "選擇身份，獲得最適合你的 ESG 資訊",
                    "size": "xs",
                    "color": "#D4C5B5",
                    "margin": "sm",
                }
            ],
            "backgroundColor": "#6B7B6E",  # 莫蘭迪綠灰
            "paddingAll": "16px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "backgroundColor": "#F5F0EB",  # 莫蘭迪米白
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "👔 機構投資人",
                        "data": "persona=institutional",
                        "displayText": "我是機構投資人",
                    },
                    "style": "primary",
                    "color": "#7B8FA1",  # 莫蘭迪藍灰
                    "margin": "md",
                    "height": "sm",
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
                    "color": "#9B8EA0",  # 莫蘭迪紫灰
                    "margin": "sm",
                    "height": "sm",
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
                    "color": "#B5967A",  # 莫蘭迪棕
                    "margin": "sm",
                    "height": "sm",
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
                    "color": "#6B7B6E",  # 莫蘭迪綠灰
                    "margin": "sm",
                    "height": "sm",
                },
            ],
            "paddingAll": "16px",
        },
    }


def _reply(api_client: ApiClient, reply_token: str, messages: list):
    MessagingApi(api_client).reply_message(
        ReplyMessageRequest(reply_token=reply_token, messages=messages)
    )


def _is_broad_query(question: str) -> bool:
    question = question.strip()
    broad_markers = [
        "哪些", "還有", "還有哪些", "其他公司", "同業", "同類公司",
        "各家公司", "哪些公司", "還有沒有", "比較", "差異", "還有什麼"
    ]
    return any(marker in question for marker in broad_markers)


def _text_with_qr(text: str, options: list[dict]) -> TextMessage:
    """
    建立帶 Quick Reply 的 TextMessage
    options: [{"label": str, "data": str, "display": str}]
    """
    items = []
    for opt in options[:13]:  # LINE 限制最多13個
        items.append(QuickReplyItem(
            action=PostbackAction(
                label=opt["label"][:20],
                data=opt["data"],
                display_text=opt.get("display", opt["label"]),
            )
        ))
    return TextMessage(
        text=text,
        quick_reply=QuickReply(items=items),
    )


def _main_menu_options(user_id: str) -> list[dict]:
    """回答後的主選單三個選項"""
    return [
        {"label": "🔍 延伸問題", "data": f"menu=followup&uid={user_id}", "display": "延伸問題"},
        {"label": "🏢 同類公司", "data": f"menu=similar&uid={user_id}", "display": "同類型公司"},
        {"label": "👤 換角色",   "data": f"menu=persona&uid={user_id}", "display": "換角色"},
    ]


def _do_query_and_reply(
    api_client: ApiClient,
    reply_token: str,
    user_id: str,
    question: str,
):
    """執行查詢並回覆，附帶主選單（多公司時提供每家公司×角色的延伸問題）"""
    session = user_sessions[user_id]
    persona = session["persona"]
    persona_name = PERSONA_NAMES[persona]

    try:
        # 顯示「輸入中」動畫（最長20秒）
        try:
            MessagingApi(api_client).show_loading_animation(
                ShowLoadingAnimationRequest(
                    chat_id=user_id,
                    loading_seconds=20,
                )
            )
        except Exception:
            pass  # typing indicator 失敗不影響主流程

        # 預先偵測公司與台股意圖
        pre_detected = resolve_companies_from_query(question)
        has_company = bool(pre_detected) or bool(session.get("last_company"))
        has_market_intent = detect_market_intent(question)

        # 情況1：散戶/機構 + 無公司 + 無台股/財務關鍵字 + 上次也是 ESG 查詢 → 提示輸入公司
        if (
            persona in _FINMIND_PERSONAS
            and not has_company
            and not has_market_intent
            and not detect_financial_intent(question)
            and session.get("last_query_type", "esg") == "esg"
        ):
            persona_name_local = PERSONA_NAMES[persona]
            questions = generate_persona_questions(persona_name_local)
            options = [
                {"label": q[:20], "data": f"ask={q}", "display": q}
                for q in questions[:3]
            ]
            msg = _text_with_qr(
                "請問你想查詢哪家公司？\n直接輸入公司名稱，或從以下問題開始 👇",
                options,
            )
            _reply(api_client, reply_token, [msg])
            return

        # 非投資人 + 有台股/財務意圖 → 儲存 pending_question 再提示切換身分
        if (
            persona not in _FINMIND_PERSONAS
            and (detect_market_intent(question) or bool(detect_financial_intent(question)))
        ):
            user_sessions[user_id]["pending_question"] = question
            options = [
                {"label": "👔 機構投資人", "data": "persona=institutional", "display": "切換為機構投資人"},
                {"label": "📈 散戶投資人", "data": "persona=retail", "display": "切換為散戶投資人"},
            ]
            msg = _text_with_qr(
                "台股相關問題請選擇投資人身份，選完後將自動回答你的問題 👇",
                options,
            )
            _reply(api_client, reply_token, [msg])
            return

        # 計算本次查詢意圖類型；若非財務/台股，延續上次 session 的類型
        current_query_type = (
            "finmind"
            if (has_market_intent or bool(detect_financial_intent(question)))
            else session.get("last_query_type", "esg")
        )

        # 先讓 pipeline 從 query 自動偵測公司
        result = query(user_query=question, persona=persona, company=None)
        detected_company = result.get("company")

        # 偵測不到才繼承 last_company
        if not detected_company:
            last_company = session.get("last_company")
            if last_company:
                result = query(user_query=question, persona=persona, company=last_company)

        answer = result["answer"]
        company = result.get("company")

        chunks = result.get("chunks", [])
        # 只有當問題中明確偵測到公司時才更新 last_company；
        # 若問題沒有公司，繼承 session 的 last_company，避免 ESG chunks 的別家公司覆蓋
        new_company = company if bool(pre_detected) else None
        primary_company = new_company or session.get("last_company") or (chunks[0].get("company") if chunks else None)

        # 用獨立 prompt 抽取與問題直接相關的卡片
        cards = extract_key_points(answer, question, persona_name)
        carousel = build_carousel(cards, user_id) if cards else None

        asked = session.get("asked_questions", set())
        asked.add(question)
        user_sessions[user_id].update({
            "last_query": question,
            "last_company": primary_company,
            "last_answer": answer,
            "card_details": [p.get("detail", p.get("summary", "")) for p in cards] if cards else [],
            "asked_questions": asked,
            "last_query_type": current_query_type,
        })
        logging.getLogger(__name__).info(
            f"session updated: last_company={primary_company}, query={question}, broad={company is None}"
        )

        query_type = user_sessions[user_id].get("last_query_type", "esg")
        followup_company = primary_company or ("台股大盤" if query_type == "finmind" else None)

        if followup_company:
            questions = generate_followup_questions(
                followup_company,
                question,
                persona_name,
                exclude=asked,
                include_broad=True,
                query_type=query_type,
            )
            options = []
            for i, q in enumerate(questions[:3]):
                is_broad_followup = (i == 2)
                options.append({
                    "label": q[:20],
                    "data": f"ask_broad={q}" if is_broad_followup else f"ask={q}",
                    "display": q,
                })
            options += _main_menu_options(user_id)
        else:
            options = _main_menu_options(user_id)

        if carousel:
            # Carousel + 延伸選單
            carousel_msg = FlexMessage(
                alt_text=f"ESG重點摘要（{len(cards)}項）",
                contents=FlexContainer.from_dict(carousel),
            )
            menu_msg = _text_with_qr(
                "點選卡片可查看詳細說明 👆",
                options[:6],
            )
            _reply(api_client, reply_token, [carousel_msg, menu_msg])
        else:
            # fallback：純文字
            msg = _text_with_qr(answer, options[:6])
            _reply(api_client, reply_token, [msg])

    except Exception as e:
        _reply(api_client, reply_token, [
            TextMessage(text=f"查詢錯誤，請稍後再試。\n{str(e)}")
        ])


def handle_message(event: MessageEvent, api_client: ApiClient):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # 開始 / 重設
    if text.lower() in ["開始", "hi", "hello", "選擇身份", "重設", "/start"]:
        _reply(api_client, event.reply_token, [
            FlexMessage(
                alt_text="請選擇您的身份",
                contents=FlexContainer.from_dict(get_persona_select_flex()),
            )
        ])
        return

    # 尚未選擇 persona
    if user_id not in user_sessions:
        if detect_market_intent(text) or bool(detect_financial_intent(text)):
            user_sessions[user_id] = {
                "persona": Persona.RETAIL_INVESTOR,
                "last_query": None,
                "last_company": None,
                "last_answer": None,
                "card_details": [],
                "asked_questions": set(),
                "last_query_type": "finmind",
                "pending_question": None,
            }
        else:
            _reply(api_client, event.reply_token, [
                TextMessage(text="請先輸入「開始」選擇您的身份 🙏")
            ])
            return

    # 一般查詢
    _do_query_and_reply(api_client, event.reply_token, user_id, text)


def handle_postback(event: PostbackEvent, api_client: ApiClient):
    user_id = event.source.user_id
    data = event.postback.data

    # ── Persona 選擇 ──────────────────────────────
    if data.startswith("persona="):
        persona_key = data.split("=")[1]
        persona = PERSONA_OPTIONS.get(persona_key)
        if not persona:
            return

        pending = user_sessions.get(user_id, {}).get("pending_question")
        user_sessions[user_id] = {
            "persona": persona,
            "last_query": None,
            "last_company": None,
            "last_answer": None,
            "card_details": [],
            "asked_questions": set(),
            "pending_question": None,
        }

        persona_name = PERSONA_NAMES[persona]
        icon = PERSONA_ICONS.get(persona_name, "")

        # 生成推薦問題
        questions = generate_persona_questions(persona_name)
        options = [
            {"label": q[:20], "data": f"ask={q}", "display": q}
            for q in questions[:3]
        ]

        msg = _text_with_qr(
            f"✅ 身份：{icon} {persona_name}\n\n"
            f"👋 歡迎使用 eSider ESG 查詢助理！\n"
            f"直接輸入問題，或從以下推薦問題開始 👇\n"
            f"（輸入「開始」可重新選擇身份）",
            options,
        )
        if pending:
            user_sessions[user_id]["last_query_type"] = (
                "finmind"
                if (detect_market_intent(pending) or bool(detect_financial_intent(pending)))
                else "esg"
            )
            user_sessions[user_id]["last_company"] = None
            user_sessions[user_id]["pending_question"] = None
            _do_query_and_reply(api_client, event.reply_token, user_id, pending)
            return
        _reply(api_client, event.reply_token, [msg])
        return

    # ── 廣泛型延伸問題（第3題）──────────────
    if data.startswith("ask_broad="):
        question = data[10:]
        if user_id not in user_sessions:
            _reply(api_client, event.reply_token, [
                TextMessage(text="請先輸入「開始」選擇身份 🙏")
            ])
            return

        session = user_sessions[user_id]
        persona = session["persona"]
        persona_name = PERSONA_NAMES[persona]

        # 顯示「輸入中」動畫（最長20秒）
        try:
            MessagingApi(api_client).show_loading_animation(
                ShowLoadingAnimationRequest(
                    chat_id=user_id,
                    loading_seconds=20,
                )
            )
        except Exception:
            pass  # typing indicator 失敗不影響主流程

        try:
            result = query(user_query=question, persona=persona, company=None)
            answer = result["answer"]
            chunks = result.get("chunks", [])

            asked = session.get("asked_questions", set())
            asked.add(question)
            user_sessions[user_id]["asked_questions"] = asked

            # 讓 ask_broad 延伸也能跟隨原意圖（台股/財務 或 ESG）
            user_sessions[user_id].update({
                **user_sessions[user_id],
                "last_query_type": "finmind"
                if detect_financial_intent(question)
                else "esg",
            })

            mentioned = []
            seen = set()
            for c in chunks:
                co = c.get("company")
                if co and co not in seen:
                    seen.add(co)
                    mentioned.append(co)

            if mentioned:
                deep_options = [
                    {"label": f"深入了解{co[:8]}", "data": f"company_select={co}", "display": f"深入了解{co}"}
                    for co in mentioned[:3]
                ]
                deep_options += [{"label": "👤 換角色", "data": f"menu=persona&uid={user_id}", "display": "換角色"}]
                msg = _text_with_qr(answer, deep_options)
            else:
                msg = _text_with_qr(answer, _main_menu_options(user_id))

            _reply(api_client, event.reply_token, [msg])

        except Exception as e:
            _reply(api_client, event.reply_token, [
                TextMessage(text=f"查詢錯誤：{str(e)}")
            ])
        return

    # ── 直接問問題（推薦/延伸選單觸發）──────────────
    if data.startswith("ask="):
        question = data[4:]
        if user_id not in user_sessions:
            _reply(api_client, event.reply_token, [
                TextMessage(text="請先輸入「開始」選擇身份 🙏")
            ])
            return

        # 顯示「輸入中」動畫（最長20秒）
        try:
            MessagingApi(api_client).show_loading_animation(
                ShowLoadingAnimationRequest(
                    chat_id=user_id,
                    loading_seconds=20,
                )
            )
        except Exception:
            pass  # typing indicator 失敗不影響主流程

        _do_query_and_reply(api_client, event.reply_token, user_id, question)
        return

    if data.startswith("card_detail="):
        # 解析 card index
        parts = data.split("&")
        card_idx = int(parts[0].split("=")[1])

        session = user_sessions.get(user_id, {})
        # 從 session 取得上一次的卡片詳細內容
        card_details = session.get("card_details", [])

        if card_idx < len(card_details):
            detail_text = card_details[card_idx]
        else:
            detail_text = "抱歉，找不到詳細資料，請重新查詢。"

        msg = _text_with_qr(detail_text, _main_menu_options(user_id))
        _reply(api_client, event.reply_token, [msg])
        return

    # ── 主選單：延伸問題 ──────────────────────────
    if "menu=followup" in data:
        session = user_sessions.get(user_id, {})
        company = session.get("last_company")
        last_query = session.get("last_query") or ""
        persona_name = PERSONA_NAMES.get(session.get("persona"), "求職者")

        query_type = session.get("last_query_type", "esg")
        followup_company = company or ("台股大盤" if query_type == "finmind" else None)

        if not followup_company:
            _reply(api_client, event.reply_token, [
                TextMessage(text="請先查詢一家公司，再點延伸問題 🙏")
            ])
            return

        asked = session.get("asked_questions", set())
        questions = generate_followup_questions(
            followup_company,
            last_query,
            persona_name,
            exclude=asked,
            include_broad=True,
            query_type=query_type,
        )
        options = [
            {"label": q[:20], "data": f"ask={q}", "display": q}
            for q in questions[:3]
        ]
        display_name = company or "台股大盤"
        msg = _text_with_qr(f"🔍 關於「{display_name}」的延伸問題：", options)
        _reply(api_client, event.reply_token, [msg])
        return

    # ── 主選單：同類型公司 ────────────────────────
    if "menu=similar" in data:
        session = user_sessions.get(user_id, {})
        company = session.get("last_company")
        last_query = session.get("last_query") or ""

        # debug log
        logging.getLogger(__name__).info(
            f"menu=similar, company={company}, last_query={last_query}"
        )

        # 如果 company 是 None，從 last_query 嘗試解析
        if not company:
            from app.core.company_resolver import resolve_companies_from_query
            detected = resolve_companies_from_query(last_query)
            company = detected[0] if detected else None

        if not company:
            _reply(api_client, event.reply_token, [
                TextMessage(text="請先查詢一家公司，再點同類型公司 🙏")
            ])
            return

        companies = generate_similar_companies(company, last_query)
        options = [
            {"label": c[:20], "data": f"company_select={c}", "display": c}
            for c in companies[:3]
        ]
        msg = _text_with_qr(f"🏢 與「{company}」同類型的公司：", options)
        _reply(api_client, event.reply_token, [msg])
        return

    # ── 選擇公司 → 顯示該公司延伸問題 ────────────
    if data.startswith("company_select="):
        selected = data.split("=")[1]
        session = user_sessions.get(user_id, {})
        last_query = session.get("last_query")
        persona_name = PERSONA_NAMES.get(session.get("persona"), "求職者")

        if user_id in user_sessions:
            user_sessions[user_id]["last_company"] = selected

        if last_query:
            exclude = session.get("asked_questions", set())
            query_type = session.get("last_query_type", "esg")
            questions = generate_followup_questions(
                selected,
                last_query,
                persona_name,
                exclude=exclude,
                include_broad=False,
                query_type=query_type,
            )
            options = [
                {"label": q[:20], "data": f"ask={q}", "display": q}
                for q in questions[:3]
            ]
            msg = _text_with_qr(f"📊 關於「{selected}」你可能想問：", options)
        else:
            persona_hints = {
                "求職者": f"例如：「{selected}薪資福利如何？」「{selected}加班文化怎樣？」",
                "機構投資人": f"例如：「{selected}TCFD氣候風險量化？」「{selected}供應鏈ESG稽核？」",
                "散戶投資人": f"例如：「{selected}最近獲利如何？」「{selected}配息穩定嗎？」",
                "ESG從業者": f"例如：「{selected}GRI揭露完整度？」「{selected}雙重重大性方法？」",
            }
            hint = persona_hints.get(persona_name, f"請輸入關於「{selected}」的問題")
            msg = _text_with_qr(
                f"✅ 已選擇「{selected}」\n\n請直接輸入你想問的問題 👇\n{hint}",
                _main_menu_options(user_id),
            )

        _reply(api_client, event.reply_token, [msg])
        return

    # ── 主選單：換角色 ────────────────────────────
    if "menu=persona" in data:
        session = user_sessions.get(user_id, {})
        current = PERSONA_NAMES.get(session.get("persona"), "")

        options = []
        for name, key in [("求職者","job_seeker"),("機構投資人","institutional"),
                           ("散戶投資人","retail"),("ESG從業者","esg_pro")]:
            if name == current:
                continue
            icon = PERSONA_ICONS.get(name, "")
            options.append({
                "label": f"{icon} {name}",
                "data": f"persona={key}",
                "display": f"切換為{name}",
            })

        msg = _text_with_qr("請選擇新的身份：", options)
        _reply(api_client, event.reply_token, [msg])
        return
