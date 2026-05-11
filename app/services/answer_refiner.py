import re

class AnswerRefiner:

    def refine(self, answer: str) -> str:
        if not answer:
            return answer

        text = answer

        # 1) 移除重複空行與多餘空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)

        # 2) 統一標點（簡單處理）
        text = text.replace("：\n", "：\n")
        text = text.strip()

        return text