from openai import OpenAI

client = OpenAI(
    api_key="test",
    base_url="http://localhost:1234/v1"
)

response = client.chat.completions.create(
    model="qwen2.5-7b-instruct",
    messages=[{"role": "user", "content": "請回覆OK"}],
    temperature=0
)

print(response.choices[0].message.content)