import google.generativeai as genai
from utils.pdf_parser import extract_text_from_pdf
from db.connection import get_db
import os
import uuid

class DocumentProcessor:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "models/embedding-001"

    def chunck_text(self, text, chuck_size=500, overlap=50):
        words = text.split()
        chunks=[]
        start = 0

        while start < len(words):
            end = start + chuck_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += chuck_size-overlap
        return chunks



    def process(self, file_path):
        try:
            # 1. Extract text
            text = extract_text_from_pdf(file_path)
            if not text.strip():
                return {"agent": "DocumentProcessor", "status": "error", "result": "No text found in PDF"}
            
            chunks = self.chunck_text(text)
            
            # 3. Save to pgvector
            conn = get_db()
            cur = conn.cursor()


            for chunk in chunks:

                clean_chunk = chunk.replace("\x00", "")

                embedding = genai.embed_content(
                    model=self.model,
                    content=clean_chunk,
                    task_type="retrieval_document"
                )["embedding"]
                

                doc_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO documents (id, content, embedding) VALUES (%s, %s, %s)",
                    (doc_id, clean_chunk, embedding)
                )


            conn.commit()
            cur.close()
            conn.close()

            return {
                "agent": "DocumentProcessor",
                "status": "success",
                "result": f"Document processed into {len(chunks)} chunks and saved"
            }

        except Exception as e:
            return {"agent": "DocumentProcessor", "status": "error", "result": str(e)}
