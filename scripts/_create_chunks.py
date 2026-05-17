#!/usr/bin/env python3
import os, json, re
from pathlib import Path

def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|]', '_', s)
    s = s.replace('\n',' ').strip()
    return s[:120]

BASE = Path(os.path.dirname(__file__))
json_path = BASE / 'project_memory.json'
out_dir = BASE / 'project_memory_chunks'
out_dir.mkdir(exist_ok=True)

if not json_path.exists():
    print('project_memory.json not found at', json_path)
    raise SystemExit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    docs = json.load(f)

created = []
for i, d in enumerate(docs, start=1):
    title = d.get('title') or f'doc_{i}'
    category = d.get('category','')
    fname = f"{i:02d}_{safe_name(category)}_{safe_name(title)}.txt"
    path = out_dir / fname
    header = f"Title: {title}\nCategory: {category}\nTags: {', '.join(d.get('tags', []))}\n\n"
    content = d.get('content','')
    with open(path, 'w', encoding='utf-8') as w:
        w.write(header + content)
    created.append(str(path))

print(f'Created {len(created)} files in {out_dir}')
for p in created:
    print(' -', p)
