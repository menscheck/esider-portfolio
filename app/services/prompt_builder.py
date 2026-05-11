def build_esg_prompt(
    company: str,
    role: str,
    topic: str,
    structured_data: dict,
    documents: list[dict[str, str]],
) -> str:
    document_block = "\n".join(
        f"- [{doc['source']}] {doc['snippet']}" for doc in documents
    )
    return (
        "You are an ESG analysis assistant.\n"
        f"Company: {company}\n"
        f"User role: {role}\n"
        f"Topic: {topic}\n"
        f"Structured data: {structured_data}\n"
        "Retrieved context:\n"
        f"{document_block}\n"
        "Produce an investor-ready assessment with summary, metrics, risks, and highlights."
    )
