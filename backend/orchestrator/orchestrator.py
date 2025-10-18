"""
Orchestrator Module

Central orchestrator that routes user messages to appropriate graph pipelines.
Responsibilities:
- Intent classification (via IntentClassifier)
- Graph management and routing
- Stream generation for SSE responses
"""

from typing import Dict, Any, Optional, AsyncGenerator
from graphs.company_policies import build_company_policy_graph
from graphs.general import build_general_purpose_graph
from graphs.international_policy_graph import build_international_policy_graph
from .executor import create_async_stream_generator
from .intent_classifier import IntentClassifier
from db.repositories.chat_repository import ChatRepository


class Orchestrator:
    """
    Central orchestrator that classifies user intents and routes to appropriate pipelines.
    """
    
    def __init__(self):
        """Initialize orchestrator with intent classifier and graph cache."""
        self.intent_classifier = IntentClassifier()
        self.company_policy_graph = None
        self.general_purpose_graph = None
        self.international_policy_graph = None
        self.chat_repo = ChatRepository()
        print("🎼 Orchestrator initialized and ready!")
    
    def get_graph(self, intent: str):
        """
        Get or build the appropriate graph for the given intent.
        Graphs are lazily instantiated and cached.
        
        Args:
            intent: The classified intent ("company_policy", "international_policy", or "general")
            
        Returns:
            Compiled LangGraph instance
            
        Raises:
            ValueError: If intent is not recognized
        """
        print(f"🔍 Getting graph for intent: {intent}")
        
        if intent == "company_policy":
            print(f"🏢 Routing to COMPANY POLICY pipeline")
            if self.company_policy_graph is None:
                print("🏗️  Building company policy graph...")
                self.company_policy_graph = build_company_policy_graph()
                print("✅ Company policy graph built successfully")
            return self.company_policy_graph
            
        elif intent == "general":
            print(f"🌐 Routing to GENERAL PURPOSE pipeline")
            if self.general_purpose_graph is None:
                print("🌐 Building general purpose graph...")
                self.general_purpose_graph = build_general_purpose_graph()
                print("✅ General purpose graph built successfully")
            return self.general_purpose_graph
            
        elif intent == "international_policy":
            print(f"🌍 Routing to INTERNATIONAL POLICY pipeline")
            if self.international_policy_graph is None:
                print("🌍 Building international policy graph...")
                self.international_policy_graph = build_international_policy_graph()
                print("✅ International policy graph built successfully")
            return self.international_policy_graph
    
    def create_stream_generator(
        self, 
        session_id: str, 
        message: str, 
        document_url: Optional[str] = None, 
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Create an async stream generator that routes through the orchestrator.
        
        Args:
            session_id: Unique session identifier
            message: User's input message
            document_url: Optional URL to document for analysis
            user_id: Optional user identifier for session management
            
        Returns:
            AsyncGenerator yielding SSE-formatted strings
        """
        print("🚀 Starting AI Pipeline Execution")
        print("=" * 50)
        print(f"Session: {session_id}")
        print(f"User: {user_id}")
        print(f"Query: {message[:80]}{'...' if len(message) > 80 else ''}")
        if document_url:
            print(f"Document: {document_url}")
        print("=" * 50)
        
        # Step 1: Classify intent
        print("🎯 Step 1: Classifying user intent...")
        intent = self.intent_classifier.classify(message)
        print(f"🎯 Intent classified: {intent}")
        
        # Step 2: Get appropriate graph
        print("🔧 Step 2: Building execution graph...")
        graph = self.get_graph(intent)
        print(f"✅ Graph ready: {type(graph).__name__}")
        
        # Step 3: Create initial state
        print("📋 Step 3: Preparing initial state...")
        initial_state = {
            "session_id": session_id,
            "message": message,
            "document_url": document_url,
            "intent": intent,
            "user_id": user_id,
            "chat_repository": self.chat_repo,  # Pass repository instead of orchestrator
        }
        
        print(f"📋 State keys: {list(initial_state.keys())}")
        print(f"🚀 Final routing: {intent.upper()} pipeline")
        print("=" * 80)
        
        # Step 4: Create and return async stream generator
        print("⚡ Step 4: Creating async stream generator...")
        stream_gen = create_async_stream_generator(graph, initial_state)
        print("✅ Async stream generator ready")
        
        return stream_gen


# Global orchestrator instance (singleton pattern)
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    """
    Get the global orchestrator instance (singleton).
    Creates a new instance on first call, returns cached instance on subsequent calls.
    
    Returns:
        Global Orchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        print("🎼 Creating new global orchestrator instance...")
        _orchestrator = Orchestrator()
        print("✅ Global orchestrator ready")
    else:
        print("♻️  Using existing global orchestrator instance")
    return _orchestrator