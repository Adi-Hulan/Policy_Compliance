"""
Claim Validator Performance Evaluation

Evaluates the accuracy of claim extraction and hallucination detection
using precision, recall, and F1 score metrics.
"""

from graphs.nodes.shared.claim_validator import extract_claims, find_best_chunk_match
from typing import List, Dict, Any
import json


def evaluate_claim_validator(test_cases: List[Dict[str, Any]], threshold: float = 0.4) -> Dict[str, Any]:
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

            match = find_best_chunk_match(claim, test_case['chunks'], threshold=0.4)
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
                confidence = match.get('confidence', 'unknown')
                if match['id'] == expected_chunk:
                    results['correct_matches'] += 1
                    claim_result['correct'] = True
                    print(f'✅ CORRECT ({confidence.upper()}): "{claim[:50]}..." → {match["id"]}')
                else:
                    results['false_positives'] += 1
                    claim_result['false_positive'] = True
                    print(f'❌ WRONG MATCH ({confidence.upper()}): "{claim[:50]}..." → {match["id"]} (expected {expected_chunk})')
            elif match and not expected_chunk:
                confidence = match.get('confidence', 'unknown')
                results['false_positives'] += 1
                claim_result['false_positive'] = True
                print(f'❌ FALSE POSITIVE ({confidence.upper()}): "{claim[:50]}..." → {match["id"]} (should be no match)')
            elif not match and expected_chunk:
                results['false_negatives'] += 1
                claim_result['false_negative'] = True
                # Try to find what the best match actually was
                best_match = find_best_chunk_match(claim, test_case['chunks'], threshold=0.0)  # Very low threshold to see best match
                best_score = best_match['similarity_score'] if best_match else 0.0
                best_id = best_match['id'] if best_match else 'none'
                print(f'❌ MISSED: "{claim[:50]}..." (expected {expected_chunk}, best match: {best_id} score: {best_score:.3f})')
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
        },
        {
            'name': 'Ambiguous Claims Test',
            'response': 'Employees can work from home. The dress code is business casual. Performance reviews happen quarterly.',
            'chunks': [
                {'content': 'Remote work is permitted with manager approval and proper equipment setup.', 'id': 'remote_1', 'page': 15},
                {'content': 'Dress code is business casual Monday through Thursday, business formal on Fridays.', 'id': 'dress_1', 'page': 16},
                {'content': 'Performance reviews are conducted quarterly with annual salary reviews.', 'id': 'perf_1', 'page': 17},
                {'content': 'Casual Friday allows jeans and company t-shirts.', 'id': 'casual_1', 'page': 18}  # Similar but different
            ],
            'expected_matches': {
                'Employees can work from home': 'remote_1',
                'The dress code is business casual': 'dress_1',
                'Performance reviews happen quarterly': 'perf_1'
            }
        },
        {
            'name': 'Hallucination Detection',
            'response': 'All meetings start at 9 AM sharp. Coffee is provided free in the break room. The company gym is open 24/7.',
            'chunks': [
                {'content': 'Meeting rooms must be reserved through the online booking system.', 'id': 'meeting_1', 'page': 21},
                {'content': 'Break room amenities include microwave, refrigerator, and coffee machine.', 'id': 'break_1', 'page': 22},
                {'content': 'Employee parking is available in the west lot.', 'id': 'parking_1', 'page': 23},
                {'content': 'IT support is available Monday through Friday from 8 AM to 6 PM.', 'id': 'it_1', 'page': 24}
            ],
            'expected_matches': {
                # No matches expected - all claims are hallucinations/fabrications
            }
        },
        {
            'name': 'Similar Chunks Challenge',
            'response': 'Salaries are reviewed annually. Bonuses are discretionary. Health insurance covers dental.',
            'chunks': [
                {'content': 'Annual salary reviews are based on performance and market conditions.', 'id': 'salary_1', 'page': 31},
                {'content': 'Performance bonuses are at the discretion of management.', 'id': 'bonus_1', 'page': 32},
                {'content': 'Health insurance includes medical, dental, and vision coverage.', 'id': 'health_1', 'page': 33},
                {'content': 'Salary increases are reviewed annually but not guaranteed.', 'id': 'salary_2', 'page': 34},  # Very similar to salary_1
                {'content': 'Management has discretion over bonus allocations.', 'id': 'bonus_2', 'page': 35}  # Very similar to bonus_1
            ],
            'expected_matches': {
                'Salaries are reviewed annually': 'salary_1',
                'Bonuses are discretionary': 'bonus_1',
                'Health insurance covers dental': 'health_1'
            }
        },
        {
            'name': 'Partial Information Test',
            'response': 'The probation period is 90 days. New hires get 15 PTO days. Background checks are required.',
            'chunks': [
                {'content': 'New employees serve a 90-day probationary period with performance reviews at 30, 60, and 90 days.', 'id': 'probation_1', 'page': 41},
                {'content': 'New hires receive 10 PTO days in their first year, increasing to 15 after the first anniversary.', 'id': 'pto_new_1', 'page': 42},
                {'content': 'All employment offers are contingent upon successful background check completion.', 'id': 'background_1', 'page': 43},
                {'content': 'Probationary employees have limited access to certain company resources.', 'id': 'probation_2', 'page': 44}
            ],
            'expected_matches': {
                'The probation period is 90 days': 'probation_1',
                'New hires get 15 PTO days': 'pto_new_1',
                'Background checks are required': 'background_1'
            }
        },
        {
            'name': 'Contradictory Information',
            'response': 'Overtime must be approved. Work week is 40 hours. Flexible hours are available.',
            'chunks': [
                {'content': 'Overtime work requires prior management approval.', 'id': 'ot_1', 'page': 51},
                {'content': 'Standard work week is 40 hours Monday through Friday.', 'id': 'week_1', 'page': 52},
                {'content': 'Flexible scheduling is available for exempt employees with manager approval.', 'id': 'flex_1', 'page': 53},
                {'content': 'Non-exempt employees must clock overtime hours accurately.', 'id': 'ot_2', 'page': 54}
            ],
            'expected_matches': {
                'Overtime must be approved': 'ot_1',
                'Work week is 40 hours': 'week_1',
                'Flexible hours are available': 'flex_1'
            }
        },
        {
            'name': 'Temporal Reasoning Test',
            'response': 'Employees must submit expense reports within 30 days. Training sessions occur quarterly. Performance reviews happen annually.',
            'chunks': [
                {'content': 'Expense reports must be submitted within 30 days of the expense date.', 'id': 'expense_1', 'page': 61},
                {'content': 'Quarterly training sessions are mandatory for all staff.', 'id': 'training_1', 'page': 62},
                {'content': 'Annual performance reviews determine salary adjustments.', 'id': 'review_1', 'page': 63},
                {'content': 'Monthly expense summaries are due by the 5th of each month.', 'id': 'expense_2', 'page': 64},  # Different timing
                {'content': 'Weekly team meetings are held every Friday.', 'id': 'meeting_1', 'page': 65}  # Different frequency
            ],
            'expected_matches': {
                'Employees must submit expense reports within 30 days': 'expense_1',
                'Training sessions occur quarterly': 'training_1',
                'Performance reviews happen annually': 'review_1'
            }
        },
        {
            'name': 'Conditional Logic Test',
            'response': 'Overtime pay is double time if approved. Employees can work remotely if productivity is maintained. Bonuses are awarded when targets are exceeded.',
            'chunks': [
                {'content': 'Approved overtime is paid at double the regular rate.', 'id': 'ot_pay_1', 'page': 71},
                {'content': 'Remote work is permitted when employee productivity remains high.', 'id': 'remote_1', 'page': 72},
                {'content': 'Performance bonuses are given when quarterly targets are exceeded.', 'id': 'bonus_1', 'page': 73},
                {'content': 'Overtime requires manager approval before working extra hours.', 'id': 'ot_approval_1', 'page': 74},  # Different condition
                {'content': 'Base salary increases occur annually regardless of performance.', 'id': 'salary_1', 'page': 75}  # No condition
            ],
            'expected_matches': {
                'Overtime pay is double time if approved': 'ot_pay_1',
                'Employees can work remotely if productivity is maintained': 'remote_1',
                'Bonuses are awarded when targets are exceeded': 'bonus_1'
            }
        },
        {
            'name': 'Quantitative Reasoning Test',
            'response': 'Health insurance covers 80% of medical costs. Employees receive 2 weeks of paid sick leave. The company matches 50% of 401k contributions.',
            'chunks': [
                {'content': 'Health insurance covers 80% of approved medical expenses.', 'id': 'health_1', 'page': 81},
                {'content': 'Employees accrue 10 days of paid sick leave annually.', 'id': 'sick_1', 'page': 82},
                {'content': '401k matching is 50% of employee contributions up to 6% of salary.', 'id': 'retirement_1', 'page': 83},
                {'content': 'Dental insurance covers 70% of preventive care costs.', 'id': 'dental_1', 'page': 84},  # Different percentage
                {'content': 'Vacation accrual is 10 days per year.', 'id': 'vacation_1', 'page': 85}  # Different benefit type
            ],
            'expected_matches': {
                'Health insurance covers 80% of medical costs': 'health_1',
                'Employees receive 2 weeks of paid sick leave': 'sick_1',
                'The company matches 50% of 401k contributions': 'retirement_1'
            }
        },
        {
            'name': 'Multi-hop Reasoning Test',
            'response': 'Senior managers can approve expenses up to $5000. Department heads report to vice presidents. IT support is available during business hours.',
            'chunks': [
                {'content': 'Managers can approve expenses up to $5000 without additional approval.', 'id': 'expense_approval_1', 'page': 91},
                {'content': 'Department heads report directly to vice presidents.', 'id': 'reporting_1', 'page': 92},
                {'content': 'IT help desk operates Monday through Friday, 8 AM to 6 PM.', 'id': 'it_hours_1', 'page': 93},
                {'content': 'Individual contributors can approve up to $1000.', 'id': 'expense_approval_2', 'page': 94},  # Different level
                {'content': 'Vice presidents report to the CEO.', 'id': 'reporting_2', 'page': 95}  # Different relationship
            ],
            'expected_matches': {
                'Senior managers can approve expenses up to $5000': 'expense_approval_1',
                'Department heads report to vice presidents': 'reporting_1',
                'IT support is available during business hours': 'it_hours_1'
            }
        },
        {
            'name': 'Negation and Exception Test',
            'response': 'No smoking is allowed in the building. Employees cannot work more than 60 hours per week. Visitors must sign in except for vendors.',
            'chunks': [
                {'content': 'Smoking is prohibited in all company buildings and facilities.', 'id': 'smoking_1', 'page': 101},
                {'content': 'Maximum work week is 60 hours, including overtime.', 'id': 'hours_1', 'page': 102},
                {'content': 'All visitors must sign in at reception, except pre-approved vendors.', 'id': 'visitors_1', 'page': 103},
                {'content': 'Smoking areas are designated outside the main entrance.', 'id': 'smoking_2', 'page': 104},  # Exception exists
                {'content': 'Regular work week is 40 hours.', 'id': 'hours_2', 'page': 105}  # Different limit
            ],
            'expected_matches': {
                'No smoking is allowed in the building': 'smoking_1',
                'Employees cannot work more than 60 hours per week': 'hours_1',
                'Visitors must sign in except for vendors': 'visitors_1'
            }
        },
        {
            'name': 'Cross-domain Confusion Test',
            'response': 'Code reviews are required for all changes. Security protocols must be followed. Quality assurance testing is mandatory.',
            'chunks': [
                {'content': 'All code changes require peer review before deployment.', 'id': 'code_review_1', 'page': 111},
                {'content': 'Information security protocols must be followed at all times.', 'id': 'security_1', 'page': 112},
                {'content': 'Quality assurance testing is required for all software releases.', 'id': 'qa_1', 'page': 113},
                {'content': 'Financial audits are conducted quarterly.', 'id': 'audit_1', 'page': 114},  # Different domain
                {'content': 'Building security requires keycard access.', 'id': 'security_2', 'page': 115}  # Different domain
            ],
            'expected_matches': {
                'Code reviews are required for all changes': 'code_review_1',
                'Security protocols must be followed': 'security_1',
                'Quality assurance testing is mandatory': 'qa_1'
            }
        },
        {
            'name': 'Subtle Hallucinations Test',
            'response': 'Employees get 11 PTO days annually. Training is completed by January 15th. Performance ratings include outstanding level.',
            'chunks': [
                {'content': 'Employees accrue 10 PTO days annually, increasing to 15 after 5 years.', 'id': 'pto_1', 'page': 121},
                {'content': 'Annual compliance training must be completed by December 31st.', 'id': 'training_1', 'page': 122},
                {'content': 'Performance ratings are: exceeds expectations, meets expectations, needs improvement.', 'id': 'ratings_1', 'page': 123},
                {'content': 'Holiday pay is 11 days for full-time employees.', 'id': 'holiday_1', 'page': 124},  # Close but different
                {'content': 'Training completion deadline is January 31st for new hires.', 'id': 'training_2', 'page': 125}  # Close but different
            ],
            'expected_matches': {
                # All claims are subtle hallucinations - should have no matches
            }
        },
        {
            'name': 'Context-dependent Claims Test',
            'response': 'Full-time employees get health benefits. Contractors are eligible for parking. Temporary workers receive training.',
            'chunks': [
                {'content': 'Full-time employees receive comprehensive health insurance benefits.', 'id': 'benefits_1', 'page': 131},
                {'content': 'Parking permits are available to all employees and approved contractors.', 'id': 'parking_1', 'page': 132},
                {'content': 'All new hires, including temporaries, receive orientation training.', 'id': 'training_1', 'page': 133},
                {'content': 'Contractors are responsible for their own benefits.', 'id': 'contractor_1', 'page': 134},  # Context matters
                {'content': 'Temporary employees work on fixed-term assignments.', 'id': 'temp_1', 'page': 135}  # Context matters
            ],
            'expected_matches': {
                'Full-time employees get health benefits': 'benefits_1',
                'Contractors are eligible for parking': 'parking_1',
                'Temporary workers receive training': 'training_1'
            }
        },
        {
            'name': 'Comparative Claims Test',
            'response': 'Senior developers earn more than junior developers. Managers have larger offices than staff. Executive bonuses exceed staff bonuses.',
            'chunks': [
                {'content': 'Senior developers receive higher salaries than junior developers.', 'id': 'salary_1', 'page': 141},
                {'content': 'Management has larger office spaces compared to individual contributors.', 'id': 'office_1', 'page': 142},
                {'content': 'Executive compensation includes substantial bonuses above base salary.', 'id': 'exec_bonus_1', 'page': 143},
                {'content': 'All employees receive equal base pay regardless of position.', 'id': 'equal_pay_1', 'page': 144},  # Contradicts
                {'content': 'Office size is determined by team size, not position.', 'id': 'office_2', 'page': 145}  # Contradicts
            ],
            'expected_matches': {
                'Senior developers earn more than junior developers': 'salary_1',
                'Managers have larger offices than staff': 'office_1',
                'Executive bonuses exceed staff bonuses': 'exec_bonus_1'
            }
        },
        {
            'name': 'Policy Evolution Test',
            'response': 'The new PTO policy increases accrual rates. Updated security measures require two-factor authentication. Revised expense limits went into effect January 1st.',
            'chunks': [
                {'content': 'Effective January 1st, PTO accrual increased from 10 to 12 days annually.', 'id': 'pto_update_1', 'page': 151},
                {'content': 'Two-factor authentication is now required for all system access.', 'id': 'security_update_1', 'page': 152},
                {'content': 'Expense approval limits increased effective January 1st.', 'id': 'expense_update_1', 'page': 153},
                {'content': 'Previous PTO policy was 10 days per year.', 'id': 'pto_old_1', 'page': 154},  # Historical
                {'content': 'Security measures are updated annually.', 'id': 'security_general_1', 'page': 155}  # General
            ],
            'expected_matches': {
                'The new PTO policy increases accrual rates': 'pto_update_1',
                'Updated security measures require two-factor authentication': 'security_update_1',
                'Revised expense limits went into effect January 1st': 'expense_update_1'
            }
        }
    ]
    results = evaluate_claim_validator(test_cases)

    # Print detailed results per test case
    print(f'\n{"="*80}')
    print('DETAILED RESULTS PER TEST CASE')
    print(f'{"="*80}')
    
    for case_result in results['detailed_results']:
        case_name = case_result['test_case']
        claims = case_result['claims']
        correct = sum(1 for c in claims if c['correct'])
        fp = sum(1 for c in claims if c['false_positive'])
        fn = sum(1 for c in claims if c['false_negative'])
        total = len(claims)
        
        print(f'\n{case_name}:')
        print(f'  Claims: {total}, Correct: {correct}, False Positives: {fp}, False Negatives: {fn}')
        if total > 0:
            case_precision = correct / (correct + fp) if (correct + fp) > 0 else 0
            case_recall = correct / (correct + fn) if (correct + fn) > 0 else 0
            case_f1 = 2 * case_precision * case_recall / (case_precision + case_recall) if (case_precision + case_recall) > 0 else 0
            print(f'  Precision: {case_precision:.3f}, Recall: {case_recall:.3f}, F1: {case_f1:.3f}')

    # Print summary
    print(f'\n{"="*60}')
    print('OVERALL CLAIM VALIDATOR PERFORMANCE EVALUATION')
    print(f'{"="*60}')
    print(f'Total Test Cases: {len(test_cases)}')
    print(f'Total Claims Evaluated: {results["total_claims"]}')
    print(f'Correct Matches: {results["correct_matches"]}')
    print(f'False Positives: {results["false_positives"]}')
    print(f'False Negatives: {results["false_negatives"]}')
    print(f'Precision: {results["precision"]:.3f}')
    print(f'Recall: {results["recall"]:.3f}')
    print(f'F1 Score: {results["f1_score"]:.3f}')

    # Error analysis
    print(f'\n📊 ERROR ANALYSIS:')
    if results['false_positives'] > 0 or results['false_negatives'] > 0:
        fp_rate = results['false_positives'] / results['total_claims']
        fn_rate = results['false_negatives'] / results['total_claims']
        print(f'False Positive Rate: {fp_rate:.3f} ({results["false_positives"]}/{results["total_claims"]})')
        print(f'False Negative Rate: {fn_rate:.3f} ({results["false_negatives"]}/{results["total_claims"]})')
        
        if results['false_positives'] > results['false_negatives']:
            print('Primary Issue: Too many false positives (over-matching)')
        elif results['false_negatives'] > results['false_positives']:
            print('Primary Issue: Too many false negatives (under-matching)')
        else:
            print('Balanced error rates')
    else:
        print('No errors detected - perfect performance!')

    # Human review requirements
    uncertain_matches = results['total_claims'] - results['correct_matches'] - results['false_positives']
    human_review_rate = uncertain_matches / results['total_claims'] if results['total_claims'] > 0 else 0
    print(f'\n👥 HUMAN REVIEW REQUIREMENTS:')
    print(f'Claims needing human verification: {uncertain_matches}/{results["total_claims"]} ({human_review_rate:.1%})')
    if results['false_negatives'] > 0:
        print(f'🚨 Critical: {results["false_negatives"]} unsupported claims - require immediate human review')
    if uncertain_matches > results['correct_matches']:
        print('⚠️  Warning: More claims need review than are auto-validated')

    # Performance interpretation
    f1 = results['f1_score']
    if f1 >= 0.95:
        performance = "🎉 Outstanding - Production Ready"
    elif f1 >= 0.9:
        performance = "✅ Excellent - Production Ready"
    elif f1 >= 0.8:
        performance = "👍 Very Good - Minor Tuning Needed"
    elif f1 >= 0.7:
        performance = "⚠️ Good - Consider Threshold Adjustments"
    elif f1 >= 0.6:
        performance = "🟡 Acceptable - Needs Improvement"
    else:
        performance = "❌ Poor - Significant Tuning Required"

    print(f'\n🏆 Performance Rating: {performance}')

    # Recommendations
    print(f'\n📋 RECOMMENDATIONS:')
    if results['false_positives'] > results['false_negatives']:
        print('- Increase similarity threshold (current: 0.5) to reduce false positives')
        print('- Consider stricter matching criteria')
    elif results['false_negatives'] > results['false_positives']:
        print('- Decrease similarity threshold (current: 0.5) to reduce false negatives')
        print('- Review chunk preprocessing and embedding quality')
    else:
        print('- Similarity threshold (0.5) appears well-calibrated')

    if results['precision'] < 0.8:
        print('- Improve claim extraction to reduce ambiguous claims')
        print('- Enhance chunk relevance filtering')
    if results['recall'] < 0.8:
        print('- Consider ensemble matching approaches')
        print('- Review chunk coverage and granularity')

    # Test different thresholds
    print(f'\n🔧 THRESHOLD SENSITIVITY ANALYSIS:')
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    for threshold in thresholds:
        test_results = evaluate_claim_validator(test_cases, threshold=threshold)
        print(f'Threshold {threshold:.1f}: Precision={test_results["precision"]:.3f}, Recall={test_results["recall"]:.3f}, F1={test_results["f1_score"]:.3f}')

    return results


if __name__ == "__main__":
    run_evaluation()