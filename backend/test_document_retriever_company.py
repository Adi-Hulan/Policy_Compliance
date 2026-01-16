from graphs.nodes.company_policy.document_retriever import document_retriever_node, _temp_retriever

class MockState:
    def __init__(self, message, tmp_file_path, safe_session_id):
        self.message = message
        self.tmp_file_path = tmp_file_path
        self.safe_session_id = safe_session_id

class MockTempRetriever:
    def retrieve_chunks(self, question, safe_session_id, top_k=5):
        print(f"[MOCK_TEMP_RETRIEVER] Called with question={question}, session={safe_session_id}")
        chunks = [
            {
                'id': 'doc_1',
                'content': 'This is a document chunk about health benefits.',
                'distance': 0.1,
                'char_start': 50,
                'char_end': 120,
                'page': 1,
                'file_path': '/tmp/benefits.pdf'
            },
            {
                'id': 'doc_2',
                'content': 'Temporary doc chunk without citation metadata.',
                'distance': 0.2,
                # intentionally missing file_path fields
            }
        ]
        return {'status': 'success', 'chunks': chunks}

# Monkeypatch the module-level retriever
import graphs.nodes.company_policy.document_retriever as module
module._temp_retriever = MockTempRetriever()

# Run test
state = MockState('What are benefits?', '/tmp/fake.pdf', 'session_123')
output = document_retriever_node(state)
print('\n=== OUTPUT ===')
print(output)
