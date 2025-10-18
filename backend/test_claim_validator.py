#!/usr/bin/env python3
"""
Test script for claim validator node
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graphs.nodes.shared.claim_validator import claim_validator_node
from graphs.nodes.models import ClaimValidatorNodeInput, ClaimValidatorNodeOutput

# Mock state object
class MockState:
    def __init__(self, response, policy_chunks, doc_chunks):
        self.response = response
        self.policy_chunks_with_metadata = policy_chunks
        self.doc_chunks_with_metadata = doc_chunks

def test_claim_validator():
    print("🧪 Testing Claim Validator Node")
    print("=" * 50)

    # Test LLM response with claims
    test_response = """
    Based on the company policies, employees are entitled to 15 days of paid time off annually. The training budget is $2,000 per employee. All employees must complete safety training within 30 days of hire. The company provides health insurance benefits to full-time staff.
    """

    # Test policy chunks with metadata
    policy_chunks = [
        {
            'id': 'policy_1',
            'content': 'Employees are entitled to 15 days of paid time off (PTO) annually. This includes vacation days and sick leave.',
            'file_path': '/docs/company_policies.pdf',
            'char_start': 100,
            'char_end': 180,
            'page': 1,
            'source': 'policy'
        },
        {
            'id': 'policy_2',
            'content': 'The company provides a training budget of $2,000 per employee for professional development.',
            'file_path': '/docs/company_policies.pdf',
            'char_start': 200,
            'char_end': 280,
            'page': 2,
            'source': 'policy'
        },
        {
            'id': 'policy_3',
            'content': 'All employees must complete mandatory safety training within 30 days of their hire date.',
            'file_path': '/docs/company_policies.pdf',
            'char_start': 300,
            'char_end': 380,
            'page': 3,
            'source': 'policy'
        }
    ]

    # Test document chunks (some with metadata, some without)
    doc_chunks = [
        {
            'id': 'doc_1',
            'content': 'The company offers comprehensive health insurance benefits to all full-time employees.',
            'file_path': '/docs/benefits_guide.pdf',
            'char_start': 50,
            'char_end': 130,
            'page': 1,
            'source': 'document'
        },
        {
            'id': 'temp_doc_1',
            'content': 'Temporary document content without proper metadata for testing.',
            'source': 'document'
            # Missing file_path, char_start, char_end, page
        }
    ]

    # Create mock state
    state = MockState(test_response, policy_chunks, doc_chunks)

    print("📝 Test Input:")
    print(f"Response: {test_response.strip()}")
    print(f"Policy chunks: {len(policy_chunks)}")
    print(f"Doc chunks: {len(doc_chunks)}")
    print()

    try:
        # Call the claim validator
        result = claim_validator_node(state)

        print("✅ Claim Validator Output:")
        print("=" * 30)

        print("📄 Response with citations:")
        print(result['response'])
        print()

        print("📊 Citation Metadata:")
        for i, citation in enumerate(result.get('citation_metadata', [])):
            print(f"  [{i+1}] Claim: {citation.get('claim', '')[:60]}...")
            print(f"      Confidence: {citation.get('confidence', 'N/A')}")
            print(f"      Source: {citation.get('source', 'N/A')}")
            print(f"      Has metadata: {bool(citation.get('document_info', {}).get('file_path'))}")
            if citation.get('document_info'):
                print(f"      File: {citation['document_info'].get('file_path', 'N/A')}")
            print()

        print("📈 Validation Metrics:")
        metrics = result.get('validation_metrics', {})
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        print()

        # Test what event formatter would receive
        print("🎯 Event Formatter Input Preview:")
        print("=" * 30)
        print("The event formatter would receive this data structure:")
        print("- response: (string with [1], [2], etc. citation markers)")
        print("- citation_metadata: (list of citation objects)")
        print("- documents: (would be collected from citations with metadata)")

        # Show what documents would be collected
        documents = []
        for citation in result.get('citation_metadata', []):
            if citation.get('document_info', {}).get('file_path'):
                doc_info = citation['document_info']
                doc = {
                    'id': f"{citation.get('source', 'unknown')}_{doc_info['file_path']}",
                    'title': os.path.basename(doc_info['file_path']),
                    'url': doc_info['file_path'],
                    'type': citation.get('source', 'unknown'),
                    'file_path': doc_info['file_path']
                }
                if doc not in documents:
                    documents.append(doc)

        print(f"📚 Documents collected: {len(documents)}")
        for doc in documents:
            print(f"  - {doc['title']} ({doc['type']})")

        return result

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_claim_validator()