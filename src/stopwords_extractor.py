import jieba
from collections import Counter

def load_stopwords(file_path):
    stopwords = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            word = line.strip()
            if len(word) >= 2 and not word.isdigit():
                stopwords.add(word)
    return stopwords

def extract_stopwords(file_path):
    content = ''
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    words = jieba.lcut(content)
    counter = Counter(words)

    top_100_words = counter.most_common(100)
    stopwords = {word for word, _ in top_100_words}

    return list(stopwords)

stopwords = extract_stopwords('report/ESG_Questionaire300.txt')

with open('report/stopwords.json', 'w', encoding='utf-8') as file:
    import json
    json.dump(list(stopwords), file, ensure_ascii=False, indent=4)