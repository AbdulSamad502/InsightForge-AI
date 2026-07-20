from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

llm = ChatOllama(
    model="qwen3:8b",
    base_url="http://localhost:11434",
    temperature=0
)

response = llm.invoke([
    HumanMessage(content="Say only Hello.")
])

print(response.content)