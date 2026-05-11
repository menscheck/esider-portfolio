class EvidenceFormatter:
    """為 ESG 從業人員提供格式化的證據聚合"""

    def format(self, company, tag, matches):
        """
        格式化證據，方便複製貼上到報告或問卷
        
        Args:
            company: 公司名稱
            tag: 主題標籤
            matches: 相關的文本段落列表 (chunk list)
        
        Returns:
            格式化的證據字符串
        """
        lines = []

        lines.append(f"【主題】{tag}")
        lines.append(f"【公司】{company}")
        lines.append("")

        # 整理與排版證據
        for idx, match in enumerate(matches, 1):
            lines.append(f"【證據{idx}】")
            lines.append(match["text"])
            lines.append("")

        # 來源：假設來源是從最後一個 match 中取得，或合併所有來源
        if matches:
            sources = [match.get("source", "") for match in matches if match.get("source")]
            if sources:
                lines.append("【來源】")
                lines.append(", ".join(set(sources)))  # 去重並合併

        return "\n".join(lines)

    def format_multi_tags(self, company, tags_chunks_map):
        """
        格式化多個標籤的證據
        
        Args:
            company: 公司名稱
            tags_chunks_map: dict of {tag: [chunks]}
        
        Returns:
            格式化的完整證據報告
        """
        sections = []

        for tag, chunks in tags_chunks_map.items():
            sections.append(self.format(company, tag, chunks))
            sections.append("\n" + "="*60 + "\n")

        return "\n".join(sections)
