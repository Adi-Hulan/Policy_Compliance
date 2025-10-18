from graphs.company_policies import build_company_policy_graph
import uuid


class MockChatRepository:
    def get_messages(self, session_id):
        # Return an empty history to avoid database dependency during tests
        return []


if __name__ == '__main__':
    session_id = str(uuid.uuid4())
    message = 'What is the company PTO policy?'

    # Build the graph and invoke it directly with the expected state fields
    app = build_company_policy_graph()
    initial_state = {
        'session_id': session_id,
        'user_id': 'tester',
        'message': message,
        'document_url': None,
        'intent': 'company_policy_query',
        'chat_repository': MockChatRepository(),
    }

    import asyncio

    async def run_graph():
        final = await app.ainvoke(initial_state)
        return final

    final_state = asyncio.run(run_graph())

    print('\n--- FINAL RESPONSE START ---')
    try:
        print(final_state.response)
    except Exception:
        print(final_state.get('response'))
    print('--- FINAL RESPONSE END ---')
