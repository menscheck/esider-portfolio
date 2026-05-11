from app.core.tag_rules import TAG_RULES


class Tagger:

    def tag(self, text):
        tags = []

        for tag, keywords in TAG_RULES.items():
            for kw in keywords:
                if kw in text:
                    tags.append(tag)
                    break

        return list(set(tags))
