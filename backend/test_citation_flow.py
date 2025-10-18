#!/usr/bin/env python3
"""
Simple test to check citation flow between nodes without LLM calls.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from graphs.nodes.shared.claim_validator import claim_validator_node
from graphs.nodes.shared.session_update import session_update_node
from graphs.nodes.shared.output import output_node
from graphs.nodes.models import CompanyPolicyState
from db.repositories.chat_repository import ChatRepository

import uuid

def test_citation_flow():
    """Test citation flow between claim_validator -> session_update -> output_node"""

    print("=" * 80)
    print("🧪 TESTING CITATION FLOW BETWEEN NODES")
    print("=" * 80)

    # Mock data
    mock_response = """
    According to company policy, employees are entitled to 15 days of paid time off annually.
    The training program requires all new hires to complete safety training within 30 days.
    Performance reviews are conducted quarterly and include salary adjustments.
    """

    mock_policy_chunks = [
        {
            "id": "policy_chunk_1",
            "content": "Employees receive 15 days of PTO annually, prorated for new hires.",
            "similarity_score": 0.95,
            "confidence": "high",
            "page": 1,
            "file_path": "/policies/hr_policy.pdf",
            "document_text": "Employees receive 15 days of PTO annually, prorated for new hires. All employees must complete mandatory safety training within 30 days of hire."
        },
        {
            "id": "policy_chunk_2",
            "content": "All employees must complete mandatory safety training within 30 days of hire.",
            "similarity_score": 0.88,
            "confidence": "high",
            "page": 2,
            "file_path": "/policies/hr_policy.pdf",
            "document_text": "Employees receive 15 days of PTO annually, prorated for new hires. All employees must complete mandatory safety training within 30 days of hire."
        }
    ]

    mock_doc_chunks = [
        {
            "id": "doc_chunk_1",
            "content": "Performance reviews occur every quarter with potential salary increases.",
            "similarity_score": 0.92,
            "confidence": "high",
            "page": 1,
            "file_path": "/uploads/employee_handbook.pdf",
            "document_text": "Performance reviews occur every quarter with potential salary increases."
        }
    ]

    # Create mock state with valid UUID
    test_session_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    state = CompanyPolicyState(
        session_id=test_session_id,
        user_id=test_user_id,
        message="What are the PTO and training policies?",
        response=mock_response,
        policy_chunks_with_metadata=mock_policy_chunks,
        doc_chunks_with_metadata=mock_doc_chunks,
        chat_repository=ChatRepository(),
        intent="company_policy"
    )

    print("📝 Initial state:")
    print(f"   Response length: {len(state.response)} chars")
    print(f"   Policy chunks: {len(mock_policy_chunks)}")
    print(f"   Doc chunks: {len(mock_doc_chunks)}")

    try:
        # 1. Call claim validator
        print("\n🔍 Step 1: Calling claim_validator_node...")
        validated_state = claim_validator_node(state)
        print("✅ Claim validator completed")

        # Check what it returned
        citation_metadata = validated_state.get('citation_metadata', [])
        validation_metrics = validated_state.get('validation_metrics', {})
        response_with_citations = validated_state.get('response', '')

        print(f"   Citations generated: {len(citation_metadata)}")
        print(f"   Validation metrics: {validation_metrics}")
        print(f"   Response has citations: {'[1]' in response_with_citations or '[2]' in response_with_citations}")

        # Assert document_info fields are populated
        for citation in citation_metadata:
            assert 'document_info' in citation, "Missing document_info in citation"
            doc_info = citation['document_info']
            print(f"[DEBUG] Document Info: {doc_info}")
            assert doc_info['file_path'] is not None, "file_path is None in document_info"
            assert doc_info['char_start'] is not None, "char_start is None in document_info"
            assert doc_info['char_end'] is not None, "char_end is None in document_info"

        # Update state with validator results
        state.response = response_with_citations
        state.citation_metadata = citation_metadata
        state.validation_recommendations = validation_metrics

        # 2. Call session update
        print("\n💾 Step 2: Calling session_update_node...")
        session_state = session_update_node(state)
        print("✅ Session update completed")

        # Check what it preserved
        preserved_citations = session_state.get('citation_metadata', [])
        print(f"   Citations preserved: {len(preserved_citations)}")

                # Update state with session results
        # Convert state to dict, merge, then back to state
        state_dict = state.model_dump()
        state_dict.update(session_state)
        # Set final flag AFTER merge to ensure it overrides any value from session_state
        state_dict['final'] = True
        print(f"   Final flag in state_dict after setting: {state_dict.get('final', False)}")
        state = CompanyPolicyState(**state_dict)
        print(f"   Final flag in CompanyPolicyState: {getattr(state, 'final', False)}")

        # 3. Call output node
        # Create a dict version of state with final=True for output processing
        output_state_dict = state.model_dump()
        output_state_dict['final'] = True
        print(f"   Output state dict citation_metadata: {len(output_state_dict.get('citation_metadata', []))}")
        print(f"   Citation metadata sample: {output_state_dict.get('citation_metadata', [])[:1] if output_state_dict.get('citation_metadata') else 'None'}")
        final_output = output_node(output_state_dict)
        print("✅ Output node completed")

        # Check final output
        content = final_output.get('content', '')
        history = final_output.get('history', [])
        citations = final_output.get('citations', [])
        citation_metadata_final = final_output.get('citation_metadata', [])
        validation_recommendations_final = final_output.get('validation_recommendations', {})

        print("\n📊 FINAL OUTPUT:")
        print(f"   Content length: {len(content)} chars")
        print(f"   History items: {len(history)}")
        print(f"   Citations: {len(citations)}")
        print(f"   Citation metadata: {len(citation_metadata_final)}")
        print(f"   Validation recommendations: {bool(validation_recommendations_final)}")

        # Show sample citation metadata
        if citation_metadata_final:
            print("\n📋 Sample citation metadata:")
            for i, citation in enumerate(citation_metadata_final[:2]):
                print(f"  {i+1}. Claim: {citation.get('claim', '')[:50]}...")
                print(f"     Confidence: {citation.get('confidence', 'unknown')}")
                print(f"     Citation number: {citation.get('citation_number', 'unknown')}")

        # Check if citations are in the content
        citation_markers = []
        import re
        for match in re.finditer(r'\[(\d+)\]', content):
            citation_markers.append(match.group(1))

        print(f"\n🔗 Citation markers in content: {citation_markers}")

        print("\n✅ CITATION FLOW TEST COMPLETED")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_citation_flow()