import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from db.connection import get_db
except ImportError:
    print("Warning: db.connection module not found. Skipping import.")
    get_db = None

class TempQueryAnalyzer:
    """
    A class to analyze user queries against company policies
    and a temporarily attached document using Gemini API.
    """
    def __init__(self):
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        except Exception as e:
            print(f"Error configuring Gemini API: {e}")
            self.model = None
            return

        self.model = genai.GenerativeModel("gemini-1.5-flash")

        self.base_prompt = """
You are a Policy Check Agent.

Your only responsibility is to answer user questions strictly based on the provided documents.

You will receive TWO sets of documents:
1. Company policy documents.
2. Temporarily attached document provided by the user.

Compare the temporarily attached document against the company policies.

If the user asks whether something in the attached document complies with company policies,
check the content carefully and provide a clear, direct answer in simple language.

If the answer cannot be found in the provided documents, respond with: "I don’t know" and also give the specific reason for not knowing.

Do not guess, assume, or use any external knowledge.
"""

    def process(self, query, policy_chunks, temp_chunks):
        """
        Processes a user query by sending it to the Gemini model with
        the provided policy chunks and temporary document chunks.

        Args:
            query (str): The user's question.
            policy_chunks (list of str): Retrieved company policy chunks.
            temp_chunks (list of str): Retrieved temporary document chunks.
        Returns:
            dict: A dictionary containing the agent name, status, and result.
        """
        if not self.model:
            return {
                "agent": "QueryAnalyzer",
                "status": "error",
                "result": "Gemini API model not initialized."
            }

        try:
            # Combine chunks into strings for context
# Extract content from chunk dictionaries
            policy_contents = [chunk["content"] for chunk in policy_chunks["chunks"]] if policy_chunks.get("chunks") else []
            temp_contents = [chunk["content"] for chunk in temp_chunks["chunks"]] if temp_chunks.get("chunks") else []

            # Join the contents
            policy_context = "\n\n".join(policy_contents) if policy_contents else "No policy documents provided."
            temp_context = "\n\n".join(temp_contents) if temp_contents else "No temporary document provided."
            # Create the full prompt
            prompt = f"{self.base_prompt}\n\nCompany Policies:\n{policy_context}\n\nTemporary Document:\n{temp_context}\n\nQuestion:\n{query}\nAnswer:"

            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            answer = response.text

            return {
                "agent": "TempQueryAnalyzer",
                "status": "success",
                "result": answer
            }

        except Exception as e:
            return {
                "agent": "TempQueryAnalyzer",
                "status": "error",
                "result": f"An error occurred during content generation: {e}"
            }
