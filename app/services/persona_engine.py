class PersonaEngine:

    def generate(self, persona, company, tags, evidence):

        if persona == "investor":
            return self._investor(company, tags, evidence)

        elif persona == "job_seeker":
            return self._job(company, tags, evidence)

        elif persona == "internal":
            return self._internal(company, tags, evidence)

        else:
            return self._default(company, evidence)

    def _investor(self, company, tags, evidence):

        lines = [f"【投資觀點】{company}"]

        if "operational_risk" in tags:
            lines.append("營運穩定性需關注，可能影響交付與收入認列")

        if "cost_pressure" in tags:
            lines.append("成本結構可能上升，壓縮毛利空間")

        lines.append("建議觀察：營收趨勢與毛利率變化")

        return "\n".join(lines)

    def _job(self, company, tags, evidence):

        lines = [f"【職場觀點】{company}"]

        if "leave_policy" in tags:
            lines.append("請假制度與休息權益需特別留意")

        if "work_hours" in tags:
            lines.append("可能存在工時壓力，建議面試時確認")

        if "benefits" in tags:
            lines.append("福利制度需進一步了解實際落地情況")

        return "\n".join(lines)

    def _internal(self, company, tags, evidence):

        lines = [f"【管理建議】{company}"]

        if "gap" in tags:
            lines.append("部分關鍵指標未揭露，需補強資訊透明度")

        if "operational_risk" in tags:
            lines.append("營運風險與人力配置需重新評估")

        if "work_hours" in tags:
            lines.append("可能反映人力不足，需檢視人力規劃")

        return "\n".join(lines)

    def _default(self, company, evidence):

        return f"{company}資料整理完成"
