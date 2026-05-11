import json

class IndexLoader:

    def load(self, path="app/index/document_store.json"):

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []