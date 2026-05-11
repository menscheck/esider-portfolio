"""
app/bot/webhook.py
FastAPI webhook endpoint
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent, FollowEvent
from linebot.v3.messaging import MessagingApi, FlexMessage, FlexContainer

from app.core.config import get_config
from app.bot.line_handler import (
    handle_message, handle_postback,
    configuration, get_persona_select_flex,
)

app = FastAPI()
cfg = get_config()["line_bot"]
parser = WebhookParser(cfg["channel_secret"])


def process_events(body: str, signature: str):
    """背景處理所有 LINE events"""
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return

    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        for event in events:
            if isinstance(event, FollowEvent):
                user_id = event.source.user_id
                reply_token = event.reply_token
                flex_dict = get_persona_select_flex()
                try:
                    from linebot.v3.messaging import ReplyMessageRequest
                    messaging_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[
                                FlexMessage(
                                    alt_text="歡迎使用 eSider ESG 永續洞察",
                                    contents=FlexContainer.from_dict(flex_dict),
                                )
                            ],
                        )
                    )
                    print(f"[FollowEvent] reply 發送成功")
                except Exception as e:
                    print(f"[FollowEvent] 發送失敗: {e}")
                    import traceback
                    traceback.print_exc()
            elif isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                handle_message(event, api_client)
            elif isinstance(event, PostbackEvent):
                handle_postback(event, api_client)


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode("utf-8")

    # 立刻回 200 給 LINE
    background_tasks.add_task(process_events, body_str, signature)
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
