class InsightEngine:

    def build(self, data, mode="insight"):
        """
        data 結構：
        {
          "company": str,
          "metrics": {
              "carbon": {2023: ..., 2024: ...},
              "injury_rate": {...},
              ...
          }
        }
        """

        company = data.get("company")
        metrics = data.get("metrics", {})

        if mode == "evidence":
            return self._evidence(company, metrics)

        elif mode == "speculation":
            return self._speculation(company, metrics)

        else:
            return self._insight(company, metrics)

    def _evidence(self, company, metrics):
        lines = [f"公司：{company}", "（僅列出客觀數據）"]

        for k, v in metrics.items():
            if isinstance(v, dict):
                items = [f"{y}:{val}" for y, val in v.items()]
                lines.append(f"- {k}: " + ", ".join(items))

        return "\n".join(lines)

    def _insight(self, company, metrics):
        lines = [f"公司：{company}", "（數據 + 解讀）"]

        for k, v in metrics.items():
            if isinstance(v, dict) and len(v) >= 2:
                years = sorted(v.keys())
                y1, y2 = years[0], years[-1]
                val1, val2 = v[y1], v[y2]

                change = val2 - val1

                trend = "上升" if change > 0 else "下降"

                lines.append(
                    f"- {k}: {y1}→{y2} {trend}（{val1}→{val2}）"
                )

        return "\n".join(lines)

    def _speculation(self, company, metrics):

        lines = [f"公司：{company}", "（前瞻推論）"]

        carbon = metrics.get("carbon")
        injury = metrics.get("injury_rate")

        if carbon and injury:

            years = sorted(carbon.keys())
            y1, y2 = years[0], years[-1]

            carbon_change = carbon[y2] - carbon[y1]
            injury_change = injury[y2] - injury[y1]

            # 減碳 + 工傷上升
            if carbon_change < 0 and injury_change > 0:
                lines.append("觀察：減碳與工傷上升同時發生")

                lines.append("潛在影響：")
                lines.append("- 生產效率可能下降")
                lines.append("- 營運中斷風險上升")
                lines.append("- 交期穩定性需關注")

                lines.append("投資意涵：")
                lines.append("短期營收與毛利可能承壓")

        return "\n".join(lines)