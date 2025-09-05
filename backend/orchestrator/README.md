# Policy Compliance Orchestrator

This orchestrator provides a clean, modular architecture for the Policy Compliance system using LangGraph.

## Architecture Overview

The orchestrator follows a clean architecture pattern with the following components:

### 1. Agents
- Located in `/agents/` directory
- Contain the core business logic
- Example: `Retriever`, `QueryAnalyzer`, `DocumentProcessor`

### 2. Nodes
- Located in `/orchestrator/nodes/` directory
- Wrap agents as LangGraph node functions
- Handle input/output conversion and validation
- Example: `retriever_node.py`, `query_analyzer_node.py`

### 3. Schemas
- Located in `/orchestrator/schemas/` directory
- Define Pydantic models for strong typing
- Used for inputs and outputs of nodes
- Example: `RetrieverInput`, `QueryAnalyzerOutput`

### 4. Pipelines
- Located in `/orchestrator/pipelines/` directory
- Define LangGraph graphs connecting nodes
- Control the flow of data between nodes
- Example: `query_pipeline.py`, `document_process_pipeline.py`

### 5. Controller
- Located in `/orchestrator/controller.py`
- Routes requests to the appropriate pipeline
- Provides a single entry point for the Flask API

## Pipelines

The system includes the following pipelines:

1. **Query Pipeline**
   - Handles user queries about company policies
   - Flow: `RetrieverNode` → `QueryAnalyzerNode`
   - Input: User query
   - Output: Answer with source chunks

2. **Document Process Pipeline**
   - Handles uploading and processing of company policy documents
   - Flow: `DocumentProcessorNode`
   - Input: Document file path
   - Output: Processing status and chunks count

3. **Document Query Pipeline**
   - Handles analysis of temporary documents against company policies
   - Flow: `TempDocumentProcessorNode` → (`PolicyRetrieverNode` + `TempRetrieverNode`) → `TempQueryAnalyzerNode`
   - Input: Document file path and query
   - Output: Compliance analysis with source chunks

## Usage

The orchestrator is integrated with Flask routes in the following way:

```python
from orchestrator.controller import Orchestrator

# Initialize the orchestrator
orchestrator = Orchestrator()

# Process a query
result = orchestrator.route({"query": "What is our policy on remote work?"})

# Process a document
result = orchestrator.route({"document": "/path/to/document.pdf"})

# Process a document and query
result = orchestrator.route({
    "document": "/path/to/document.pdf",
    "query": "Is this document compliant with our policies?"
})
```

## Benefits

- **Modularity**: Each component has a single responsibility
- **Type Safety**: All inputs and outputs are strongly typed
- **Testability**: Each node can be tested independently
- **Flexibility**: Pipelines can be reconfigured without changing agent code
- **Maintainability**: Clean separation of concerns
