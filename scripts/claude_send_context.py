#!/usr/bin/env python3
"""
scripts/claude_send_context.py
範例：把 project_memory.json 做 chunk，作為上下文送到 Claude API（示範用，可依照 Claude API 調整 header/payload）

使用方式：
1. 設定環境變數 CLAUDE_API_KEY 與 CLAUDE_API_URL（或在程式中直接修改）
2. 確保 scripts/project_memory.json 存在（已由前一步匯出）
3. 執行：python claude_send_context.py
"""

import os
import json
import requests

PROJECT_JSON = os.path.join(os.path.dirname(__file__), 'project_memory.json')


def chunk_text(s, max_chars=1500):
    """簡單的字元切分器，盡量在換行或句點處斷句。返回字串清單。"""
    s = s.strip()
    chunks = []
    while s:
        if len(s) <= max_chars:
            chunks.append(s)
            break
        # 優先在換行處切分
        split_pos = s.rfind('\n', 0, max_chars)
        if split_pos == -1:
            split_pos = s.rfind('. ', 0, max_chars)
        if split_pos == -1 or split_pos < max_chars // 2:
            split_pos = max_chars
        chunk = s[:split_pos].strip()
        chunks.append(chunk)
        s = s[len(chunk):].strip()
    return chunks


def load_documents(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_messages(docs, max_chars=1500):
    messages = []
    for d in docs:
        header = f"Title: {d.get('title','')} | Category: {d.get('category','')} | Tags: {', '.join(d.get('tags', []))}\n\n"
        text = header + d.get('content','')
        for chunk in chunk_text(text, max_chars=max_chars):
            # 使用 system role 儲存上下文片段；依 API 需求調整 role/naming
            messages.append({"role": "system", "content": chunk})
    return messages


def send_to_claude(messages, user_query="請用中文摘要上述記憶並列出最重要的 5 個 tags（按出現次數）"):
    # 預設使用環境變數來設定 API
    CLAUDE_API_URL = os.environ.get('CLAUDE_API_URL', 'https://api.example.com/v1/claude')
    API_KEY = os.environ.get('CLAUDE_API_KEY', 'REPLACE_WITH_YOUR_KEY')

    payload = {
        # 許多 LLM API 使用 messages 格式；若你的 Claude 版本使用不同欄位（例如 prompt / input），請調整
        "model": os.environ.get('CLAUDE_MODEL', 'claude-2.1'),
        "messages": messages + [{"role": "user", "content": user_query}],
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
        # 某些 Claude 版本使用 'x-api-key' 或 'Anthropic-API-Key'；視你使用的 API 而定
        # 'x-api-key': API_KEY,
    }

    resp = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=60)
    try:
        print('Status:', resp.status_code)
        print('Response:')
        print(resp.text)
    except Exception as e:
        print('Error printing response:', e)


if __name__ == '__main__':
    if not os.path.exists(PROJECT_JSON):
        print('project_memory.json not found at', PROJECT_JSON)
        raise SystemExit(1)

    docs = load_documents(PROJECT_JSON)
    messages = build_messages(docs, max_chars=1500)
    print(f'Built {len(messages)} context messages from {len(docs)} documents')

    # 範例查詢
    send_to_claude(messages, user_query='請以中文（100-200字）總結這個專案的核心架構與資料來源，並列出最常見的 5 個 tags。')
