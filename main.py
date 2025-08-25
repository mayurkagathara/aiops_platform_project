import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Create the custom ChatOpenAI instance for OpenRouter
openrouter_llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct:free",  # Replace with any OpenRouter model
    openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
    openai_api_base="phttps://openrouter.ai/api/v1",
)

messages = [
                (
                    "system",
                    "You are a funny assistant giving answer like a joke",
                ),
                ("human", "why sky is blue?"),
            ]

