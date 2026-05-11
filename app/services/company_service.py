import json


class CompanyService:
    def __init__(self):
        self.stopwords = self._load_json("report/stopwords.json")
        self.industry_words = self._load_json("report/industry_words.json")

    def _load_json(self, path):
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _load_company_list(self):
        try:
            import json
            with open("app/data/company_list.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading company_list: {e}")
            return []

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        return (
            text.replace("台", "臺")
            .lower()
            .strip()
        )

    def clean_query(self, query: str) -> str:
        text = self.normalize(query)

        # 移除 stop words
        for w in self.stopwords:
            if len(w) >= 2:
                text = text.replace(w.lower(), "")

        # 移除 industry words
        for w in self.industry_words:
            if len(w) >= 2:
                text = text.replace(w.lower(), "")

        return text.strip()

    def split_alias(self, alias: str):
        if not alias:
            return []
        return [a.strip() for a in alias.split() if a.strip()]

    def search(self, query: str, top_k: int = 5):
        query_norm = self.normalize(query)
        cleaned_query = self.clean_query(query)

        results = []
        _company_list = self._load_company_list()

        for c in _company_list:
            name = self.normalize(c.get("name", ""))
            alias_list = self.split_alias(c.get("alias", ""))
            code = c.get("code", "")

            score = 0

            # 股票代碼
            if code and code in query_norm:
                score += 120

            # 完整名稱 match
            if name and name in query_norm:
                score += 100

            # alias match（强）
            for a in alias_list:
                a_norm = self.normalize(a)
                if a_norm and a_norm in query_norm:
                    score += 90

            # cleaned query match（关键）
            if cleaned_query:
                if cleaned_query in name:
                    score += 80
                for a in alias_list:
                    if cleaned_query in self.normalize(a):
                        score += 70

            # partial overlap（防 typo / 简称）
            if cleaned_query and len(cleaned_query) >= 2:
                if any(ch in name for ch in cleaned_query):
                    score += 30

            if score > 0:
                results.append({
                    "code": code,
                    "name": c.get("name"),
                    "alias": c.get("alias"),
                    "score": score,
                })

        # 排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def extract_company(self, query: str):
        results = self.search(query, top_k=1)
        if not results:
            return None
        return results[0]


# Backward-compatible helper (esg_service.py expects this symbol)
def normalize_company(text: str) -> str:
    return CompanyService().normalize(text)


def get_company_service() -> CompanyService:
    """Compatibility for query_pipeline.py"""
    return CompanyService()
