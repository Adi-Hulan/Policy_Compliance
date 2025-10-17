"""
Proof-of-Concept: Citation verification end-to-end

This script is a self-contained test harness to validate the citation idea
without modifying the main pipeline. It performs these steps:

1. Load a document (PDF or plain text)
2. Chunk the document into overlapping chunks and record char offsets + page
3. Store chunks into a new DB table `documents_test_chunks`
4. Accept a user query and retrieve top-k candidate chunks (embedding or TF-IDF fallback)
5. (Optional) Produce a candidate answer with temporary citations. If an LLM API key exists
   it will call the LLM to generate an answer with temporary markers [temp_1], [temp_2].
   Otherwise it will synthesize an answer by concatenating retrieved chunk summaries.
6. Validate each proposed citation using semantic similarity (sentence-transformers if available,
   TF-IDF fallback otherwise). Compute verification score and mark verified/unverified.
7. If a citation fails verification, run a retry: search top-n chunks for better matches.
8. Replace temporary citations with numbered citations [1], [2] and emit a JSON file
   containing the final answer, citations metadata (including file_path + char offsets),
   and quality metrics.

Run:
    python3 backend/scripts/citation_proof_of_concept.py --file path/to/doc.pdf --query "Your question here"

Note: The script tries to use offline libraries (sentence-transformers). If those are not
present, it gracefully falls back to TF-IDF matching so you can run locally without cloud keys.

This is intentionally non-invasive: it creates a single DB table `documents_test_chunks`
and does not touch other application code.
"""

import os
import sys
import uuid
import json
import argparse
import textwrap
from typing import List, Dict, Tuple, Optional
from collections import namedtuple

# Database helper (reuse existing connection util)
try:
    from db.connection import get_db
except Exception:
    # Fallback: require that script is run from repo root where db/connection.py exists
    print("Could not import db.connection.get_db; make sure you run this from repo root." )
    raise

# PDF parsing
from utils.pdf_parser import extract_text_from_pdf

# Tokenization
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
from nltk.tokenize import sent_tokenize

# Optional semantic libraries
HAS_SENT_TRANSFORMER = False
try:
    from sentence_transformers import SentenceTransformer, util as sbert_util
    HAS_SENT_TRANSFORMER = True
except Exception:
    HAS_SENT_TRANSFORMER = False

# Fallback vectorizer
HAS_SKLEARN = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

# Optional LLM (will only be used if GEMINI_API_KEY is available)
HAS_LANGCHAIN_LLM = False
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    from graphs.nodes.shared.llm import _LLM
    HAS_LANGCHAIN_LLM = True
except Exception:
    HAS_LANGCHAIN_LLM = False

# Data containers
Chunk = namedtuple('Chunk', ['id', 'content', 'char_start', 'char_end', 'page', 'doc_id', 'file_path', 'orig_char_start', 'orig_char_end'])

# DB table name
TABLE_NAME = 'documents_test_chunks'

# Utility: simple chunking with offsets. We chunk by sentences groups while tracking char offsets per page.

def chunk_text_with_offsets(text: str, page_texts: Optional[List[str]] = None, sentences_per_chunk: int = 15, overlap: int = 3) -> List[Chunk]:
    """Return list of Chunk with deterministic global char offsets.

    This mirrors the upload route chunking (sentence grouping) but computes
    exact char_start/char_end offsets by scanning the normalized full text
    sequentially. This avoids using naive find() that can match earlier
    duplicates.
    """
    # Keep original extracted text for mapping offsets (do NOT discard)
    original_text = text

    # Normalize whitespace for tokenization consistency with upload pipeline
    norm_text = ' '.join(text.split())

    # If page_texts given, normalize and compute cumulative offsets per page
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
        # Join normalized pages to produce a single canonical full_text
        full_text = ''.join(normalized_pages)
        # Also join original page texts for original offset mapping
        original_pages = [p or '' for p in page_texts]
        original_full_text = ''.join(original_pages)
    else:
        original_full_text = original_text

    sentences = sent_tokenize(full_text)
    chunks = []
    start_idx = 0

    # We will track a pointer into normalized full_text to find sentence boundaries deterministically
    search_pos = 0
    sentence_starts: List[int] = []
    for s in sentences:
        # find the next occurrence of s starting at search_pos in normalized text
        idx = full_text.find(s, search_pos)
        if idx == -1:
            # fallback: try from start (should be rare)
            idx = full_text.find(s)
            if idx == -1:
                idx = search_pos
        sentence_starts.append(idx)
        search_pos = idx + len(s)

    # Map normalized sentence positions back to original_full_text positions by sequential search
    orig_search_pos = 0
    sentence_orig_starts: List[int] = []
    for s in sentences:
        idx = original_full_text.find(s, orig_search_pos)
        if idx == -1:
            # Try a relaxed search after normalizing s similarly
            s_norm = ' '.join(s.split())
            idx = original_full_text.find(s_norm, orig_search_pos)
            if idx == -1:
                # fallback: use current orig_search_pos
                idx = orig_search_pos
        sentence_orig_starts.append(idx)
        orig_search_pos = idx + len(s)

    while start_idx < len(sentences):
        end_idx = min(start_idx + sentences_per_chunk, len(sentences))
        # compute chunk char_start as start of first sentence and char_end as end of last sentence
        first_sentence = sentences[start_idx]
        last_sentence = sentences[end_idx - 1]
        char_start = sentence_starts[start_idx]
        char_end = sentence_starts[end_idx - 1] + len(last_sentence)
        # original offsets
        orig_char_start = sentence_orig_starts[start_idx]
        orig_char_end = sentence_orig_starts[end_idx - 1] + len(last_sentence)

        chunk_sentences = sentences[start_idx:end_idx]
        chunk_text = ' '.join(chunk_sentences)

        # Determine page by locating char_start in page offsets (best effort)
        page = None
        if page_texts and page_offsets:
            for i, (offset, ptext) in enumerate(page_offsets):
                if char_start >= offset and char_start < offset + len(ptext):
                    page = i + 1
                    break

        chunk_id = f"doc_chunk_{len(chunks)+1}"
        chunks.append(Chunk(id=chunk_id, content=chunk_text, char_start=char_start, char_end=char_end, page=page, doc_id=None, file_path=None, orig_char_start=orig_char_start, orig_char_end=orig_char_end))

        start_idx += sentences_per_chunk - overlap

    return chunks


def chunk_by_repo_processor(text: str, sentences_per_chunk: int = 15, overlap: int = 3):
    """If available, reuse the repository's document chunking (sentence grouping)
    so the POC matches the app's chunk boundaries exactly. Returns list of chunk texts.
    Falls back to local sentence-grouping if repo class is unavailable.
    """
    try:
        from agents.document_processor import DocumentProcessor
        dp = DocumentProcessor()
        return dp.chunk_text(text, sentences_per_chunk=sentences_per_chunk, overlap=overlap)
    except Exception:
        # fallback: replicate grouping logic
        text_norm = ' '.join(text.split())
        sentences = sent_tokenize(text_norm)
        chunks = []
        start = 0
        while start < len(sentences):
            end = start + sentences_per_chunk
            chunk = ' '.join(sentences[start:end])
            chunks.append(chunk)
            start += sentences_per_chunk - overlap
        return chunks


# DB helpers

def create_table(conn):
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id UUID PRIMARY KEY,
            doc_id UUID,
            file_path TEXT,
            content TEXT,
            char_start INTEGER,
            char_end INTEGER,
            page INTEGER
        )
    """)
    conn.commit()
    cur.close()


def insert_chunks(conn, chunks: List[Chunk], file_path: str, doc_id: str):
    cur = conn.cursor()
    for c in chunks:
        cur.execute(
            f"INSERT INTO {TABLE_NAME} (id, doc_id, file_path, content, char_start, char_end, page) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (str(uuid.uuid4()), doc_id, file_path, c.content, c.char_start, c.char_end, c.page)
        )
    conn.commit()
    cur.close()


def fetch_chunks_for_doc(conn, doc_id: str) -> List[Dict]:
    cur = conn.cursor()
    cur.execute(f"SELECT id, doc_id, file_path, content, char_start, char_end, page FROM {TABLE_NAME} WHERE doc_id = %s", (doc_id,))
    rows = cur.fetchall()
    cur.close()
    res = []
    for r in rows:
        res.append({
            'id': r[0], 'doc_id': r[1], 'file_path': r[2], 'content': r[3], 'char_start': r[4], 'char_end': r[5], 'page': r[6]
        })
    return res


# Embedding / similarity helpers

def compute_embeddings_texts(texts: List[str]):
    if HAS_SENT_TRANSFORMER:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode(texts, convert_to_tensor=True)
    elif HAS_SKLEARN:
        vect = TfidfVectorizer().fit(texts)
        mat = vect.transform(texts)
        return mat
    else:
        # naive fallback: return list of texts for substring matching
        return texts


def similarity_query(query: str, candidates: List[str], query_emb=None, candidates_emb=None) -> List[Tuple[int, float]]:
    """Return list of (index, score) sorted desc. Supports multiple emb backends."""
    # If we have SBERT tensors
    if HAS_SENT_TRANSFORMER and query_emb is not None and candidates_emb is not None:
        scores = sbert_util.cos_sim(query_emb, candidates_emb)[0].tolist()
        return sorted([(i, float(scores[i])) for i in range(len(scores))], key=lambda x: x[1], reverse=True)

    # If we have sklearn sparse matrices
    if HAS_SKLEARN and query_emb is not None and candidates_emb is not None:
        import numpy as np
        sims = cosine_similarity(query_emb, candidates_emb)[0]
        return sorted([(i, float(sims[i])) for i in range(len(sims))], key=lambda x: x[1], reverse=True)

    # Fallback: naive substring overlap score
    results = []
    for i, cand in enumerate(candidates):
        q_words = set(query.lower().split())
        c_words = set(cand.lower().split())
        overlap = len(q_words & c_words)
        denom = max(1, len(q_words))
        score = overlap / denom
        results.append((i, score))
    return sorted(results, key=lambda x: x[1], reverse=True)


# Simple LLM answer generator (optional)

def generate_candidate_answer(query: str, retrieved_chunks: List[Dict], use_llm: bool = False) -> Tuple[str, List[str]]:
    """Return a candidate answer text and a list of temporary citation markers mapped to chunk ids.
    If LLM not available, build a naive answer and assign markers in retrieved order."""
    temp_citations = []
    if use_llm and HAS_LANGCHAIN_LLM and os.getenv('GEMINI_API_KEY'):
        # Use the same prompt structure as the LLM node
        system_prompt = "You are an assistant that answers questions based on provided document context. Always include citation markers [temp_1], [temp_2], etc. when referencing context information. Map citations to the chunk IDs provided in the context."
        
        # Build context
        context_parts = []
        for i, ch in enumerate(retrieved_chunks[:6]):
            context_parts.append(f"[CAND_{i+1}] ID: {ch['id']}\n{ch['content'][:500]}\n")
        
        user_content = f"Query: {query}\n\nContext:\n{chr(10).join(context_parts)}"
        
        # Merge system prompt with user content (same as LLM node)
        full_content = f"{system_prompt}\n\n{user_content}"
        
        messages = [HumanMessage(content=full_content)]
        resp = _LLM.invoke(messages)
        answer = resp.content
        
        # Parse markers from the answer in order of appearance
        import re
        marker_pattern = r'\[temp_(\d+)\]'
        matches = re.findall(marker_pattern, answer)
        unique_markers = []
        seen = set()
        for m in matches:
            if m not in seen:
                unique_markers.append(f"temp_{m}")
                seen.add(m)
        
        # Map markers to chunks in order of appearance
        temp_citations = []
        for i, marker in enumerate(unique_markers):
            if i < len(retrieved_chunks):
                temp_citations.append((marker, retrieved_chunks[i]['id']))
        return answer, temp_citations

    # Fallback naive answer: concatenate short excerpts and tag with temp markers
    parts = []
    for i, ch in enumerate(retrieved_chunks[:6]):
        marker = f"[temp_{i+1}]"
        excerpt = ch['content'][:300]
        parts.append(f"{excerpt} {marker}")
    answer = "\n\n".join(parts)
    temp_citations = [(f"temp_{i+1}", ch['id']) for i, ch in enumerate(retrieved_chunks[:6])]
    return answer, temp_citations


# Validation routine

# Inline citation validation utilities (was previously in agents/citation_validator.py)
try:
    from sentence_transformers import SentenceTransformer, util as sbert_util
    HAS_SENT_TRANSFORMER = True
except Exception:
    HAS_SENT_TRANSFORMER = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False


def _build_candidate_embeddings(candidates: List[str]):
    if HAS_SENT_TRANSFORMER:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        emb = model.encode(candidates, convert_to_tensor=True)
        return {'type': 'sbert', 'model': model, 'emb': emb}
    if HAS_SKLEARN:
        vect = TfidfVectorizer().fit(candidates)
        mat = vect.transform(candidates)
        return {'type': 'tfidf', 'vect': vect, 'mat': mat}
    return {'type': 'naive', 'candidates': candidates}


def verify_claim_against_chunk(claim: str, chunk_text: str, candidate_emb_obj: dict) -> float:
    if candidate_emb_obj['type'] == 'sbert':
        model = candidate_emb_obj['model']
        cand_emb = candidate_emb_obj['emb']
        q_emb = model.encode([claim], convert_to_tensor=True)
        sim = float(sbert_util.cos_sim(q_emb, cand_emb)[0][0])
        return sim

    if candidate_emb_obj['type'] == 'tfidf':
        vect = candidate_emb_obj['vect']
        mat = candidate_emb_obj['mat']
        q = vect.transform([claim])
        sims = cosine_similarity(q, mat)[0]
        return float(sims[0])

    q_words = set(claim.lower().split())
    c_words = set(chunk_text.lower().split())
    overlap = len(q_words & c_words)
    denom = max(1, len(q_words))
    return overlap / denom


def validate_temp_citations(answer_text: str, temp_citations: List[Tuple[str, str]], chunk_records: Dict[str, Dict], threshold: float = 0.7, retry_top_n: int = 5) -> Tuple[List[Dict], Dict]:
    sentences = sent_tokenize(answer_text)
    candidates = [chunk_records[cid]['content'] for _, cid in temp_citations if cid in chunk_records]
    if not candidates:
        return [], {'total': 0, 'verified': 0, 'avg_score': 0.0}

    emb_obj = _build_candidate_embeddings(candidates)
    citation_results = []
    scores = []

    for marker, chunk_id in temp_citations:
        sentence_idx = None
        for idx, s in enumerate(sentences):
            if marker in s:
                sentence_idx = idx
                break
        claim_text = sentences[sentence_idx] if sentence_idx is not None else answer_text

        if chunk_id in chunk_records:
            base_chunk = chunk_records[chunk_id]['content']
            score = verify_claim_against_chunk(claim_text, base_chunk, emb_obj)
        else:
            score = 0.0

        verified = score >= threshold
        tried_alt = None

        if not verified and retry_top_n > 0:
            all_texts = [v['content'] for v in chunk_records.values()]
            if HAS_SENT_TRANSFORMER:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                all_emb = model.encode(all_texts, convert_to_tensor=True)
                q_emb = model.encode([claim_text], convert_to_tensor=True)
                sims = sbert_util.cos_sim(q_emb, all_emb)[0].tolist()
                ranked = sorted([(i, float(sims[i])) for i in range(len(sims))], key=lambda x: x[1], reverse=True)
            elif HAS_SKLEARN:
                vect = TfidfVectorizer().fit(all_texts + [claim_text])
                mat = vect.transform(all_texts)
                q = vect.transform([claim_text])
                from sklearn.metrics.pairwise import cosine_similarity
                sims = cosine_similarity(q, mat)[0]
                ranked = sorted([(i, float(sims[i])) for i in range(len(sims))], key=lambda x: x[1], reverse=True)
            else:
                ranked = []
                q_words = set(claim_text.lower().split())
                for i, t in enumerate(all_texts):
                    c_words = set(t.lower().split())
                    score_i = len(q_words & c_words) / max(1, len(q_words))
                    ranked.append((i, score_i))
                ranked = sorted(ranked, key=lambda x: x[1], reverse=True)

            for idx, sc in ranked[:retry_top_n]:
                alt_chunk_id = list(chunk_records.keys())[idx]
                alt_chunk = list(chunk_records.values())[idx]['content']
                if sc > score:
                    tried_alt = (alt_chunk_id, sc)
                    score = sc
                    if score >= threshold:
                        chunk_id = alt_chunk_id
                        verified = True
                        break

        scores.append(score)

        citation_results.append({
            'marker': marker,
            'chunk_id': chunk_id,
            'claim_text': claim_text,
            'score': score,
            'verified': verified,
            'chunk_meta': chunk_records.get(chunk_id),
            'retry_alt': tried_alt
        })

    metrics = {'total': len(citation_results), 'verified': sum(1 for c in citation_results if c['verified']), 'avg_score': sum(scores) / len(scores) if scores else 0.0}
    return citation_results, metrics


# High-level POC runner

def run_poc(file_path: str, query: str, db_conn_info: dict = None):
    print("Starting Citation Proof-of-Concept script...")
    # 1. Extract text (PDF or txt)
    if file_path.lower().endswith('.pdf'):
        # Use pdf parser to get text per page
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            page_texts = []
            for p in reader.pages:
                page_texts.append(p.extract_text() or '')
            full_text = ''.join(page_texts)
        except Exception:
            full_text = extract_text_from_pdf(file_path)
            page_texts = None
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        page_texts = None

    print(f"Document length (chars): {len(full_text)}")

    # 2. Chunk with offsets (match upload route defaults: sentences_per_chunk=15, overlap=3)
    chunks = chunk_text_with_offsets(full_text, page_texts, sentences_per_chunk=15, overlap=3)
    print(f"Created {len(chunks)} chunks")

    # 3. Persist chunks to DB
    conn = get_db()
    create_table(conn)
    doc_id = str(uuid.uuid4())
    insert_chunks(conn, chunks, file_path, doc_id)
    print(f"Inserted chunks into DB with doc_id: {doc_id}")

    # 4. Retrieve chunks for doc
    rows = fetch_chunks_for_doc(conn, doc_id)
    # Build chunk_records map by id
    chunk_records = {}
    for r in rows:
        chunk_records[str(r['id'])] = r
    # For simplicity, create a list of candidate dicts in stable order
    candidates = list(chunk_records.values())

    # 5. Retrieve top-k chunks for the query
    # Prefer using the repository's chunk retriever (same logic as chunk retriever) which
    # creates an embedding via the GenAI client and queries pgvector in the DB.
    top_k = 6
    retrieved_chunks = None
    try:
        # Import locally to avoid hard failure if module isn't available in this environment
        from agents.chuck_retriever import Retriever as RepoRetriever

        repo_retriever = RepoRetriever()
        res = repo_retriever.retrieve_chunks(query, top_k=top_k)
        if isinstance(res, dict) and res.get("status") == "success":
            # retriever returns {'status':'success', 'chunks': [...]}
            retrieved_chunks = res.get('chunks', [])
            print(f"Retrieved top {len(retrieved_chunks)} chunks for query via repo retriever")
        else:
            print("Repo retriever returned error or unexpected format, falling back to local retrieval")
            retrieved_chunks = None
    except Exception as e:
        print(f"Could not use repo retriever: {e}; falling back to local retrieval.")
        retrieved_chunks = None

    if retrieved_chunks is None:
        # Fallback: compute embeddings / TF-IDF / naive overlap as before
        candidate_texts = [c['content'] for c in candidates]
        if HAS_SENT_TRANSFORMER:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            cand_emb = model.encode(candidate_texts, convert_to_tensor=True)
            q_emb = model.encode([query], convert_to_tensor=True)
            sims = sbert_util.cos_sim(q_emb, cand_emb)[0].tolist()
            ranked = sorted([(i, float(sims[i])) for i in range(len(sims))], key=lambda x: x[1], reverse=True)
        elif HAS_SKLEARN:
            vect = TfidfVectorizer().fit(candidate_texts + [query])
            cand_mat = vect.transform(candidate_texts)
            q_mat = vect.transform([query])
            from sklearn.metrics.pairwise import cosine_similarity
            sims = cosine_similarity(q_mat, cand_mat)[0]
            ranked = sorted([(i, float(sims[i])) for i in range(len(sims))], key=lambda x: x[1], reverse=True)
        else:
            # naive bag-of-words overlap
            ranked = similarity_query(query, candidate_texts)

        top_indices = [i for i, _ in ranked[:top_k]]
        retrieved_chunks = [candidates[i] for i in top_indices]
        print(f"Retrieved top {len(retrieved_chunks)} chunks for query via local fallback")

    # 6. Generate candidate answer with temporary citations
    use_llm = bool(os.getenv('GEMINI_API_KEY')) and HAS_LANGCHAIN_LLM
    answer_text, temp_citations = generate_candidate_answer(query, retrieved_chunks, use_llm=use_llm)
    print("Candidate answer generated. Temp citations:")
    print(temp_citations)

    # Map temp citation chunk ids to internal stored chunk primary keys
    # Note: generate_candidate_answer used chunk['id'] from DB rows which are UUIDs

    # 7. Validate citations
    # Build chunk_records map keyed by chunk primary key (string)
    # Our `chunk_records` keys are the DB UUIDs; however generate_candidate_answer used these IDs.
    citation_results, metrics = validate_temp_citations(answer_text, temp_citations, chunk_records)
    print("Citation validation metrics:", metrics)

    # 8. Replace temp markers with numbered citations [1], [2]
    final_answer = answer_text
    verified_citations = [c for c in citation_results if c['verified']]
    numbered_map = {}
    for idx, c in enumerate(verified_citations, start=1):
        numbered_map[c['marker']] = str(idx)
    for marker, num in numbered_map.items():
        final_answer = final_answer.replace(f"[{marker}]", f"[{num}]")

    # 9. Prepare UI payload
    ui_citations = []
    for idx, c in enumerate(verified_citations, start=1):
        ui_citations.append({
            'number': idx,
            'chunk_id': c['chunk_id'],
            'score': c['score'],
            'file_path': c['chunk_meta'].get('file_path'),
            'char_start': c['chunk_meta'].get('char_start'),
            'char_end': c['chunk_meta'].get('char_end'),
            'page': c['chunk_meta'].get('page')
        })

    output = {
        'query': query,
        'final_answer': final_answer,
        'metrics': metrics,
        'citations': ui_citations,
        'all_chunks_count': len(candidates)
    }

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f'citation_poc_{doc_id}.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"POC output written to: {out_file}")
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Citation POC')
    parser.add_argument('--file', required=True, help='Path to document (PDF or .txt)')
    parser.add_argument('--query', required=True, help='User query to test')
    args = parser.parse_args()

    run_poc(args.file, args.query)
