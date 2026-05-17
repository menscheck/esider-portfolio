import sys
sys.path.insert(0, ".")

from app.core.retriever import ESGRetriever

r = ESGRetriever()

print("FAISS向量數:", r.index.ntotal)
print("id_map長度:", len(r.id_map))
print("MongoDB chunks:", r.collection.count_documents({}))

results = r.search("碳排放", top_k=3)
print("搜尋結果筆數:", len(results))
if results:
    for res in results:
        print(res["company"], res["page"], res["score"])
        print(res["text"][:80])
        print("---")
