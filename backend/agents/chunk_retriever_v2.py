# Enhanced retriever with citation support
from db.connection import get_db
import os
from google import genai
from typing import List, Dict, Any

class RetrieverV2:
    """Enhanced retriever that returns citation information along with chunks."""

    def __init__(self):
        # Initialize client using API key from environment
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-embedding-001"

    def retrieve_chunks_with_citations(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Returns top-k most relevant chunks from documents_v2 table with citation metadata.
        """
        print(f"Retrieved Question in V2: {question}")
        try:
            # 1. Create embedding for the question
            result = self.client.models.embed_content(
                model=self.model,
                contents=[question]  # must be a list
            )

            # Extract the embedding vector (first item because we passed one text)
            question_embedding = result.embeddings[0].values
            question_embedding = [float(x) for x in question_embedding]

            print(f"Question Embedding length: {len(question_embedding)}")
            print(f"Question Embedding (first 5 dims): {question_embedding[:5]}...")

            # 2. Query pgvector with enhanced metadata
            conn = get_db()
            cur = conn.cursor()

            query = """
                SELECT id, content, embedding <=> %s::vector(3072) AS distance,
                       char_start, char_end, orig_char_start, orig_char_end,
                       page, file_path, created_at
                FROM documents_v2
                ORDER BY distance
                LIMIT %s
            """
            cur.execute(query, (question_embedding, top_k))
            results = cur.fetchall()
            cur.close()
            conn.close()

            # 3. Format results with citation metadata
            chunks = []
            for r in results:
                chunk_data = {
                    "id": r[0],
                    "content": r[1],
                    "distance": r[2],
                    "citation": {
                        "char_start": r[3],
                        "char_end": r[4],
                        "orig_char_start": r[5],
                        "orig_char_end": r[6],
                        "page": r[7],
                        "file_path": r[8],
                        "created_at": r[9].isoformat() if r[9] else None
                    }
                }
                chunks.append(chunk_data)

            print(f"Retrieved {len(chunks)} chunks with citations from documents_v2.")
            return {"status": "success", "chunks": chunks}

        except Exception as e:
            print(f"Error in retrieve_chunks_with_citations: {e}")
            return {"status": "error", "message": str(e)}

    def retrieve_chunks(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Backward compatibility method that returns chunks without citation metadata.
        """
        result = self.retrieve_chunks_with_citations(question, top_k)
        if result["status"] == "success":
            # Strip citation metadata for backward compatibility
            simplified_chunks = [
                {
                    "id": chunk["id"],
                    "content": chunk["content"],
                    "distance": chunk["distance"]
                }
                for chunk in result["chunks"]
            ]
            return {"status": "success", "chunks": simplified_chunks}
        return result