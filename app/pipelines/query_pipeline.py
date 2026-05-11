from app.services.company_service import CompanyService
from app.services.intent_classifier import IntentClassifier
from app.services.document_loader import DocumentLoader
from app.services.text_chunker import TextChunker
from retriever import SimpleRetriever
from app.services.answer_generator import AnswerGenerator
from app.index.index_loader import IndexLoader
from app.services.answer_refiner import AnswerRefiner
from app.services.insight_engine import InsightEngine
from app.services.metric_extractor import MetricExtractor
from app.services.persona_engine import PersonaEngine
from app.services.evidence_formatter import EvidenceFormatter


class QueryPipeline:

    # Persona 優先級配置
    PERSONA_TAG_PRIORITY = {
        "investor": ["operational_risk", "cost_pressure", "margin_impact", "stability"],
        "job_seeker": ["leave_policy", "benefits", "salary", "work_hours"],
        "esg": ["gap", "missing", "conflict", "operational_risk"]  # ESG 從業人員
    }

    def __init__(self):
        self.company_service = CompanyService()
        self.intent_classifier = IntentClassifier()
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.retriever = SimpleRetriever()
        self.answer_generator = AnswerGenerator()
        self.index_loader = IndexLoader()
        self.index = self.index_loader.load()
        self.refiner = AnswerRefiner()
        self.insight_engine = InsightEngine()
        self.metric_extractor = MetricExtractor()
        self.persona_engine = PersonaEngine()
        self.evidence_formatter = EvidenceFormatter()

    def run(self, query: str, persona="investor", mode="insight"):

        company = self.company_service.extract_company(query)
        intent = self.intent_classifier.classify(query)

        search_query = query

        # 第一步：進行基本檢索
        matches = self.retriever.search(search_query, self.index)

        # 第二步：推導 tags（所有 persona 共用）
        metrics = {}
        for m in matches:
            extracted = self.metric_extractor.extract(m["text"])
            for k, v in extracted.items():
                metrics[k] = v

        tags = self._infer_tags(metrics, matches)

        company_name = company["name"] if company else "unknown"

        # ESG 從業人員模式：直接返回格式化的證據聚合
        if persona == "esg":
            # 收集所有相關標籤的證據
            tags_chunks_map = self._collect_evidence_by_tags(tags, matches)
            final_answer = self.evidence_formatter.format_multi_tags(company_name, tags_chunks_map)
            return {
                "query": query,
                "company": company,
                "intent": intent,
                "matches": matches,
                "tags": tags,
                "persona": persona,
                "answer": final_answer,
                "evidence_report": True  # 標記這是證據報告
            }

        # 第三步：根據 persona 優先級排序 matches
        sorted_matches = self._sort_matches_by_persona(matches, tags, persona)

        # 第四步：根據 persona 決定回答方式
        if persona in self.PERSONA_TAG_PRIORITY:
            # 使用 persona 引擎生成針對性答案
            final_answer = self.persona_engine.generate(persona, company_name, tags, sorted_matches)
        else:
            # 使用 insight_engine 的三模式（當 persona 無效或為 None）
            insight_data = {
                "company": company_name,
                "metrics": metrics
            }
            final_answer = self.insight_engine.build(insight_data, mode=mode)

        # 最後做安全潤飾
        answer = self.refiner.refine(final_answer)

        return {
            "query": query,
            "company": company,
            "intent": intent,
            "matches": sorted_matches,
            "tags": tags,
            "persona": persona,
            "answer": answer
        }

    def _infer_tags(self, metrics, matches):
        """從指標和內容推導相應的 tags"""
        tags = []

        # 根據指標推導
        if "carbon" in metrics and "injury_rate" in metrics:
            # 檢查是否有減碳但工傷上升
            carbon_vals = list(metrics["carbon"].values())
            injury_vals = list(metrics["injury_rate"].values())
            if len(carbon_vals) > 1 and len(injury_vals) > 1:
                if carbon_vals[-1] < carbon_vals[0] and injury_vals[-1] > injury_vals[0]:
                    tags.append("operational_risk")
                    tags.append("cost_pressure")
                    tags.append("margin_impact")
                    tags.append("stability")

        # 根據內容推導
        content = " ".join([m.get("text", "") for m in matches])
        if "薪酬" in content or "福利" in content:
            tags.append("benefits")
            tags.append("salary")
        if "工時" in content or "工傷" in content:
            tags.append("work_hours")
        if "離職" in content or "請假" in content:
            tags.append("leave_policy")
        if not content:
            tags.append("gap")
            tags.append("missing")

        return list(set(tags))  # 去重

    def _sort_matches_by_persona(self, matches, tags, persona):
        """根據 persona 優先級對 matches 進行排序"""
        
        if persona not in self.PERSONA_TAG_PRIORITY:
            return matches

        priority_tags = self.PERSONA_TAG_PRIORITY[persona]

        # 為每個 match 計算優先級分數
        def get_match_score(match):
            match_text = match.get("text", "")
            score = 0

            # 根據 match 中的 tag 匹配度計算分數
            for tag_idx, tag in enumerate(priority_tags):
                if tag in tags:
                    # 檢查 match text 是否包含相應的關鍵詞
                    tag_keywords = self._get_tag_keywords(tag)
                    match_count = sum(1 for kw in tag_keywords if kw in match_text)
                    if match_count > 0:
                        # 優先級越高的 tag（idx 越小）給予更高分數
                        score += (len(priority_tags) - tag_idx) * match_count

            return score

        # 按分數降序排序
        sorted_matches = sorted(matches, key=get_match_score, reverse=True)
        return sorted_matches

    def _get_tag_keywords(self, tag):
        """根據 tag 返回相應的關鍵詞"""
        keywords_map = {
            "operational_risk": ["工傷", "風險", "停工", "損失"],
            "cost_pressure": ["成本", "費用", "支出", "開銷"],
            "margin_impact": ["毛利", "利潤", "營收", "獲利"],
            "stability": ["穩定", "持續", "保障", "可靠"],
            "benefits": ["福利", "津貼", "保險", "獎金"],
            "salary": ["薪酬", "薪資", "薪水", "報酬"],
            "work_hours": ["工時", "工傷", "加班", "休息"],
            "leave_policy": ["請假", "休假", "離職", "調動"],
            "gap": ["缺陷", "缺少", "不足", "空白"],
            "missing": ["缺失", "未揭露", "未說明", "待補"],
            "conflict": ["矛盾", "衝突", "不一致", "差異"]
        }
        return keywords_map.get(tag, [tag])
