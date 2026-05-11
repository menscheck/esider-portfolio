import re

class AnswerGenerator:

    def __init__(self):
        from app.services.metric_extractor import MetricExtractor
        self.metric_extractor = MetricExtractor()

    def extract_kpi(self, text):

        pattern = r"(20\d{2})年.*?(\d+\.?\d*)\s*(噸|萬立方米|萬元)"
        matches = re.findall(pattern, text)

        data = []

        for year, value, unit in matches:
            data.append({
                "year": int(year),
                "value": float(value),
                "unit": unit
            })

        return data

    def generate(self, query, matches, company=None, mode="structured"):

        if not matches:
            return "找不到相關資料"

        top = matches[0]
        text = top["text"]
        source = top.get("source", "")

        # 抽 KPI
        kpis = self.extract_kpi(text)

        kpi_text = ""
        if len(kpis) >= 2:
            y1, y2 = kpis[0], kpis[1]
            change = y2["value"] - y1["value"]
            pct = (change / y1["value"]) * 100

            kpi_text = f"""
數據：
{y1['year']}：{y1['value']} {y1['unit']}
{y2['year']}：{y2['value']} {y2['unit']}
變化：{change} {y1['unit']} ({pct:.1f}%)
"""

        answer = f"""公司：{company}

重點內容：
{text}
{kpi_text}

資料來源：
{source}
"""

        return answer
