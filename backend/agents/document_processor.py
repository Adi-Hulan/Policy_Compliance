# import google.generativeai as genai
from utils.pdf_parser import extract_text_from_pdf
from db.connection import get_db
import os
import uuid
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
from google import genai
from typing import List, Optional
from collections import namedtuple

# Chunk namedtuple for the new implementation
Chunk = namedtuple('Chunk', [
    'id', 'content', 'char_start', 'char_end', 'page', 
    'doc_id', 'file_path', 'orig_char_start', 'orig_char_end'
])

class DocumentChunker:
    """Handles document chunking with character offset tracking."""
    
    def __init__(self, sentences_per_chunk: int = 15, overlap: int = 3):
        self.sentences_per_chunk = sentences_per_chunk
        self.overlap = overlap

    def chunk_text_with_offsets(self, text: str, page_texts: Optional[List[str]] = None) -> List[Chunk]:
        """Return list of Chunk with deterministic global char offsets."""
        original_text = text
        norm_text = ' '.join(text.split())

        # Compute page offsets if page texts are provided
        page_offsets = []
        full_text = norm_text
        if page_texts:
            cumulative = 0
            normalized_pages = []
            for p in page_texts:
                p_norm = ' '.join((p or '').split())
                normalized_pages.append(p_norm)
                page_offsets.append((cumulative, p_norm))
                cumulative += len(p_norm)
            full_text = ''.join(normalized_pages)
            original_pages = [p or '' for p in page_texts]
            original_full_text = ''.join(original_pages)
        else:
            original_full_text = original_text

        # Tokenize sentences and find their positions
        sentences = sent_tokenize(full_text)
        sentence_starts = self._find_sentence_positions(sentences, full_text)
        sentence_orig_starts = self._find_sentence_positions(sentences, original_full_text)

        # Create chunks
        chunks = []
        start_idx = 0

        while start_idx < len(sentences):
            end_idx = min(start_idx + self.sentences_per_chunk, len(sentences))
            
            char_start, char_end, orig_char_start, orig_char_end = self._compute_chunk_boundaries(
                sentences, start_idx, end_idx, sentence_starts, sentence_orig_starts
            )

            chunk_text = ' '.join(sentences[start_idx:end_idx])
            page = self._determine_page(char_start, page_offsets)

            chunk_id = f"doc_chunk_{len(chunks)+1}"
            chunks.append(Chunk(
                id=chunk_id, content=chunk_text, 
                char_start=char_start, char_end=char_end,
                orig_char_start=orig_char_start, orig_char_end=orig_char_end,
                page=page, doc_id=None, file_path=None
            ))

            start_idx += self.sentences_per_chunk - self.overlap

        return chunks

    def _find_sentence_positions(self, sentences: List[str], text: str) -> List[int]:
        """Find starting positions of sentences in text."""
        positions = []
        search_pos = 0
        for s in sentences:
            idx = text.find(s, search_pos)
            if idx == -1:
                idx = text.find(s)
                if idx == -1:
                    idx = search_pos
            positions.append(idx)
            search_pos = idx + len(s)
        return positions

    def _compute_chunk_boundaries(self, sentences: List[str], start_idx: int, end_idx: int,
                                sentence_starts: List[int], sentence_orig_starts: List[int]) -> tuple:
        """Compute character boundaries for a chunk."""
        last_sentence = sentences[end_idx - 1]
        char_start = sentence_starts[start_idx]
        char_end = sentence_starts[end_idx - 1] + len(last_sentence)
        orig_char_start = sentence_orig_starts[start_idx]
        orig_char_end = sentence_orig_starts[end_idx - 1] + len(last_sentence)
        return char_start, char_end, orig_char_start, orig_char_end

    def _determine_page(self, char_start: int, page_offsets: List[tuple]) -> Optional[int]:
        """Determine page number based on character offset."""
        if not page_offsets:
            return None
            
        for i, (offset, ptext) in enumerate(page_offsets):
            if offset <= char_start < offset + len(ptext):
                return i + 1
        return None

class DocumentProcessor:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-embedding-001"

    def chunk_text(self, text, sentences_per_chunk=15, overlap=3):
        text = ' '.join(text.split())
        sentences = sent_tokenize(text)
        chunks = []
        start = 0

        while start < len(sentences):
            end = start + sentences_per_chunk
            chunk = " ".join(sentences[start:end])
            chunks.append(chunk)
            start += sentences_per_chunk - overlap  # move with overlap

        return chunks



    def process(self, file_path):
        try:
            # 1. Extract text
            text = extract_text_from_pdf(file_path)
            print(f"Length of text in characters: {len(text)}")
            if not text.strip():
                return {"agent": "DocumentProcessor", "status": "error", "result": "No text found in PDF"}
            
            chunks = self.chunk_text(text)
            
            # 3. Save to pgvector
            conn = get_db()
            cur = conn.cursor()
            i=0

            for chunk in chunks:
                i=i+1
                clean_chunk = chunk.replace("\x00", "")

                try:
                    # Generate embedding using official API
                    result = self.client.models.embed_content(
                        model=self.model,
                        contents=[clean_chunk]  # must be a list
                    )

                    # Extract embedding
                    embedding = result.embeddings[0].values
                    embedding = [float(x) for x in embedding]

                except Exception as e:
                    return {
                        "agent": "DocumentProcessor",
                        "status": "error",
                        "result": str(e)
                    }

                # Generate unique doc_id
                doc_id = str(uuid.uuid4())

                # Insert into DB
                cur.execute(
                    "INSERT INTO documents (id, content, embedding) VALUES (%s, %s, %s)",
                    (doc_id, clean_chunk, embedding)
                )
                print(f"Inserted chunk {i}/{len(chunks)}")


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

class DocumentProcessorV2:
    """Enhanced document processor with offset tracking for citations."""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-embedding-001"
        self.chunker = DocumentChunker()

    def process(self, file_path):
        try:
            # 1. Extract text
            text = extract_text_from_pdf(file_path)
            print(f"Length of text in characters: {len(text)}")
            if not text.strip():
                return {"agent": "DocumentProcessorV2", "status": "error", "result": "No text found in PDF"}
            
            # 2. Create chunks with offset tracking
            chunks = self.chunker.chunk_text_with_offsets(text)
            
            # 3. Save to pgvector with enhanced metadata
            conn = get_db()
            cur = conn.cursor()
            i = 0

            for chunk in chunks:
                i += 1
                clean_chunk = chunk.content.replace("\x00", "")

                try:
                    # Generate embedding using official API
                    result = self.client.models.embed_content(
                        model=self.model,
                        contents=[clean_chunk]  # must be a list
                    )

                    # Extract embedding
                    embedding = result.embeddings[0].values
                    embedding = [float(x) for x in embedding]

                except Exception as e:
                    return {
                        "agent": "DocumentProcessorV2",
                        "status": "error",
                        "result": str(e)
                    }

                # Generate unique doc_id
                doc_id = str(uuid.uuid4())

                # Insert into new table with enhanced metadata
                cur.execute(
                    """INSERT INTO documents_v2 
                       (id, content, embedding, char_start, char_end, page, 
                        file_path, orig_char_start, orig_char_end) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (doc_id, clean_chunk, embedding, chunk.char_start, chunk.char_end, 
                     chunk.page, file_path, chunk.orig_char_start, chunk.orig_char_end)
                )
                print(f"Inserted chunk {i}/{len(chunks)} into documents_v2")

            conn.commit()
            cur.close()
            conn.close()

            return {
                "agent": "DocumentProcessorV2",
                "status": "success",
                "result": f"Document processed into {len(chunks)} chunks with offset tracking and saved to documents_v2",
                "chunks": chunks,  # Add chunks to the result for testing
                "collection_name": f"documents_v2_{os.path.basename(file_path)}"
            }

        except Exception as e:
            return {"agent": "DocumentProcessorV2", "status": "error", "result": str(e)}
