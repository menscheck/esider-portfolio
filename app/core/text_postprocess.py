import re


# 所有需要被清除的來源標註 pattern
_REMOVE_PATTERNS = [
    # ①②③④⑤ 等圓圈數字符號（行首、句中、句尾、括號前）
    r'[①②③④⑤⑥⑦⑧⑨⑩]\s*\([^)]*\)',   # ④(任何內容) → 整個移除
    r'[①②③④⑤⑥⑦⑧⑨⑩]\s*$',           # 句尾單獨的 ④
    r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*',           # 行首的 ①
    r'[①②③④⑤⑥⑦⑧⑨⑩]',              # 剩餘所有圓圈數字

    # (2024-p.任何內容) 各種變體
    r'\(2024-p\.[^)]*\)',
    r'\(ESG2024-p\.[^)]*\)',

    # (來源：任何內容)
    r'\(來源：[^)]*\)',

    # (台股即時資訊) 或 (台股即時)
    r'\(台股即時[^)]*\)',
]


def fix_source_annotation(text: str) -> str:
    """強制清除 LLM 回答中所有來源標註格式"""

    for pattern in _REMOVE_PATTERNS:
        if pattern.startswith('^') or pattern.endswith('$'):
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        else:
            text = re.sub(pattern, '', text)

    # 清理多餘空白和空行
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def fix_finmind_annotations(answer: str, has_esg_chunks: bool) -> str:
    """台股回答：直接清除所有來源標註（已在 fix_source_annotation 處理）"""
    return fix_source_annotation(answer)


def fix_finmind_only_annotations(answer: str) -> str:
    return fix_source_annotation(answer)
