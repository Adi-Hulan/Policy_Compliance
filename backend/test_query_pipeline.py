import os
from dotenv import load_dotenv
from orchestrator.pipelines.query_pipeline import execute_query_pipeline

# Load environment variables
load_dotenv()

def test_query_pipeline():
    """
    Test the query pipeline with a simple policy question.
    """
    print("===== TESTING QUERY PIPELINE =====")
    
    # The question we want to ask
    test_query = "Can I be terminated for using the company’s email system in a way that violates anti-discrimination policies?"
    print(f"\nQuery: '{test_query}'")
    
    # Execute the pipeline
    print("\nExecuting pipeline...")
    result = execute_query_pipeline(test_query)
    
    # Print the pipeline status
    print(f"\nPipeline Status: {result.get('status', 'unknown')}")
    
    if result.get("status") == "success":
        print("\n✅ Query pipeline test passed!")
        
        # Print the result
        print("\nResponse:")
        print("-" * 50)
        print(result.get("result", "No result returned"))
        print("-" * 50)
        
        # Print information about retrieved chunks if available
        if "chunks" in result:
            print(f"\nRetrieved {len(result.get('chunks', []))} relevant chunks")
            
            # Show a sample of the first chunk if available
            if result.get("chunks") and len(result.get("chunks")) > 0:
                first_chunk = result.get("chunks")[0]
                print("\nSample chunk:")
                print("-" * 50)
                print(f"ID: {first_chunk.get('id', 'unknown')}")
                print(f"Distance: {first_chunk.get('distance', 'unknown')}")
                print(f"Content: {first_chunk.get('content', 'No content')[:150]}...")
                print("-" * 50)
    else:
        print("\n❌ Query pipeline test failed!")
        print(f"Error: {result.get('message', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    # Run the test
    test_query_pipeline()
