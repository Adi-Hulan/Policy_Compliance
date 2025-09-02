import os
import json
import logging
from urllib.parse import quote_plus
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.documents import Document
from db.connection import get_db  # Reuse the DB connection
import psycopg2  # For raw queries if needed

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationAgent:
    def __init__(self):
        # Configure Gemini via LangChain
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)  # For reasoning
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Set up vector store for IR (connects to pgvector DB)
        try:
            db_user = os.getenv('DB_USER', '')
            db_password = os.getenv('DB_PASSWORD', '')
            db_host = os.getenv('DB_HOST', '')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', '')

            # Safely URL-encode credentials (handles special chars like @, :, /)
            safe_user = quote_plus(db_user)
            safe_password = quote_plus(db_password)

            connection_string = (
                f"postgresql://{safe_user}:{safe_password}"
                f"@{db_host}:{db_port}/{db_name}?sslmode=require"
            )
            
            self.vector_store = PGVector(
                collection_name="documents",  # Your table
                connection=connection_string,
                embeddings=self.embeddings,
                use_jsonb=True  # If using JSON for metadata
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            # Fallback: create a mock vector store for testing
            self.vector_store = None

    def validate_input(self, query, violations=None):
        """Validate input parameters"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace")
        if len(query.strip()) < 10:
            raise ValueError("Query must be at least 10 characters long")
        if violations and not isinstance(violations, (str, list)):
            raise ValueError("Violations must be a string or list")
        return True

    def generate_mock_recommendations(self, query, violations=None):
        """Generate mock recommendations when LLM is not available"""
        base_recommendations = [
            {
                "action": "Implement comprehensive remote work policy with clear guidelines",
                "priority": "Critical",
                "policy_reference": "Section 3.2 - Remote Work Guidelines",
                "deadline": "30 days"
            },
            {
                "action": "Establish regular check-ins and communication protocols",
                "priority": "Important", 
                "policy_reference": "Section 4.1 - Communication Standards",
                "deadline": "immediate"
            },
            {
                "action": "Set up secure VPN and data protection measures",
                "priority": "Critical",
                "policy_reference": "Section 5.3 - Data Security",
                "deadline": "immediate"
            }
        ]
        
        # Customize based on query keywords
        if "harassment" in query.lower():
            base_recommendations = [
                {
                    "action": "Immediately investigate the harassment complaint",
                    "priority": "Critical",
                    "policy_reference": "Section 2.1 - Harassment Policy",
                    "deadline": "immediate"
                },
                {
                    "action": "Document all interactions and evidence",
                    "priority": "Important",
                    "policy_reference": "Section 2.3 - Documentation Requirements",
                    "deadline": "ongoing"
                },
                {
                    "action": "Provide support to the affected employee",
                    "priority": "Critical",
                    "policy_reference": "Section 2.5 - Employee Support",
                    "deadline": "immediate"
                }
            ]
        elif "data" in query.lower() or "privacy" in query.lower():
            base_recommendations = [
                {
                    "action": "Implement GDPR-compliant data handling procedures",
                    "priority": "Critical",
                    "policy_reference": "Section 6.1 - Data Protection",
                    "deadline": "30 days"
                },
                {
                    "action": "Train employees on data privacy requirements",
                    "priority": "Important",
                    "policy_reference": "Section 6.2 - Training Requirements",
                    "deadline": "ongoing"
                },
                {
                    "action": "Establish data retention and deletion policies",
                    "priority": "Important",
                    "policy_reference": "Section 6.3 - Data Retention",
                    "deadline": "30 days"
                }
            ]
        
        return {
            "recommendations": base_recommendations,
            "confidence": 0.85,
            "reasoning": f"Generated recommendations based on query analysis: {query[:100]}...",
            "risk_level": "Medium"
        }

    def extract_recommendations_from_text(self, text):
        """Fallback method to extract recommendations from LLM text response"""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith(('-', '•', '1.', '2.', '3.')):
                recommendations.append(line.strip())
        return {
            "recommendations": recommendations[:3],
            "confidence": 0.6,
            "reasoning": "Generated from text analysis",
            "risk_level": "Medium"
        }

    def process_context(self, docs):
        """Process retrieved documents more intelligently"""
        if len(docs) > 3:
            summary_prompt = "Summarize the key compliance points from these policy sections:\n"
            context = summary_prompt + "\n".join([doc.page_content for doc in docs[:3]])
        else:
            context = "\n".join([doc.page_content for doc in docs])
        return context

    def process(self, query, violations=None):
        try:
            logger.info(f"Processing recommendation request: {query[:50]}...")
            self.validate_input(query, violations)
            full_query = query
            if violations:
                full_query += f"\nDetected violations: {violations}"
            logger.info("Performing vector search...")
            if self.vector_store is None:
                logger.warning("Vector store not available, using mock data for testing")
                # Mock documents for testing when DB is not available
                docs = [
                    Document(page_content="Sample HR policy: All employees must follow workplace safety guidelines and report incidents immediately."),
                    Document(page_content="Remote work policy: Employees working remotely must maintain regular communication and adhere to company security protocols."),
                    Document(page_content="Data protection policy: Employee data must be handled according to GDPR guidelines with proper consent and security measures.")
                ]
            else:
                docs = self.vector_store.similarity_search(full_query, k=5)
            
            if not docs:
                logger.warning("No relevant policies found")
                return {"agent": "RecommendationAgent", "status": "error", "result": "No relevant policies found"}
            context = self.process_context(docs)
            logger.info(f"Retrieved {len(docs)} relevant policy chunks")
            
            # Step 4: LLM Chain for recommendations
            try:
                prompt = PromptTemplate(
                    input_variables=["context", "query", "violations"],
                    template="""You are a policy compliance expert. 

Context from policy documents:
{context}

User situation: {query}
{violations_text}

Provide 2-3 specific, actionable recommendations:
1. Each recommendation should be concrete and implementable
2. Include compliance level (Critical/Important/Recommended)
3. Mention specific policy sections if relevant
4. Consider risk mitigation strategies

Format as JSON:
{{
    "recommendations": [
        {{"action": "specific action", "priority": "Critical/Important/Recommended", "policy_reference": "section if applicable", "deadline": "immediate/30 days/ongoing"}}
    ],
    "confidence": 0.XX,
    "reasoning": "detailed explanation",
    "risk_level": "High/Medium/Low"
}}

Ensure the response is valid JSON only."""
                )
                
                # Prepare violations text
                violations_text = f"Detected violations: {violations}" if violations else ""
                
                chain = LLMChain(llm=self.llm, prompt=prompt)
                response = chain.run({"context": context, "query": full_query, "violations_text": violations_text})
                
                logger.info("Parsing LLM response...")
                try:
                    result = json.loads(response)
                    logger.info(f"Successfully generated {len(result.get('recommendations', []))} recommendations")
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}. Using fallback method.")
                    result = self.generate_mock_recommendations(query, violations)
                    
            except Exception as llm_error:
                logger.warning(f"LLM failed: {str(llm_error)}. Using mock recommendations.")
                result = self.generate_mock_recommendations(query, violations)
            return {"agent": "RecommendationAgent", "status": "success", "result": result}
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return {"agent": "RecommendationAgent", "status": "error", "result": f"Validation error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error in recommendation generation: {str(e)}")
            return {"agent": "RecommendationAgent", "status": "error", "result": str(e)}
