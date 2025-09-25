import google.generativeai as genai
from db.connection import get_db
import os

class TempRetriever:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "models/embedding-001"

    def retrieve_chunks(self, question, session_id, top_k=5):
        print(f"Retrived Question inside temp_retriever: {question}")
        """
        Returns top-k most relevant chunks from the database for a question.
        """
        try:
            # 1. Create embedding for the question
            question_embedding = genai.embed_content(
                model=self.model,
                content=question,
                task_type="retrieval_document"
            )["embedding"]

            # Ensure it's float list
            question_embedding = [float(x) for x in question_embedding]

            # 2. Query pgvector
            conn = get_db()
            cur = conn.cursor()

            query = f"""
                SELECT id, content, embedding <=> %s::vector AS distance
                FROM temp_documents_{session_id}
                ORDER BY distance
                LIMIT %s
            """
            cur.execute(query, (question_embedding, top_k))
            results = cur.fetchall()
            cur.close()
            conn.close()

            # 3. Format results
            chunks = [{"id": r[0], "content": r[1], "distance": r[2]} for r in results]
            return {"status": "success", "chunks": chunks}

        except Exception as e:
            return {"status": "error", "message": str(e)}