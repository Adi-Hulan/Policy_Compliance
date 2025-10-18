-- Migration: Create documents_v2 table with enhanced metadata for citations
-- Description: Add support for document chunks with offset tracking and citation support
-- Date: 2025-10-17

-- Create documents_v2 table with enhanced metadata
CREATE TABLE IF NOT EXISTS documents_v2 (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(3072),  -- Gemini embedding dimension
    char_start INTEGER,
    char_end INTEGER,
    orig_char_start INTEGER,
    orig_char_end INTEGER,
    page INTEGER,
    file_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector extension if not exists (for pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_documents_v2_embedding ON documents_v2 USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_documents_v2_file_path ON documents_v2(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_v2_page ON documents_v2(page);
CREATE INDEX IF NOT EXISTS idx_documents_v2_created_at ON documents_v2(created_at DESC);