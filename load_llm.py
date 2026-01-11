from langchain_groq import ChatGroq


def llm(model: str) -> ChatGroq:
    return ChatGroq(
        model=model,
        temperature=0,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2,
        # other params...
    )
