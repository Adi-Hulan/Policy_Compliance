#!/usr/bin/env python3
"""
Test script for the Recommendation Agent
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from agents.recommendation_agent import RecommendationAgent

def test_recommendation_agent():
    """Test the Recommendation Agent with sample violation data"""
    
    print("🧪 Testing Recommendation Agent...")
    
    # Sample violation data (similar to what the violation detector would provide)
    sample_violations = [
        {
            "type": "Violation",
            "title": "Data Privacy Policy Violation",
            "description": "The document contains personal information processing without proper consent mechanisms",
            "severity": "high"
        },
        {
            "type": "Violation", 
            "title": "Security Protocol Non-compliance",
            "description": "Document lacks required security measures for data handling",
            "severity": "medium"
        }
    ]
    
    # Sample paired contexts
    sample_contexts = [
        {
            "attached_chunk": "We collect user data for analytics purposes without explicit consent",
            "matching_policy": "All data collection must be preceded by explicit user consent as per GDPR requirements",
            "distance": 0.15
        }
    ]
    
    try:
        # Initialize the recommendation agent
        agent = RecommendationAgent()
        print("✅ Recommendation Agent initialized successfully")
        
        # Test recommendation generation
        print("\n📋 Generating recommendations...")
        result = agent.generate_recommendations(sample_violations, sample_contexts)
        
        if result["status"] == "success":
            print("✅ Recommendations generated successfully!")
            print(f"📊 Confidence Score: {result['confidence']}")
            print(f"💭 Reasoning: {result['reasoning']}")
            
            print("\n🎯 Generated Recommendations:")
            for i, rec in enumerate(result["recommendations"], 1):
                print(f"\n{i}. {rec.get('recommendation', 'N/A')}")
                print(f"   Priority: {rec.get('priority', 'N/A')}")
                print(f"   Timeline: {rec.get('timeline', 'N/A')}")
                print(f"   Resources: {rec.get('resources_needed', 'N/A')}")
            
            # Test summary generation
            print("\n📈 Testing recommendation summary...")
            summary = agent.get_recommendation_summary(result["recommendations"])
            print(f"Total Recommendations: {summary['total_recommendations']}")
            print(f"Priority Breakdown: {summary['priority_breakdown']}")
            print(f"Timeline Breakdown: {summary['timeline_breakdown']}")
            
        else:
            print(f"❌ Error generating recommendations: {result['result']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
    
    print("\n🎉 All tests passed! Recommendation Agent is working correctly.")
    return True

def test_edge_cases():
    """Test edge cases for the Recommendation Agent"""
    
    print("\n🔍 Testing edge cases...")
    agent = RecommendationAgent()
    
    # Test with empty violations
    print("Testing with empty violations...")
    result = agent.generate_recommendations([])
    if result["status"] == "success" and len(result["recommendations"]) == 0:
        print("✅ Empty violations handled correctly")
    else:
        print("❌ Empty violations not handled correctly")
    
    # Test with malformed violation data
    print("Testing with malformed violation data...")
    malformed_violations = [{"invalid": "data"}]
    result = agent.generate_recommendations(malformed_violations)
    if result["status"] == "success":
        print("✅ Malformed data handled gracefully")
    else:
        print("❌ Malformed data not handled correctly")

if __name__ == "__main__":
    print("🚀 Starting Recommendation Agent Tests\n")
    
    # Check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("Please set your Gemini API key in the .env file")
        sys.exit(1)
    
    # Run tests
    success = test_recommendation_agent()
    test_edge_cases()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
