"""
Shared LLM Node

Generates response using LLM with configurable prompt and message source.
Used by both company policy and general purpose graphs.
"""

from typing import Dict, Any, List
import asyncio
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re
from graphs.nodes.models import LLMNodeInput, LLMNodeOutput


# Shared LLM instance
_LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    streaming=True,  # Enable streaming for LangGraph event capture
)


async def llm_node(state: Dict[str, Any], system_prompt: str, message_key: str = "message") -> Dict[str, Any]:
    """
    Generate response using LLM and return final result with citations.
    Streaming is handled by LangGraph event system.
    """
    print(f"[LLM_NODE] ENTERING LLM NODE", flush=True)
    print(f"[LLM_NODE] State type: {type(state)}", flush=True)
    print(f"[LLM_NODE] Message key: {message_key}", flush=True)
    print(f"[LLM_NODE] Has message_key in state: {hasattr(state, message_key)}", flush=True)
    if hasattr(state, message_key):
        print(f"[LLM_NODE] Message content length: {len(getattr(state, message_key, ''))}", flush=True)
    
    # Validate inputs using Pydantic model
    try:
        input_data = LLMNodeInput(
            message=getattr(state, message_key, state.message),
            history=getattr(state, 'history', []) or [],
            system_prompt=system_prompt,
            message_key=message_key
        )
    except Exception as e:
        raise ValueError(f"LLM input validation failed: {e}")

    message = input_data.message
    history = input_data.history

    print(f"[LLM_NODE] Generating response", flush=True)
    print(f"[LLM_NODE] History length: {len(history)} messages", flush=True)
    print(f"[LLM_NODE] Message length: {len(message)} chars", flush=True)
    print(f"[LLM_NODE] Using message key: {input_data.message_key}", flush=True)

    try:
        # Convert LangChain messages to LangChain dict format
        def convert_message(msg):
            if isinstance(msg, SystemMessage):
                # System messages are not directly supported, merge with next user message
                return None
            elif isinstance(msg, HumanMessage):
                return {"role": "user", "content": msg.content}
            elif isinstance(msg, AIMessage):
                return {"role": "assistant", "content": msg.content}
            else:
                return None

        # Build conversation, merging system prompt with first user message
        google_messages = []
        pending_system = input_data.system_prompt
        
        for msg in history + [HumanMessage(content=message)]:
            converted = convert_message(msg)
            if converted:
                if pending_system and converted["role"] == "user":
                    # Merge system prompt with first user message
                    converted["content"] = f"{pending_system}\n\n{converted['content']}"
                    pending_system = None
                google_messages.append(converted)

        # If no user message to merge with, add system as first user message
        if pending_system:
            google_messages.insert(0, {"role": "user", "content": pending_system})

        print(f"[LLM_NODE] Total conversation: {len(google_messages)} messages")
        print("[LLM_NODE] Invoking LLM with streaming...")
        print(f"[LLM_NODE] First message content preview: {google_messages[0]['content'][:200]}...")

        # Convert dict messages back to LangChain format for streaming
        langchain_messages = []
        for msg in google_messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        print(f"[LLM_NODE] Converted to {len(langchain_messages)} LangChain messages")

        # Use asyncio.run to handle the async LLM call
        async def get_llm_response():
            full_response_with_citations = ""
            chunk_count = 0

            async for chunk in _LLM.astream(langchain_messages):
                chunk_count += 1
                token = chunk.content or ""
                print(f"[LLM_NODE] Received chunk #{chunk_count}: '{token}'")

                if token:
                    # Accumulate full response with citations
                    full_response_with_citations += token

            return full_response_with_citations

        full_response_with_citations = await get_llm_response()

        print(f"[LLM_NODE] ✓ Response with citations length: {len(full_response_with_citations)} chars")

        # Return final result with citations for output node processing
        return {
            "response": full_response_with_citations,
            "final": True  # Mark this as the final result
        }

    except Exception as e:
        print(f"[LLM_NODE] ✗ LLM invocation failed: {e}")
        import traceback
        traceback.print_exc()
        fallback = "I'm temporarily unavailable to generate a detailed answer, but I've recorded your question."
        return {"response": fallback}