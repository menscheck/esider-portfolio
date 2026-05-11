import os


class DocumentLoader:

    def load_reports(self, folder="reports"):
        docs = []

        if not os.path.exists(folder):
            return docs

        for file in os.listdir(folder):
            if file.endswith(".txt"):
                path = os.path.join(folder, file)

                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                docs.append({
                    "file": file,
                    "content": content
                })

        return docs
