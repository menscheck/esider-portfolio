from app.services.llm_service import generate_esg_summary

def llm_score(context: str):
    prompt = f"""
You are an ESG analyst. Based on the context, return JSON:

{{
 "E": {{"score": 0-10, "reason": "..."}},
 "S": {{"score": 0-10, "reason": "..."}},
 "G": {{"score": 0-10, "reason": "..."}}
}}

Context:
{context[:4000]}
"""

    out = generate_esg_summary({"prompt": prompt})

    # 最小容錯（實務可用 pydantic/regex）
    import json
    try:
        # Strip markdown code blocks if the LLM wraps the JSON
        if out.startswith("```json"):
            out = out[7:]
        if out.startswith("```"):
            out = out[3:]
        if out.endswith("```"):
            out = out[:-3]
        return json.loads(out.strip())
    except:
        return {
            "E": {"score": 5, "reason": "fallback"},
            "S": {"score": 5, "reason": "fallback"},
            "G": {"score": 5, "reason": "fallback"},
        }