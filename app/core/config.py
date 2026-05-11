"""
app/core/config.py
統一設定讀取
"""
import configparser
from pathlib import Path

_config = None

def get_config() -> configparser.ConfigParser:
    global _config
    if _config is None:
        _config = configparser.ConfigParser()
        config_path = Path(__file__).parent.parent.parent / "config.ini"
        _config.read(config_path, encoding="utf-8")
    return _config