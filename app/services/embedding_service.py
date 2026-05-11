import configparser
from openai import AzureOpenAI

# 讀 config
config = configparser.ConfigParser()
config.read("config.ini")

# 讀 embedding 設定
cfg = config["azure_openai_embedding"]

# 初始化 client
client = AzureOpenAI(
    api_key=cfg["api_key"],
    api_version=cfg["api_version"],
    azure_endpoint=cfg["endpoint"]
)

deployment = cfg["deployment"]


def embed_text(text: str):
    """
    將文字轉成 embedding vector
    """
    response = client.embeddings.create(
        input=text,
        model=deployment
    )
    return response.data[0].embedding