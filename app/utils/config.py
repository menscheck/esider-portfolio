import configparser
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.ini"


def get_azure_config() -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(_CONFIG_PATH, encoding="utf-8")
    section = "azure_openai_chat"
    return {
        "api_key": cfg.get(section, "api_key"),
        "endpoint": cfg.get(section, "endpoint"),
        "deployment": cfg.get(section, "deployment"),
        "api_version": cfg.get(section, "api_version"),
    }


def get_azure_embedding_config() -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(_CONFIG_PATH, encoding="utf-8")
    section = "azure_openai_embedding"
    return {
        "api_key": cfg.get(section, "api_key"),
        "endpoint": cfg.get(section, "endpoint"),
        "deployment": cfg.get(section, "deployment"),
        "api_version": cfg.get(section, "api_version"),
    }
