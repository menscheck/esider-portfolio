import os
import json
import urllib.request
from typing import Optional


SAVE_DIR = "./report/2024"
MAP_PATH = "./report/company_report_map.json"


def _pick_report_url(company_name: str) -> Optional[str]:
    name = (company_name or "").strip()
    if not name:
        return None

    if not os.path.exists(MAP_PATH):
        return None

    try:
        with open(MAP_PATH, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception:
        return None

    # 1) exact key
    if name in mapping:
        return mapping[name]

    # 2) case-insensitive exact key
    lower_name = name.lower()
    for k, v in mapping.items():
        if str(k).lower() == lower_name:
            return v

    # 3) partial key match
    for k, v in mapping.items():
        if str(k) in name or name in str(k):
            return v

    # 4) partial case-insensitive
    for k, v in mapping.items():
        lk = str(k).lower()
        if lk in lower_name or lower_name in lk:
            return v

    return None


def download_report(company_name: str) -> Optional[str]:
    """
    Download sustainability report for the detected company.
    Returns local PDF path if successful, otherwise None.
    """
    url = _pick_report_url(company_name)
    if not url:
        return None

    os.makedirs(SAVE_DIR, exist_ok=True)
    safe_name = company_name.replace("/", "_").replace("\\", "_").strip() or "company"
    pdf_path = os.path.join(SAVE_DIR, f"{safe_name}.pdf")

    if os.path.exists(pdf_path):
        return pdf_path

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response, open(pdf_path, "wb") as out_file:
            out_file.write(response.read())
        return pdf_path
    except Exception:
        return None

