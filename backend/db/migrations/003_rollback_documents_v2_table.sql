-- Rollback: Drop documents_v2 table
-- Description: Remove the documents_v2 table and its indexes
-- Date: 2025-10-17

-- Drop indexes
DROP INDEX IF EXISTS idx_documents_v2_created_at;
DROP INDEX IF EXISTS idx_documents_v2_page;
DROP INDEX IF EXISTS idx_documents_v2_file_path;
DROP INDEX IF EXISTS idx_documents_v2_embedding;

-- Drop table
DROP TABLE IF EXISTS documents_v2;