"""
Intent Classification Module

Handles classification of user messages into intent categories:
- company_policy: Questions about company policies, HR, compliance
- general: Casual conversation, system capability questions, history queries
"""

from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os


INTENT_CLASSIFICATION_PROMPT = """
You are an intent classifier for a policy compliance system. Analyze the user's message and classify it into one of these categories:

1. "company_policy" - Questions about company policies, HR policies, employee handbook, compliance, procedures, etc.
2. "general" - ONLY casual conversation (greetings, small talk) or questions about what the system can do

Respond with ONLY the category name (either "company_policy" or "general").

Examples:
- "What is our vacation policy?" -> company_policy
- "How do I submit a leave request?" -> company_policy
- "What are the dress code requirements?" -> company_policy
- "Hello, how are you?" -> general
- "Hi there!" -> general
- "What can you help me with?" -> general
- "Good morning!" -> general
- "What were the questions I asked previously?" -> general
- "What did I ask before?" -> general
- "Can you recall our conversation history?" -> general
- "What should I eat?" -> general (will be handled by general agent with scope boundaries)
- "What's the weather like?" -> general (will be handled by general agent with scope boundaries)
- "Tell me a joke" -> general (will be handled by general agent with scope boundaries)

When in doubt, classify as "general" to ensure unrelated questions don't get answered.
"""


class IntentClassifier:
    """
    Classifies user intents using a two-stage approach:
    1. Rule-based classification (fast, deterministic)
    2. LLM-based classification (fallback for ambiguous cases)
    """
    
    # Keyword lists for rule-based classification
    POLICY_KEYWORDS = [
        'policy', 'policies', 'hr', 'human resources', 'vacation', 'leave', 'sick', 'holiday',
        'dress code', 'attendance', 'remote work', 'work from home', 'benefits', 'insurance',
        'harassment', 'discrimination', 'complaint', 'procedure', 'handbook', 'employee',
        'employment', 'contract', 'agreement', 'disciplinary', 'termination', 'salary',
        'pay', 'compensation', 'bonus', 'raise', 'promotion', 'performance', 'training',
        'development', 'onboarding', 'orientation', 'safety', 'security', 'compliance',
        'regulation', 'legal', 'law', 'rights', 'responsibilities', 'workplace', 'office',
        'company', 'organization', 'corporate', 'business', 'work', 'job', 'career'
    ]
    
    CASUAL_KEYWORDS = [
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'how are you', 'what\'s up', 'thanks', 'thank you', 'bye', 'goodbye',
        'see you', 'have a good', 'nice to meet', 'pleasure', 'welcome'
    ]
    
    CAPABILITY_KEYWORDS = [
        'what can you', 'what do you', 'how can you', 'what are you', 'help me',
        'assist', 'support', 'capabilities', 'features', 'functions', 'do for'
    ]
    
    HISTORY_KEYWORDS = [
        'previous', 'before', 'earlier', 'last time', 'conversation', 'chat',
        'history', 'asked', 'questions', 'messages', 'what did i', 'what was',
        'recall', 'remember', 'past', 'earlier', 'ago'
    ]
    
    def __init__(self):
        """Initialize the intent classifier with LLM for fallback classification."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        print("[INTENT_CLASSIFIER] Initialized with Gemini 2.5 Flash")
    
    def classify(self, message: str) -> str:
        """
        Classify user intent using rule-based approach first, then LLM if needed.
        
        Args:
            message: User's input message
            
        Returns:
            Intent classification: "company_policy" or "general"
        """
        print(f"[INTENT_CLASSIFIER] Classifying message: {message[:100]}...")
        
        # First try rule-based classification
        intent = self._rule_based_classification(message)
        if intent:
            print(f"[INTENT_CLASSIFIER] ✓ Rule-based result: {intent}")
            return intent
        
        # If rule-based fails, use LLM
        print(f"[INTENT_CLASSIFIER] → Rule-based uncertain, using LLM fallback...")
        intent = self._llm_classification(message)
        print(f"[INTENT_CLASSIFIER] ✓ LLM result: {intent}")
        return intent
    
    def _rule_based_classification(self, message: str) -> Optional[str]:
        """
        Fast rule-based classification using keyword matching.
        
        Args:
            message: User's input message
            
        Returns:
            Intent if confident, None if uncertain
        """
        message_lower = message.lower().strip()
        
        # Count keyword matches
        policy_matches = sum(1 for kw in self.POLICY_KEYWORDS if kw in message_lower)
        casual_matches = sum(1 for kw in self.CASUAL_KEYWORDS if kw in message_lower)
        capability_matches = sum(1 for kw in self.CAPABILITY_KEYWORDS if kw in message_lower)
        history_matches = sum(1 for kw in self.HISTORY_KEYWORDS if kw in message_lower)
        
        print(f"[INTENT_CLASSIFIER] Keyword matches - Policy: {policy_matches}, "
              f"Casual: {casual_matches}, Capability: {capability_matches}, "
              f"History: {history_matches}")
        
        # Policy keywords take precedence
        if policy_matches > 0:
            return "company_policy"
        
        # Any general keywords → general intent
        if casual_matches > 0 or capability_matches > 0 or history_matches > 0:
            return "general"
        
        # No clear matches → return None to trigger LLM classification
        print(f"[INTENT_CLASSIFIER] No clear keyword matches found")
        return None
    
    def _llm_classification(self, message: str) -> str:
        """
        LLM-based classification for ambiguous cases.
        
        Args:
            message: User's input message
            
        Returns:
            Intent classification: "company_policy" or "general"
        """
        try:
            classification_messages = [
                SystemMessage(content=INTENT_CLASSIFICATION_PROMPT),
                HumanMessage(content=message)
            ]
            
            response = self.llm.invoke(classification_messages)
            intent = response.content.strip().lower()
            
            # Validate intent
            if intent not in ["company_policy", "general"]:
                print(f"[INTENT_CLASSIFIER] ⚠ Invalid LLM response '{intent}', defaulting to 'general'")
                intent = "general"
            
            return intent
            
        except Exception as e:
            print(f"[INTENT_CLASSIFIER] ✗ LLM classification error: {e}")
            return "general"  # Safe default