"""
International LLM node

Provides the `international_policy_llm_node` used by the international policy graph.
This moves the LLM wrapper out of the graph module so nodes live with other international nodes.
"""
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from utils.prompts import MAIN_PROMPT


# Simple dedicated LLM instance for international policy node (uses same model by default)
_INTERNATIONAL_LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    streaming=True,
)


async def international_policy_llm_node(state):
    """Generate a direct LLM response for international policy queries.

    This node does not delegate to the shared LLM node and returns a dict
    compatible with the graph's expected LLM output: {'response': str, 'final': True}
    """
    INTERNATIONAL_POLICY_PROMPT = f"""{MAIN_PROMPT}

You are an expert compliance consultant specializing in international regulations and standards. Your expertise includes:

INTERNATIONAL REGULATIONS:
- GDPR (General Data Protection Regulation) - EU data protection
- HIPAA (Health Insurance Portability and Accountability Act) - US healthcare data
- SOX (Sarbanes-Oxley Act) - US financial reporting
- ISO 27001 - Information security management
- CCPA (California Consumer Privacy Act) - US state privacy law
- And other international compliance frameworks

When answering questions about international policies:
1. Always cite the specific regulation and relevant sections
2. Explain requirements clearly and practically
3. Note any regional variations or exceptions
4. Suggest implementation approaches when appropriate
5. Reference related policies or standards when relevant

Be precise, authoritative, and focused on compliance requirements."""

    # Prepare user message and history
    user_message = getattr(state, 'message', '') or ''
    history = getattr(state, 'history', []) or []

    # Build LangChain messages list
    langchain_messages: List[HumanMessage] = []
    # Prepend system prompt as first user message
    if INTERNATIONAL_POLICY_PROMPT:
        langchain_messages.append(HumanMessage(content=INTERNATIONAL_POLICY_PROMPT))
    # Append history converted to HumanMessage/AIMessage where appropriate
    for msg in (history or []):
        try:
            if hasattr(msg, 'content'):
                langchain_messages.append(HumanMessage(content=msg.content))
        except Exception:
            continue

    # Append current user question
    langchain_messages.append(HumanMessage(content=user_message))

    try:
        # Streaming call to the model
        full_response = ""
        async for chunk in _INTERNATIONAL_LLM.astream(langchain_messages):
            token = chunk.content or ""
            if token:
                full_response += token

        # Return response and content fields to ensure downstream nodes (session_update)
        # have the expected keys available on the state.
        return {"response": full_response, "content": full_response, "citation_metadata": [], "final": True}
    except Exception as e:
        print(f"[INTERNATIONAL_LLM] Error invoking LLM: {e}")
        import traceback
        traceback.print_exc()
        return {"response": "The international policy assistant is temporarily unavailable.", "content": "The international policy assistant is temporarily unavailable.", "citation_metadata": [], "final": True}
