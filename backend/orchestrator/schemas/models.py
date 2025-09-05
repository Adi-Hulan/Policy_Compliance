from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Any


# Base models
class BaseOutput(BaseModel):
    status: str
    message: Optional[str] = None


# Retriever models
class Chunk(BaseModel):
    id: str
    content: str
    distance: float


class RetrieverInput(BaseModel):
    query: str
    top_k: int = 5


class RetrieverOutput(BaseOutput):
    chunks: Optional[List[Chunk]] = None


# Query Analyzer models
class QueryAnalyzerInput(BaseModel):
    query: str
    chunks: List[Dict[str, Any]]


class QueryAnalyzerOutput(BaseOutput):
    agent: str = "MainQueryAnalyzer"
    result: Optional[str] = None


# Document Processor models
class DocumentProcessorInput(BaseModel):
    file_path: str


class DocumentProcessorOutput(BaseOutput):
    agent: str = "DocumentProcessor"
    result: Optional[str] = None


# User Query models for the complete pipeline
class UserQueryInput(BaseModel):
    query: str


class AnswerOutput(BaseModel):
    answer: str
    source_chunks: Optional[List[Dict[str, Any]]] = None


# Document Upload models for the document processing pipeline
class DocumentUploadInput(BaseModel):
    file_path: str


class DocumentUploadOutput(BaseModel):
    message: str
    chunks_count: Optional[int] = None
