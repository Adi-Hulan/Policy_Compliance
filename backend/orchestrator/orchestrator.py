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
        self.chat_repo = ChatRepository()
        print("[ORCHESTRATOR] Initialized orchestrator")
    
    def get_graph(self, intent: str):
        """
        Get or build the appropriate graph for the given intent.
        Graphs are lazily instantiated and cached.
        
        Args:
            intent: The classified intent ("company_policy" or "general")
            
        Returns:
            Compiled LangGraph instance
            
        Raises:
            ValueError: If intent is not recognized
        """
        print(f"[ORCHESTRATOR] Getting graph for intent: {intent}")
        
        if intent == "company_policy":
            print(f"[ORCHESTRATOR] → Routing to COMPANY POLICY pipeline")
            if self.company_policy_graph is None:
                print(f"[ORCHESTRATOR] Building company policy graph...")
                self.company_policy_graph = build_company_policy_graph()
                print("[ORCHESTRATOR] ✓ Company policy graph built")
            return self.company_policy_graph
            
        elif intent == "general":
            print(f"[ORCHESTRATOR] → Routing to GENERAL PURPOSE pipeline")
            if self.general_purpose_graph is None:
                print(f"[ORCHESTRATOR] Building general purpose graph...")
                self.general_purpose_graph = build_general_purpose_graph()
                print("[ORCHESTRATOR] ✓ General purpose graph built")
            return self.general_purpose_graph
            
        else:
            raise ValueError(f"Unknown intent: {intent}")
    
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
        print("=" * 80)
        print(f"[ORCHESTRATOR] Creating stream generator")
        print(f"[ORCHESTRATOR] Session: {session_id}")
        print(f"[ORCHESTRATOR] User: {user_id}")
        print(f"[ORCHESTRATOR] Message: {message[:100]}...")
        if document_url:
            print(f"[ORCHESTRATOR] Document URL: {document_url}")
        print("=" * 80)
        
        # Step 1: Classify intent
        print(f"[ORCHESTRATOR] Step 1: Classifying intent...")
        intent = self.intent_classifier.classify(message)
        print(f"[ORCHESTRATOR] ✓ Intent: {intent}")
        
        # Step 2: Get appropriate graph
        print(f"[ORCHESTRATOR] Step 2: Getting graph...")
        graph = self.get_graph(intent)
        print(f"[ORCHESTRATOR] ✓ Graph obtained: {type(graph).__name__}")
        
        # Step 3: Create initial state
        print(f"[ORCHESTRATOR] Step 3: Creating initial state...")
        initial_state = {
            "session_id": session_id,
            "message": message,
            "document_url": document_url,
            "intent": intent,
            "user_id": user_id,
            "chat_repository": self.chat_repo,  # Pass repository instead of orchestrator
        }
        
        print(f"[ORCHESTRATOR] ✓ State keys: {list(initial_state.keys())}")
        print(f"[ORCHESTRATOR] → Final routing: {intent.upper()} pipeline")
        print("=" * 80)
        
        # Step 4: Create and return async stream generator
        print(f"[ORCHESTRATOR] Step 4: Creating async stream generator...")
        stream_gen = create_async_stream_generator(graph, initial_state)
        print(f"[ORCHESTRATOR] ✓ Async stream generator created")
        
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
        print("[ORCHESTRATOR] Creating new global orchestrator instance...")
        _orchestrator = Orchestrator()
        print("[ORCHESTRATOR] ✓ Global orchestrator created")
    else:
        print("[ORCHESTRATOR] Using existing global orchestrator instance")
    return _orchestrator