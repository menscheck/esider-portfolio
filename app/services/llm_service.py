from openai import AzureOpenAI
import configparser
import os

# Use specific configuration for LLM Chat services
config = configparser.ConfigParser()
if not os.path.exists("config.ini"):
    raise FileNotFoundError("Configuration file 'config.ini' not found.")
config.read("config.ini")

# Backward/forward compatible section name
if "azure_openai_chat" in config:
    cfg_chat = config["azure_openai_chat"]
elif "azure_openai" in config:
    cfg_chat = config["azure_openai"]
else:
    raise KeyError("Missing [azure_openai_chat] or [azure_openai] section in config.ini")

client = AzureOpenAI(
    api_key=cfg_chat["api_key"],
    api_version="2023-05-15",
    azure_endpoint=cfg_chat["endpoint"]
)


def generate_esg_summary(input_data):
    # Extract prompt from dict if necessary, or use directly if string
    prompt = input_data["prompt"] if isinstance(input_data, dict) else input_data
    
    print("🔥 ENTER LLM FUNCTION")
    try:
        print("🚀 Calling Azure OpenAI...")
        response = client.chat.completions.create(
            model=cfg_chat["deployment"],  # ⚠️ Use the correct config variable for chat service
            messages=[
                {"role": "system", "content": "You are an ESG analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content

    except Exception as e:
        print("🔥 LLM ERROR:", str(e))
        return f"LLM Error: {str(e)}"
