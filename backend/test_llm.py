#!/usr/bin/env python3
"""
Test LLM directly
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    streaming=True,
)

messages = [HumanMessage(content="What is the company PTO policy?")]

print("Testing LLM directly...")
try:
    response = llm.invoke(messages)
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting streaming...")
try:
    for chunk in llm.stream(messages):
        print(f"Chunk: '{chunk.content}'")
except Exception as e:
    print(f"Streaming error: {e}")
    import traceback
    traceback.print_exc()