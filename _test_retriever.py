from app.core.retriever import ESGRetriever
r = ESGRetriever()

test_cases = [
    ('聯詠', '第三方確信'),
    ('聯詠', '環境績效量化'),
    ('鴻海', '確信範圍'),
    ('鴻海', 'ESG報告標準'),
    ('台積電', '環境績效量化'),
]

for company, query in test_cases:
    results = r.search(query, company=company, top_k=3)
    print(f'\n=== {company} / {query} ===')
    print(f'找到 {len(results)} 筆')
    for c in results:
        score = c.get('score', 'N/A')
        score_str = f'{score:.3f}' if isinstance(score, float) else str(score)
        print(f'  page={c.get("page")}, score={score_str}, text={c.get("text","")[:60]}')
