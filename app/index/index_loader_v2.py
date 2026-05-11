import json


class IndexLoaderV2:

    def load(self, path="app/index/esg_index.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
