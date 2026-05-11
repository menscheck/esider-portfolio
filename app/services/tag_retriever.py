class TagRetriever:

    def search(self, tags, index, company=None):
        results = []

        for item in index:
            if company and company not in item.get("source", ""):
                continue

            score = 0

            for t in tags:
                if t in item["tags"]:
                    score += 1

            if score > 0:
                results.append({
                    "text": item["text"],
                    "score": score,
                    "tags": item["tags"],
                    "source": item["source"]
                })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:5]
