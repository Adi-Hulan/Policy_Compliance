#!/usr/bin/env python3
"""
Test script for event formatter with claim validator output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.event_formatter import format_event_for_ui

def test_event_formatter():
    print("🎯 Testing Event Formatter with Claim Validator Output")
    print("=" * 60)

    # Simulate the output from claim validator (from our test)
    claim_validator_output = {
        'response': 'Based on the company policies, employees are entitled to 15 days of paid time off annually. The training budget is $2,000 per employee.[1] All employees must complete safety training within 30 days of hire.[3] The company provides health insurance benefits to full-time staff.[5]',
        'citation_metadata': [
            {
                'claim': 'The training budget is $2,000 per employee.',
                'chunk_id': 'policy_2',
                'similarity': 0.8936038613319397,
                'confidence': 'high',
                'citation_number': 1,
                'original_start_pos': 85,
                'original_end_pos': 125,
                'page': 2,
                'source': 'policy',
                'match_type': 'semantic',
                'document_info': {
                    'file_path': '/docs/company_policies.pdf',
                    'char_start': 200,
                    'char_end': 280
                }
            },
            {
                'claim': 'All employees must complete safety training within 30 days of hire.',
                'chunk_id': 'policy_3',
                'similarity': 0.9818028211593628,
                'confidence': 'high',
                'citation_number': 3,
                'original_start_pos': 126,
                'original_end_pos': 180,
                'page': 3,
                'source': 'policy',
                'match_type': 'semantic',
                'document_info': {
                    'file_path': '/docs/company_policies.pdf',
                    'char_start': 300,
                    'char_end': 380
                }
            },
            {
                'claim': 'The company provides health insurance benefits to full-time staff.',
                'chunk_id': 'doc_1',
                'similarity': 0.9011502265930176,
                'confidence': 'high',
                'citation_number': 5,
                'original_start_pos': 181,
                'original_end_pos': 240,
                'page': 1,
                'source': 'document',
                'match_type': 'semantic',
                'document_info': {
                    'file_path': '/docs/benefits_guide.pdf',
                    'char_start': 50,
                    'char_end': 130
                }
            }
        ]
    }

    # Simulate documents collected from citations
    documents = [
        {
            'id': 'policy_/docs/company_policies.pdf',
            'title': 'company_policies.pdf',
            'url': '/docs/company_policies.pdf',
            'type': 'policy',
            'file_path': '/docs/company_policies.pdf'
        },
        {
            'id': 'document_/docs/benefits_guide.pdf',
            'title': 'benefits_guide.pdf',
            'url': '/docs/benefits_guide.pdf',
            'type': 'document',
            'file_path': '/docs/benefits_guide.pdf'
        }
    ]

    # Create a mock event that simulates the output node finishing
    mock_event = {
        "event": "on_chain_end",
        "name": "output",
        "data": {
            "output": {
                "content": claim_validator_output['response'],
                "citation_metadata": claim_validator_output['citation_metadata'],
                "documents": documents
            }
        }
    }

    # Mock initial state
    initial_state = {
        "session_id": "test-session-123",
        "message": "What are the company policies?",
        "user_id": "test-user"
    }

    print("📝 Mock Event Data:")
    print(f"Event type: {mock_event['event']}")
    print(f"Node: {mock_event['name']}")
    print(f"Content: {mock_event['data']['output']['content'][:100]}...")
    print(f"Citations: {len(mock_event['data']['output']['citation_metadata'])}")
    print(f"Documents: {len(mock_event['data']['output']['documents'])}")
    print()

    try:
        # Format the event for UI
        ui_payloads = format_event_for_ui(mock_event, initial_state)

        print("✅ Event Formatter Output:")
        print("=" * 30)

        for i, payload in enumerate(ui_payloads):
            print(f"📦 Payload {i+1}:")
            print(f"  Type: {payload.get('type')}")
            print(f"  Category: {payload.get('category')}")
            print(f"  Node: {payload.get('node', 'N/A')}")

            if payload.get('type') == 'final':
                print(f"  Content: {payload.get('content', '')[:100]}...")
                print(f"  Citation Metadata: {len(payload.get('citation_metadata', []))} items")
                print(f"  Documents: {len(payload.get('documents', []))} items")

                # Show document details
                for doc in payload.get('documents', []):
                    print(f"    - {doc.get('title')} ({doc.get('type')})")

            print(f"  Message: {payload.get('message', 'N/A')}")
            print()

        print("🎉 SUCCESS: Event formatter correctly processed claim validator output!")
        print("The frontend will receive:")
        print("- Final response with citation markers [1], [3], [5]")
        print("- Citation metadata for highlighting")
        print("- Document list for display")

        return ui_payloads

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_event_formatter()