def extract_metric(context: str):
    from openai import AzureOpenAI
    import os
    import json

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

    prompt = f"""
從以下內容中抽取明確數據：

{context}

規則：
- 僅回傳 JSON
- 沒有數據回傳 null
- 不要猜測

格式：
{{
  "value": number or null,
  "unit": "",
  "year": "",
  "text": ""
}}
"""

    res = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    try:
        return json.loads(res.choices[0].message.content)
    except Exception:
        return {"value": None}


import re

class MetricExtractor:

    def extract(self, text):

        data = {}

        # 碳排
        carbon_matches = re.findall(r"(20\d{2})年碳排放量為(\d+)", text)
        carbon_decline_matches = re.findall(r"(20\d{2})年降至(\d+)噸", text)
        if carbon_matches or carbon_decline_matches:
            carbon_data = {}
            for y, v in carbon_matches:
                carbon_data[int(y)] = float(v)
            for y, v in carbon_decline_matches:
                carbon_data[int(y)] = float(v)
            data["carbon"] = carbon_data

        # 工傷（簡化）
        injury_matches = re.findall(r"(20\d{2})年工傷率為(\d+\.?\d*)", text)
        injury_rise_matches = re.findall(r"(20\d{2})年升至(\d+\.?\d*)", text)
        if injury_matches or injury_rise_matches:
            injury_data = {}
            for y, v in injury_matches:
                injury_data[int(y)] = float(v)
            for y, v in injury_rise_matches:
                injury_data[int(y)] = float(v)
            data["injury_rate"] = injury_data

        return data

