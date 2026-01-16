import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import nodes
from graphs.nodes.shared.history import history_node
from graphs.nodes.company_policy.policy_retriever import policy_retriever_node
from graphs.nodes.company_policy.document_retriever import document_retriever_node
from graphs.nodes.company_policy.context_combination import context_combination_node
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from utils.prompts import MAIN_PROMPT


# --- Mocks ---
class MockChatRepository:
    def __init__(self, messages):
        self._messages = messages
    def get_messages(self, session_id):
        return self._messages

class MockPolicyRetriever:
    def retrieve_chunks_with_citations(self, query, top_k=5):
        print(f"[MOCK_POLICY_RETRIEVER] query={query}")
        chunks = [
            {
                'id': 'policy_1',
                'content': 'Employees are entitled to 15 days PTO annually.',
                'char_start': 100,
                'char_end': 150,
                'file_path': '/docs/company_policies.pdf',
                'citation': {
                    'char_start': 100, 'char_end': 150, 'file_path': '/docs/company_policies.pdf'
                }
            }
        ]
        return {"status": "success", "chunks": chunks}

class MockTempRetriever:
    def retrieve_chunks(self, question, safe_session_id, top_k=5):
        print(f"[MOCK_TEMP_RETRIEVER] question={question}, session={safe_session_id}")
        chunks = [
            {
                'id': 'doc_1',
                'content': 'Temporary uploaded doc: company offers health insurance to full-time staff.',
                'char_start': 10,
                'char_end': 90,
                'file_path': f"/tmp/uploaded_{safe_session_id}.pdf"
            }
        ]
        return {"status": "success", "chunks": chunks}


# Fake llm_node to capture what would be passed to the real LLM
async def fake_llm_node(state, system_prompt, message_key="message"):
    # Reconstruct message and history similar to real llm_node
    message = getattr(state, message_key, state.message)
    history = getattr(state, 'history', []) or []

    print('\n--- FAKE LLM NODE INVOCATION ---')
    print('System prompt preview:', system_prompt[:200].replace('\n',' '))
    print('History messages count:', len(history))
    for i, m in enumerate(history):
        role = 'user' if isinstance(m, HumanMessage) else ('assistant' if isinstance(m, AIMessage) else 'system')
        print(f"  history[{i}] role={role} content_preview={m.content[:120]}")
    print('Message key:', message_key)
    print('Full user message preview:', getattr(state, message_key, '')[:500])
    print('--- END FAKE LLM INVOCATION ---\n')

    return {"response": "DUMMY RESPONSE", "final": True}


def run_pipeline():
    # Prepare fake history (as would be returned from DB)
    db_messages = [
        {'role': 'user', 'content': 'Hi, what is the PTO policy?'} ,
        {'role': 'assistant', 'content': 'Employees have 15 days PTO.'}
    ]

    # Create mock chat repo and state object
    from graphs.nodes.models import CompanyPolicyState
    class State(CompanyPolicyState):
        pass

    state = State(
        session_id='test-session-1',
        user_id='user-1',
        message='Can you confirm benefits and PTO?',
        document_url=None,
        intent='company_policy'
    )

    # Provide safe session id and tmp file path to satisfy node input validation
    state.safe_session_id = 'session_123'
    state.tmp_file_path = '/tmp/fake.pdf'

    # Attach mock chat repo so history_node uses it
    state.chat_repository = MockChatRepository(db_messages)

    # Monkeypatch retrievers
    import graphs.nodes.company_policy.policy_retriever as policy_module
    import graphs.nodes.company_policy.document_retriever as doc_module
    policy_module._policy_retriever = MockPolicyRetriever()
    doc_module._temp_retriever = MockTempRetriever()

    # We will call fake_llm_node directly later (avoid importing graphs.nodes.shared.llm which
    # may initialize external clients). No monkeypatch required.

    # 1. Load history
    history_out = history_node(state)
    state.history = history_out['history']

    # 2. Policy retrieval
    policy_out = policy_retriever_node(state)
    state.policy_context = policy_out.get('policy_context', [])
    state.policy_chunks_with_metadata = policy_out.get('policy_chunks_with_metadata', [])

    # 3. Document retrieval
    doc_out = document_retriever_node(state)
    # document_retriever_node may return a dict with doc_chunks_with_metadata
    if isinstance(doc_out, dict):
        state.doc_context = doc_out.get('doc_context', [])
        state.doc_chunks_with_metadata = doc_out.get('doc_chunks_with_metadata', [])
    else:
        state.doc_context = doc_out.get('doc_context', [])

    # 4. Context combination
    combo_out = context_combination_node(state)
    state.full_user_message = combo_out.get('full_user_message')
    state.chunk_metadata = combo_out.get('chunk_metadata')

    # 5. Call fake llm_node directly (avoid importing company_policies which pulls heavy deps)
    llm_result = asyncio.run(fake_llm_node(state, MAIN_PROMPT, "full_user_message"))
    print('LLM RESULT:', llm_result)


if __name__ == '__main__':
    run_pipeline()
