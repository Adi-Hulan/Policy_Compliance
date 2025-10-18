"""
Node Models

Pydantic models for node inputs, outputs, and graph state definitions.
Provides type safety and clear documentation of node interfaces.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


# --- Base Node Models ---
class NodeInput(BaseModel):
    """Base class for all node inputs."""
    pass


class NodeOutput(BaseModel):
    """Base class for all node outputs."""
    pass


# --- Shared Node Models ---

class InputNodeInput(NodeInput):
    """Input for input validation node."""
    session_id: str
    user_id: str
    message: str
    document_url: Optional[str] = None
    intent: Optional[str] = None


class InputNodeOutput(NodeOutput):
    """Output from input validation node."""
    safe_session_id: str


class HistoryNodeInput(NodeInput):
    """Input for history loading node."""
    session_id: str
    chat_repository: Any  # ChatRepository instance


class HistoryNodeOutput(NodeOutput):
    """Output from history loading node."""
    history: List[BaseMessage]


class LLMNodeInput(NodeInput):
    """Input for LLM generation node."""
    message: str
    history: List[BaseMessage]
    system_prompt: str
    message_key: str = "message"


class LLMNodeOutput(NodeOutput):
    """Output from LLM generation node."""
    response: str


class SessionUpdateNodeInput(NodeInput):
    """Input for session update node."""
    session_id: str
    user_id: Optional[str]
    message: str
    response: str
    chat_repository: Any  # ChatRepository instance


class SessionUpdateNodeOutput(NodeOutput):
    """Output from session update node."""
    pass  # No output, just side effects


class OutputNodeInput(NodeInput):
    """Input for output preparation node."""
    session_id: str
    response: str
    chat_repository: Any  # ChatRepository instance


class OutputNodeOutput(NodeOutput):
    """Output from output preparation node."""
    content: str
    history: List[Dict[str, str]]
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    chunk_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    citation_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    validation_recommendations: Dict[str, Any] = Field(default_factory=dict)


# --- Company Policy Node Models ---

class DocumentDownloadNodeInput(NodeInput):
    """Input for document download node."""
    document_url: str


class DocumentDownloadNodeOutput(NodeOutput):
    """Output from document download node."""
    tmp_file_path: str


class DocumentProcessingNodeInput(NodeInput):
    """Input for document processing node."""
    tmp_file_path: str


class DocumentProcessingNodeOutput(NodeOutput):
    """Output from document processing node."""
    processed_content: str


class PolicyRetrieverNodeInput(NodeInput):
    """Input for policy retriever node."""
    message: str


class PolicyRetrieverNodeOutput(NodeOutput):
    """Output from policy retriever node."""
    policy_context: List[str]
    policy_chunks_with_metadata: List[Dict[str, Any]] = []


class DocumentRetrieverNodeInput(NodeInput):
    """Input for document retriever node."""
    message: str
    tmp_file_path: str


class DocumentRetrieverNodeOutput(NodeOutput):
    """Output from document retriever node."""
    doc_context: List[str]


class ContextCombinationNodeInput(NodeInput):
    """Input for context combination node."""
    message: str
    policy_context: List[str]
    doc_context: List[str]
    history: List[BaseMessage]
    policy_chunks_with_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    doc_chunks_with_metadata: List[Dict[str, Any]] = Field(default_factory=list)


class ContextCombinationNodeOutput(NodeOutput):
    """Output from context combination node."""
    full_user_message: str
    chunk_metadata: List[Dict[str, Any]] = Field(default_factory=list)


class ClaimValidatorNodeInput(NodeInput):
    """Input for claim validator node."""
    llm_response: str
    policy_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    doc_chunks: List[Dict[str, Any]] = Field(default_factory=list)


class ClaimValidatorNodeOutput(NodeOutput):
    """Output from claim validator node."""
    response: str
    citation_metadata: List[Dict[str, Any]] = Field(default_factory=list)


# --- Graph State Models ---

class BaseGraphState(BaseModel):
    """Base state for all graphs."""
    # Core inputs
    session_id: str
    user_id: str
    message: str
    document_url: Optional[str] = None
    intent: str

    # Dependencies (injected, not passed between nodes)
    chat_repository: Optional[Any] = None  # ChatRepository instance

    # Working data (populated by nodes)
    safe_session_id: Optional[str] = None
    history: Optional[List[BaseMessage]] = None
    chunk_metadata: Optional[List[Dict[str, Any]]] = None

    # Final outputs
    response: Optional[str] = None
    content: Optional[str] = None
    
    # Control flags
    final: Optional[bool] = None


class CompanyPolicyState(BaseGraphState):
    """State for company policy graph workflow."""
    # Company policy specific data
    policy_context: Optional[List[str]] = None
    doc_context: Optional[List[str]] = None
    tmp_file_path: Optional[str] = None
    full_user_message: Optional[str] = None
    chunk_metadata: Optional[List[Dict[str, Any]]] = None
    policy_chunks_with_metadata: Optional[List[Dict[str, Any]]] = None
    doc_chunks_with_metadata: Optional[List[Dict[str, Any]]] = None
    
    # Citation validation data
    citation_metadata: Optional[List[Dict[str, Any]]] = None
    validation_recommendations: Optional[Dict[str, Any]] = None


class GeneralPurposeState(BaseGraphState):
    """State for general purpose graph workflow."""
    pass  # General purpose doesn't need additional fields