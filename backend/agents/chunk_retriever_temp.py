# import google.generativeai as genai
from db.connection import get_db
import os

# Optional import for Google GenAI SDK. Wrap in try/except so tests can run without the
# library or API keys present. If unavailable, `genai` will be None and the class will
# avoid creating a client until it's needed.
try:
    from google import genai
except Exception:
    genai = None

class TempRetriever:
    def __init__(self):
        # Lazily initialize client if genai is available; otherwise leave None so tests
        # that monkeypatch the retriever can run without the SDK.
        if genai is not None:
            try:
                self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            except Exception:
                self.client = None
        else:
            self.client = None
        self.model = "gemini-embedding-001"

    def retrieve_chunks(self, question, safe_session_id, top_k=5):
        print(f"Retrived Question inside temp_retriever: {question}")
        """
        Returns top-k most relevant chunks from the database for a question.
        """
        try:
            # 1. If embedding client is available, use vector search
            conn = get_db()
            cur = conn.cursor()

            if self.client is not None:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=[question]  # must be a list
                )

                # Ensure it's float list
                question_embedding = result.embeddings[0].values
                print(f"Question Embedding inside the temp chunk retriever (first 5 dims): {question_embedding[:5]}...")
                question_embedding = [float(x) for x in question_embedding]

                query = f"""
                    SELECT id, content, embedding <=> %s::vector AS distance,
                           char_start, char_end, orig_char_start, orig_char_end,
                           page, file_path
                    FROM temp_documents_{safe_session_id}
                    ORDER BY distance
                    LIMIT %s
                """
                cur.execute(query, (question_embedding, top_k))
                results = cur.fetchall()

                # 3. Format results with citation metadata
                chunks = [{
                    "id": r[0],
                    "content": r[1],
                    "distance": r[2],
                    "char_start": r[3],
                    "char_end": r[4],
                    "orig_char_start": r[5],
                    "orig_char_end": r[6],
                    "page": r[7],
                    "file_path": r[8]
                } for r in results]

            else:
                # Fallback: use PostgreSQL full-text search on content when embedding client
                # is not available. This allows local testing and demo without API keys.
                print("[TempRetriever] Embedding client not initialized — falling back to full-text search")
                # Use plainto_tsquery for simple natural language matching
                sql = f"""
                    SELECT id, content, NULL AS distance,
                           char_start, char_end, orig_char_start, orig_char_end,
                           page, file_path,
                           ts_rank(to_tsvector('english', coalesce(content,'')), plainto_tsquery('english', %s)) as rank
                    FROM temp_documents_{safe_session_id}
                    WHERE to_tsvector('english', coalesce(content,'')) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                """
                cur.execute(sql, (question, question, top_k))
                results = cur.fetchall()

                chunks = [{
                    "id": r[0],
                    "content": r[1],
                    "distance": None,
                    "char_start": r[3],
                    "char_end": r[4],
                    "orig_char_start": r[5],
                    "orig_char_end": r[6],
                    "page": r[7],
                    "file_path": r[8]
                } for r in results]

            cur.close()
            conn.close()
            return {"status": "success", "chunks": chunks}

        except Exception as e:
            return {"status": "error", "message": str(e)}