import json
import os
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI


def _get_client() -> Optional[AzureOpenAI]:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not api_key or not endpoint:
        return None

    return AzureOpenAI(
        api_key=api_key,
        api_version="2024-02-01",
        azure_endpoint=endpoint,
    )


def llm_select_company(query: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    candidates: [{"code":..., "name":...}, ...]
    """
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    client = _get_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if client is None or not deployment:
        return candidates[0]

    prompt = f"""
你是一個台灣上市公司辨識專家。

使用者問題：
{query}

候選公司：
{json.dumps(candidates, ensure_ascii=False)}

請選出「最符合語意」的一家公司。

只回傳 JSON：
{{
  "code": "...",
  "name": "..."
}}
"""

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = (response.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception as e:
        print("LLM error:", e)

    return candidates[0]

