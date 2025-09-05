"""
Policy Compliance Orchestrator

This module provides a clean, modular architecture for orchestrating
the Policy Compliance multi-agent system using LangGraph.
"""

from orchestrator.controller import Orchestrator
from orchestrator.pipelines.query_pipeline import execute_query_pipeline
from orchestrator.pipelines.document_process_pipeline import execute_document_pipeline
from orchestrator.pipelines.document_query_pipeline import execute_document_query_pipeline

__all__ = [
    'Orchestrator',
    'execute_query_pipeline',
    'execute_document_pipeline',
    'execute_document_query_pipeline',
]