"""
Claim Validator Performance Evaluation

Evaluates the accuracy of claim extraction and hallucination detection
using precision, recall, and F1 score metrics.
"""

from ..graphs.nodes.shared.claim_validator import extract_claims, find_best_chunk_match
from typing import List, Dict, Any
import json


def evaluate_claim_validator(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate claim validator performance using ground truth test cases.

    Args:
        test_cases: List of test cases with responses, chunks, and expected matches

    Returns:
        Dict with performance metrics
    """
    results = {
        'total_claims': 0,
        'correct_matches': 0,
        'false_positives': 0,
        'false_negatives': 0,
        'precision': 0.0,
        'recall': 0.0,
        'f1_score': 0.0,
        'detailed_results': []
    }

    for test_case in test_cases:
        print(f'\n=== Evaluating: {test_case["name"]} ===')

        claims = extract_claims(test_case['response'])
        print(f'Extracted {len(claims)} claims from response')

        case_results = {
            'test_case': test_case['name'],
            'claims': []
        }

        for claim in claims:
            results['total_claims'] += 1

            match = find_best_chunk_match(claim, test_case['chunks'], threshold=0.5)
            expected_chunk = test_case['expected_matches'].get(claim)

            claim_result = {
                'claim': claim,
                'expected_chunk': expected_chunk,
                'matched_chunk': match['id'] if match else None,
                'similarity': match['similarity_score'] if match else 0.0,
                'correct': False,
                'false_positive': False,
                'false_negative': False
            }

            if match and expected_chunk:
                if match['id'] == expected_chunk:
                    results['correct_matches'] += 1
                    claim_result['correct'] = True
                    print(f'✅ CORRECT: "{claim[:50]}..." → {match["id"]}')
                else:
                    results['false_positives'] += 1
                    claim_result['false_positive'] = True
                    print(f'❌ WRONG MATCH: "{claim[:50]}..." → {match["id"]} (expected {expected_chunk})')
            elif match and not expected_chunk:
                results['false_positives'] += 1
                claim_result['false_positive'] = True
                print(f'❌ FALSE POSITIVE: "{claim[:50]}..." → {match["id"]} (should be no match)')
            elif not match and expected_chunk:
                results['false_negatives'] += 1
                claim_result['false_negative'] = True
                print(f'❌ MISSED: "{claim[:50]}..." (expected {expected_chunk})')
            else:
                print(f'✅ CORRECT NO MATCH: "{claim[:50]}..."')

            case_results['claims'].append(claim_result)

        results['detailed_results'].append(case_results)

    # Calculate metrics
    if results['total_claims'] > 0:
        predicted_positives = results['correct_matches'] + results['false_positives']
        actual_positives = results['correct_matches'] + results['false_negatives']

        results['precision'] = results['correct_matches'] / predicted_positives if predicted_positives > 0 else 0
        results['recall'] = results['correct_matches'] / actual_positives if actual_positives > 0 else 0
        results['f1_score'] = 2 * (results['precision'] * results['recall']) / (results['precision'] + results['recall']) if (results['precision'] + results['recall']) > 0 else 0

    return results


def run_evaluation():
    """Run the evaluation with predefined test cases."""

    # Ground truth test cases
    test_cases = [
        {
            'name': 'Compliance Training Policy',
            'response': 'All employees must complete annual compliance training by December 31st. The training covers data privacy and workplace safety. Failure to complete training results in disciplinary action.',
            'chunks': [
                {'content': 'All employees must complete annual compliance training by December 31st.', 'id': 'chunk_1', 'page': 12},
                {'content': 'Training covers data privacy, workplace safety, and harassment prevention.', 'id': 'chunk_2', 'page': 13},
                {'content': 'Failure to complete training may result in disciplinary action.', 'id': 'chunk_3', 'page': 14},
                {'content': 'Remote work is allowed with manager approval.', 'id': 'chunk_4', 'page': 20}  # Unrelated chunk
            ],
            'expected_matches': {
                'All employees must complete annual compliance training by December 31st': 'chunk_1',
                'The training covers data privacy and workplace safety': 'chunk_2',
                'Failure to complete training results in disciplinary action': 'chunk_3'
            }
        },
        {
            'name': 'Vacation Policy',
            'response': 'Employees accrue 10 days of paid time off annually. PTO requests require 2 weeks advance notice. Unused PTO carries over to the next year.',
            'chunks': [
                {'content': 'Employees accrue 10 PTO days annually, increasing to 15 after 5 years.', 'id': 'vacation_1', 'page': 25},
                {'content': 'PTO requests require 2 weeks advance notice for non-emergency leave.', 'id': 'vacation_2', 'page': 26},
                {'content': 'Unused PTO carries over to the next year, up to 20 days maximum.', 'id': 'vacation_3', 'page': 27},
                {'content': 'Sick leave is separate from PTO and accrues at 5 days per year.', 'id': 'sick_1', 'page': 30}  # Unrelated
            ],
            'expected_matches': {
                'Employees accrue 10 days of paid time off annually': 'vacation_1',
                'PTO requests require 2 weeks advance notice': 'vacation_2',
                'Unused PTO carries over to the next year': 'vacation_3'
            }
        }
    ]

    # Run evaluation
    results = evaluate_claim_validator(test_cases)

    # Print summary
    print(f'\n{"="*60}')
    print('CLAIM VALIDATOR PERFORMANCE EVALUATION')
    print(f'{"="*60}')
    print(f'Total Claims Evaluated: {results["total_claims"]}')
    print(f'Correct Matches: {results["correct_matches"]}')
    print(f'False Positives: {results["false_positives"]}')
    print(f'False Negatives: {results["false_negatives"]}')
    print(f'Precision: {results["precision"]:.3f}')
    print(f'Recall: {results["recall"]:.3f}')
    print(f'F1 Score: {results["f1_score"]:.3f}')

    # Performance interpretation
    f1 = results['f1_score']
    if f1 >= 0.9:
        performance = "🎉 Excellent - Production Ready"
    elif f1 >= 0.8:
        performance = "✅ Very Good - Minor Tuning Needed"
    elif f1 >= 0.7:
        performance = "👍 Good - Consider Threshold Adjustments"
    elif f1 >= 0.6:
        performance = "⚠️ Acceptable - Needs Improvement"
    else:
        performance = "❌ Poor - Significant Tuning Required"

    print(f'\nPerformance Rating: {performance}')

    # Recommendations
    print(f'\n📋 RECOMMENDATIONS:')
    if results['false_positives'] > results['false_negatives']:
        print('- Consider increasing similarity threshold to reduce false positives')
    elif results['false_negatives'] > results['false_positives']:
        print('- Consider decreasing similarity threshold to reduce false negatives')
    else:
        print('- Similarity threshold appears well-tuned')

    if results['precision'] < 0.8:
        print('- Review claim extraction logic for better precision')
    if results['recall'] < 0.8:
        print('- Consider more sophisticated matching algorithms')

    return results


if __name__ == "__main__":
    run_evaluation()