import os
import json
from app.services.text_chunker import TextChunker
from app.services.tagger import Tagger


class IndexBuilderV2:

    def __init__(self):
        self.chunker = TextChunker()
        self.tagger = Tagger()

    def build(self, folder="reports", output="app/index/esg_index.json"):
        store = []

        for file in os.listdir(folder):
            if not file.endswith(".txt"):
                continue

            path = os.path.join(folder, file)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self.chunker.chunk(content)

            for c in chunks:
                tags = self.tagger.tag(c)

                if not tags:
                    tags = ["_untagged"]

                store.append({
                    "text": c,
                    "tags": tags,
                    "source": file,
                    "company": file.split(".")[0]
                })

        with open(output, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)

        print("Index built:", len(store))

