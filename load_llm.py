from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=None,
    timeout=None,
    reasoning_format="parsed",
    max_retries=2,
    streaming=True,
)


if __name__ == "__main__":
    res = model.invoke("Hello, What's an llm?")
    res.pretty_print()
