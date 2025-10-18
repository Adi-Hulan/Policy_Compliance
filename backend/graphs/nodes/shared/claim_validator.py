"""
ENHANCED CLAIM VALIDATOR - spaCy + Sentence Transformers + Smart Citations
Complete replacement for the existing claim validator
"""

from typing import List, Dict, Any, Tuple
import re
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from ..models import ClaimValidatorNodeInput, ClaimValidatorNodeOutput

# Initialize models
print("🧠 Loading Enhanced Claim Validator...")
print("   • Sentence Transformer for semantic matching")
print("   • spaCy for intelligent claim extraction")
print("   • Smart citation injection system")

# 1. Sentence Transformer for SEMANTIC matching
_similarity_model = SentenceTransformer('all-mpnet-base-v2')
print("   ✓ Sentence Transformer loaded")

# 2. spaCy for INTELLIGENT claim extraction
import spacy
nlp = spacy.load("en_core_web_sm")
HAS_SPACY = True
print("   ✓ spaCy loaded")

print("✅ Claim Validator ready!")


def extract_claims_with_positions(llm_response: str) -> List[Tuple[str, int, int]]:
    """
    ENHANCED: Use spaCy for intelligent claim extraction with better filtering.
    """
    return extract_claims_spacy_intelligent(llm_response)



def extract_claims_spacy_intelligent(llm_response: str) -> List[Tuple[str, int, int]]:
    """
    Use spaCy's linguistic understanding to extract ONLY factual claims.
    Filters out headers, introductory text, and non-factual sentences.
    """
    claims_with_positions = []
    doc = nlp(llm_response)
    
    for sent in doc.sents:
        sent_text = sent.text.strip()
        start_pos = sent.start_char
        end_pos = sent.end_char
        
        # Use spaCy's linguistic intelligence to identify factual claims
        if is_factual_claim_spacy(sent):
            clean_claim = clean_claim_text(sent_text)
            claims_with_positions.append((clean_claim, start_pos, end_pos))
        else:
            pass  # Filtered out
    
    return claims_with_positions[:12]  # Return most important claims


def is_factual_claim_spacy(sent) -> bool:
    """
    Use spaCy's linguistic features to identify factual policy claims.
    """
    # Skip very short sentences
    if len(sent.text.strip()) < 25 or len(sent) < 5:
        return False
    
    # Filter out headers and introductory text
    if is_header_or_intro_spacy(sent):
        return False
    
    # Use spaCy to detect factual statements
    return has_factual_content_spacy(sent)


def is_header_or_intro_spacy(sent) -> bool:
    """
    Use spaCy to detect headers and introductory text more accurately.
    """
    text = sent.text.lower().strip()
    
    # Pattern-based filtering
    header_indicators = [
        'are as follows', 'the following', 'below are', 'here are',
        'this document', 'outlines', 'policies on', 'company policies',
        'as follows:', 'the company\'s', 'below:'
    ]
    
    if any(indicator in text for indicator in header_indicators):
        return True
    
    # Very short sentences are often headers
    if len(sent) < 8:
        if text.startswith(('•', '*', '-', '#', '##')):
            return True
        if sent[0].is_upper and all(token.is_upper for token in sent if token.is_alpha):
            return True
    
    return False


def has_factual_content_spacy(sent) -> bool:
    """
    Use spaCy's linguistic analysis to identify factual policy statements.
    """
    factual_indicators = 0
    
    # Policy-related nouns
    policy_nouns = {'employee', 'company', 'policy', 'training', 'pto', 'vacation', 
                   'benefit', 'compensation', 'salary', 'development', 'holiday'}
    
    # Factual verbs and modals
    factual_verbs = {'is', 'are', 'has', 'have', 'must', 'should', 'shall', 
                    'will', 'can', 'may', 'requires', 'provides', 'includes',
                    'receives', 'offers', 'allows', 'entitled'}
    
    for token in sent:
        # Count policy nouns
        if token.lemma_ in policy_nouns and token.pos_ in ['NOUN', 'PROPN']:
            factual_indicators += 1
        
        # Count factual verbs
        if token.lemma_ in factual_verbs and token.pos_ == 'VERB':
            factual_indicators += 1
        
        # Strong indicators: money, numbers, dates
        if token.like_num or '$' in token.text or '%' in token.text:
            factual_indicators += 2
        
        # Named entities
        if token.ent_type_ in ['MONEY', 'DATE', 'TIME', 'QUANTITY']:
            factual_indicators += 1
    
    return factual_indicators >= 2


def extract_claims_fallback(llm_response: str) -> List[Tuple[str, int, int]]:
    """
    Fallback claim extraction without spaCy.
    """
    import nltk
    nltk.download('punkt', quiet=True)
    from nltk.tokenize import sent_tokenize
    
    sentences = sent_tokenize(llm_response)
    claims_with_positions = []
    current_pos = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        start_pos = llm_response.find(sentence, current_pos)
        if start_pos == -1:
            continue
            
        end_pos = start_pos + len(sentence)
        current_pos = end_pos
        
        # Basic filtering
        if is_valid_claim_fallback(sentence):
            clean_claim = clean_claim_text(sentence)
            claims_with_positions.append((clean_claim, start_pos, end_pos))
    
    return claims_with_positions[:10]


def is_valid_claim_fallback(text: str) -> bool:
    """
    Simple claim validation without spaCy.
    """
    text_lower = text.lower().strip()
    
    if len(text) < 25 or len(text.split()) < 5:
        return False
    
    # Skip headers
    header_patterns = [
        r'^#+\s', r'^[\d\.]+\s', r'^.*are as follows.*$',
        r'^the company\'s policies on', r'^below are the'
    ]
    
    for pattern in header_patterns:
        if re.match(pattern, text_lower):
            return False
    
    # Must contain factual content
    factual_indicators = [
        'must', 'should', 'shall', 'will', 'can', 'may', 
        'requires', 'provides', 'includes', 'receives',
        'entitled', 'allowed', 'offered', 'eligible',
        '$', 'dollar', 'percent', '%', 'hours', 'days',
        'employee', 'employees', 'company', 'policy'
    ]
    
    return any(indicator in text_lower for indicator in factual_indicators)


def clean_claim_text(text: str) -> str:
    """Clean claim text while preserving meaning."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    return text.strip()


def semantic_similarity(claim: str, chunk_text: str) -> float:
    """
    USE SENTENCE TRANSFORMER for semantic matching.
    This handles LLM rephrasing by understanding meaning, not just words.
    """
    try:
        # Encode both texts into semantic vectors
        claim_embedding = _similarity_model.encode([claim])
        chunk_embedding = _similarity_model.encode([chunk_text])
        
        # Calculate cosine similarity between vectors
        similarity = cosine_similarity(claim_embedding, chunk_embedding)[0][0]
        return float(similarity)
        
    except Exception as e:
        print(f"⚠️  Semantic similarity error: {e}, using fallback")
        return text_similarity(claim, chunk_text)


def text_similarity(claim: str, chunk_text: str) -> float:
    """
    Fallback text-based similarity.
    """
    claim_words = set(claim.lower().split())
    chunk_words = set(chunk_text.lower().split())
    
    if not claim_words:
        return 0.0
    
    overlap = len(claim_words.intersection(chunk_words))
    return overlap / len(claim_words)


def find_best_chunk_semantic(claim: str, chunks: List[Dict]) -> Dict[str, Any]:
    """
    ENHANCED: Use semantic matching with Sentence Transformers.
    This handles LLM rephrasing much better than text overlap.
    """
    if not chunks:
        return None

    best_similarity = 0
    best_chunk = None
    
    print(f"🔍 Finding best semantic match for claim")
    
    # FIRST PASS: Semantic matching (handles rephrasing)
    for i, chunk in enumerate(chunks):
        chunk_text = chunk.get('content', '') or chunk.get('text', '')
        if not chunk_text:
            continue
            
        # USE SENTENCE TRANSFORMER for semantic similarity
        similarity = semantic_similarity(claim, chunk_text)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_chunk = chunk.copy()
            best_chunk['similarity_score'] = similarity
            best_chunk['match_type'] = 'semantic'
    
    # SECOND PASS: If semantic fails, try keyword matching as fallback
    if best_similarity < 0.25:
        best_chunk = find_best_chunk_keyword_fallback(claim, chunks, best_similarity, best_chunk)
    
    # Set confidence levels based on similarity
    if best_chunk:
        similarity = best_chunk['similarity_score']
        if similarity > 0.6:
            best_chunk['confidence'] = 'high'
        elif similarity > 0.4:
            best_chunk['confidence'] = 'medium'
        elif similarity > 0.25:  # Lenient threshold for summarization
            best_chunk['confidence'] = 'low'
        else:
            best_chunk['confidence'] = 'none'
    
    # Ensure essential fields are present in the best chunk
    if best_chunk:
        best_chunk.setdefault('file_path', None)
        best_chunk.setdefault('char_start', None)
        best_chunk.setdefault('char_end', None)
    
    # Debug: Log the best chunk to verify document_info fields
    # if best_chunk:
    #     print(f"[DEBUG] Best chunk: {best_chunk}")
    
    # Calculate char_start based on the position of the chunk's content in the document
    # ONLY if not already provided
    if best_chunk and best_chunk.get('char_start') is None:
        chunk_text = best_chunk.get('content', '') or best_chunk.get('text', '')
        if chunk_text:
            document_text = best_chunk.get('document_text', '')  # Assuming full document text is available
            char_start = document_text.find(chunk_text)
            if char_start != -1:
                best_chunk['char_start'] = char_start
                best_chunk['char_end'] = char_start + len(chunk_text)
    
    # Debug: Log the presence of document_text in chunks
    # for chunk in chunks:
    #     if 'document_text' not in chunk:
    #         print(f"[DEBUG] Missing document_text in chunk: {chunk.get('id', 'unknown')}")
    
    return best_chunk if best_chunk and best_chunk['similarity_score'] > 0.2 else None


def find_best_chunk_keyword_fallback(claim: str, chunks: List[Dict], current_best_similarity: float, current_best_chunk: Dict) -> Dict:
    """
    Keyword-based fallback when semantic matching fails but content is similar.
    """
    best_keyword_similarity = current_best_similarity
    best_keyword_chunk = current_best_chunk
    
    for chunk in chunks:
        chunk_text = chunk.get('content', '') or chunk.get('text', '')
        if not chunk_text:
            continue
            
        # Calculate keyword similarity
        keyword_similarity = text_similarity(claim, chunk_text)
        
                # Boost good keyword matches
                # if keyword_similarity > 0.4:  # Good keyword overlap
                #     boosted_similarity = max(keyword_similarity, 0.35)  # Boost to at least low confidence
                #
                #     if boosted_similarity > best_keyword_similarity:
                #         best_keyword_similarity = boosted_similarity
                #         best_keyword_chunk = chunk.copy()
                #         best_keyword_chunk['similarity_score'] = boosted_similarity
                #         best_keyword_chunk['match_type'] = 'keyword_fallback'
                #         best_keyword_chunk['original_keyword_similarity'] = keyword_similarity
                #
                #         print(f"  🔍 Keyword match: {keyword_similarity:.3f} → {boosted_similarity:.3f}")    return best_keyword_chunk


def inject_citations_with_positions(llm_response: str, citation_metadata: List[Dict]) -> str:
    """
    SMART citation injection: Place markers at natural break points.
    """
    if not citation_metadata:
        return llm_response
    
    # Sort by citation number
    sorted_citations = sorted(citation_metadata, key=lambda x: x.get('citation_number', 0))
    
    # Convert to list for character-level manipulation
    response_chars = list(llm_response)
    inserted_markers = 0
    
    print(f"📝 Injecting {len(sorted_citations)} citations into response")
    
    for citation in sorted_citations:
        citation_number = citation.get('citation_number', 0)
        original_end = citation.get('original_end_pos')
        
        if citation_number == 0 or original_end is None:
            continue
            
        marker = f"[{citation_number}]"
        
        # Calculate base position (adjust for previously inserted markers)
        base_pos = original_end + (inserted_markers * len(marker))
        
        # Find the best position for citation (end of sentence or line)
        best_pos = find_smart_citation_position(response_chars, base_pos)
        
        # Insert the citation marker
        if best_pos <= len(response_chars):
            # Insert marker characters one by one
            for char in reversed(marker):
                response_chars.insert(best_pos, char)
            inserted_markers += 1
    
    final_response = ''.join(response_chars)
    
    # Validation
    citation_markers = re.findall(r'\[\d+\]', final_response)
    print(f"✅ Citation injection complete: {len(citation_markers)} markers added")
    
    return final_response


def find_smart_citation_position(text_chars: List[str], base_pos: int) -> int:
    """
    Find the best position to place a citation marker.
    Prioritizes: end of sentences > end of bullet points > end of lines > original position.
    """
    max_lookahead = 100
    
    # If base position is already at end of text, use it
    if base_pos >= len(text_chars):
        return len(text_chars)
    
    # Look for natural break points AFTER the claim
    for i in range(min(max_lookahead, len(text_chars) - base_pos)):
        current_pos = base_pos + i
        
        # Stop if we reach the end of text
        if current_pos >= len(text_chars):
            return len(text_chars)
        
        current_char = text_chars[current_pos]
        next_char = text_chars[current_pos + 1] if current_pos + 1 < len(text_chars) else ''
        
        # Case 1: End of sentence (.!?) - place citation AFTER punctuation
        if current_char in '.!?':
            # Check if this is truly end of sentence (followed by space or newline)
            if next_char in ' \n' or current_pos + 1 >= len(text_chars):
                return current_pos + 1
        
        # Case 2: End of bullet point (newline followed by bullet or header)
        if current_char == '\n':
            # Look ahead to see if next line starts with bullet, number, or header
            look_ahead = current_pos + 1
            while look_ahead < len(text_chars) and text_chars[look_ahead] == ' ':
                look_ahead += 1
            
            if look_ahead < len(text_chars):
                next_char = text_chars[look_ahead]
                # If next line starts with bullet, number, or header, place citation here
                if next_char in '*•-' or (look_ahead + 1 < len(text_chars) and 
                                         text_chars[look_ahead:look_ahead+2] in ['##', '**']):
                    return current_pos
        
        # Case 3: Double newline (paragraph break) - place citation before break
        if current_char == '\n' and current_pos + 1 < len(text_chars) and text_chars[current_pos + 1] == '\n':
            return current_pos
    
    # If no natural break found, look for the next newline
    for i in range(min(max_lookahead, len(text_chars) - base_pos)):
        current_pos = base_pos + i
        if current_pos < len(text_chars) and text_chars[current_pos] == '\n':
            return current_pos
    
    # Fallback: Use the original position, but ensure we're not in middle of word
    if base_pos < len(text_chars) and text_chars[base_pos] not in ' \n':
        for i in range(min(20, len(text_chars) - base_pos)):
            current_pos = base_pos + i
            if current_pos >= len(text_chars) or text_chars[current_pos] in ' \n':
                return current_pos
    
    return base_pos


# Keep existing function signatures for compatibility
def extract_claims(llm_response: str) -> List[str]:
    """
    Extract claims from LLM response (for evaluation).
    Returns just the claim texts.
    """
    claims_with_positions = extract_claims_with_positions(llm_response)
    return [claim for claim, _, _ in claims_with_positions]


def find_best_chunk_match(claim: str, chunks: List[Dict], threshold: float = 0.4) -> Dict:
    """
    Find best chunk match for evaluation.
    """
    match = find_best_chunk_semantic(claim, chunks)
    if match and match.get('similarity_score', 0) >= threshold:
        return match
    return None


def claim_validator_node(state) -> Dict[str, Any]:
    """
    ENHANCED VALIDATOR: spaCy + Sentence Transformers + Smart Citations
    """
    try:
        input_data = ClaimValidatorNodeInput(
            llm_response=state.response or "",
            policy_chunks=state.policy_chunks_with_metadata or [],
            doc_chunks=state.doc_chunks_with_metadata or []
        )
    except Exception as e:
        raise ValueError(f"Claim validator input validation failed: {e}")

    llm_response = input_data.llm_response
    
    # Add source information to chunks
    policy_chunks = [{**chunk, 'source': 'policy'} for chunk in input_data.policy_chunks]
    doc_chunks = [{**chunk, 'source': 'document'} for chunk in input_data.doc_chunks]
    all_chunks = policy_chunks + doc_chunks

    print(f"🔍 Processing {len(llm_response)} chars, {len(all_chunks)} chunks ({len(policy_chunks)} policy, {len(doc_chunks)} document)")

    try:
        # STEP 1: Enhanced claim extraction with spaCy
        claims_with_positions = extract_claims_with_positions(llm_response)
        print(f"📝 Extracted {len(claims_with_positions)} claims from response")
        
        citation_metadata = []
        documents = []
        hallucinated_claims = []
        citation_counter = 1

        # STEP 2: Semantic matching with Sentence Transformers
        for claim_text, start_pos, end_pos in claims_with_positions:
            print(f"🔍 Processing claim (next citation number {citation_counter})")

            matching_chunk = find_best_chunk_semantic(claim_text, all_chunks)

            if matching_chunk:
                confidence = matching_chunk['confidence']
                similarity = matching_chunk['similarity_score']
                match_type = matching_chunk.get('match_type', 'semantic')
                
                # Support citation metadata stored either at top-level or nested under 'citation'
                citation_block = matching_chunk.get('citation', {}) if isinstance(matching_chunk.get('citation', {}), dict) else {}

                # Resolve fields preferring nested citation block then top-level chunk keys
                resolved_file_path = citation_block.get('file_path') or matching_chunk.get('file_path')
                resolved_char_start = citation_block.get('char_start') if citation_block.get('char_start') is not None else matching_chunk.get('char_start')
                resolved_char_end = citation_block.get('char_end') if citation_block.get('char_end') is not None else matching_chunk.get('char_end')
                # `page` is not computed during ingestion; require only file path + char ranges for highlighting
                # Check if we have the minimum required fields for highlighting
                has_citation_metadata = bool(resolved_file_path) and (resolved_char_start is not None) and (resolved_char_end is not None)

                if has_citation_metadata:
                    print(f"✅ {match_type.upper()} MATCH: {confidence} confidence (score: {similarity:.3f}) - CITATION READY")

                    # Use source from chunk metadata
                    source = matching_chunk.get('source', 'policy')

                    # Build document_info with optional original char ranges if available
                    document_info = {
                        "file_path": resolved_file_path,
                        "char_start": resolved_char_start,
                        "char_end": resolved_char_end,
                    }
                    # Include original char positions if present in citation block
                    if citation_block.get('orig_char_start') is not None:
                        document_info['orig_char_start'] = citation_block.get('orig_char_start')
                    if citation_block.get('orig_char_end') is not None:
                        document_info['orig_char_end'] = citation_block.get('orig_char_end')

                    # Derive a short snippet for frontend preview / fallback search.
                    chunk_preview = (matching_chunk.get('content') or matching_chunk.get('text') or '')
                    snippet = chunk_preview.strip()
                    if len(snippet) > 120:
                        snippet = snippet[:120].rsplit(' ', 1)[0] + '...'

                    citation_metadata.append({
                        "claim": claim_text,
                        "chunk_id": matching_chunk.get('id'),
                        "similarity": similarity,
                        "confidence": confidence,
                        "citation_number": citation_counter,
                        "original_start_pos": start_pos,
                        "original_end_pos": end_pos,
                        "source": source,
                        "match_type": match_type,
                        # Short text snippet helps frontend find the cited region if offsets don't match
                        "snippet": snippet,
                        "document_info": document_info,
                    })
                    citation_counter += 1  # Only increment for citations with metadata
                else:
                    print(f"✅ {match_type.upper()} MATCH: {confidence} confidence (score: {similarity:.3f}) - NO CITATION METADATA - SKIPPING")
                    # Don't create citation entry and don't increment counter
            else:
                # No matching chunk found -> treat as hallucination.
                # Do NOT create a citation entry, but record the hallucinated claim so
                # the orchestrator/previous node can decide to retry or re-query the LLM.
                print(f"❌ NO MATCH FOUND - potential hallucination - recording for retry")
                hallucinated_claims.append({
                    "claim": claim_text,
                    "original_start_pos": start_pos,
                    "original_end_pos": end_pos,
                    "similarity": 0.0,
                    "confidence": "none",
                })
                # Do not increment citation_counter and do not append to citation_metadata
                continue

        # STEP 3: Smart citation injection
        final_response_with_citations = inject_citations_with_positions(llm_response, citation_metadata)
        
        print(f"📄 Response transformed: {len(llm_response)} → {len(final_response_with_citations)} chars")

        citation_markers = re.findall(r'\[\d+\]', final_response_with_citations)
        print(f"🏷️  Citation markers found: {len(citation_markers)}")

        # STEP 4: Collect unique documents from citations
        document_map = {}
        for citation in citation_metadata:
            if not citation.get('hallucination', False) and citation.get('document_info', {}).get('file_path'):
                file_path = citation['document_info']['file_path']
                source = citation.get('source', 'policy')
                doc_id = f"{source}_{file_path}"
                
                if doc_id not in document_map:
                    document_map[doc_id] = {
                        'id': doc_id,
                        'title': os.path.basename(file_path),
                        'url': file_path,  # TODO: Convert to proper URL if needed
                        'type': source,
                        'file_path': file_path
                    }
        
        # Add a frontend-friendly URL for each document when possible
        base_url = os.getenv('PUBLIC_BASE_URL', 'http://localhost:8000').rstrip('/')
        for d in document_map.values():
            fp = d.get('file_path')
            if fp and isinstance(fp, str) and '/uploads/' in fp:
                # map absolute or relative path to a frontend-accessible absolute URL
                filename = os.path.basename(fp)
                d['url'] = f"{base_url}/uploads/{filename}"

        documents = list(document_map.values())
        print(f"📚 Collected {len(documents)} unique documents for highlighting")

        # Show citation preview
        # citation_lines = [line for line in final_response_with_citations.split('\n') if '[' in line and ']' in line]
        # for i, line in enumerate(citation_lines[:4]):
        #     print(f"[CITATION_PREVIEW] Line {i+1}: {line.strip()[:80]}...")

        # Calculate metrics
        high_conf = len([c for c in citation_metadata if c.get('confidence') == 'high'])
        medium_conf = len([c for c in citation_metadata if c.get('confidence') == 'medium'])
        low_conf = len([c for c in citation_metadata if c.get('confidence') == 'low'])
        # Use recorded hallucinated_claims list for hallucination count
        hallucinations = len(hallucinated_claims)

        total_citations = high_conf + medium_conf + low_conf
        precision = total_citations / len(claims_with_positions) if claims_with_positions else 0

        print(f"\n🎯 ENHANCED VALIDATION COMPLETE:")
        print(f"   Architecture: spaCy + Sentence Transformers")
        print(f"   Total claims: {len(claims_with_positions)}")
        print(f"   High confidence: {high_conf}")
        print(f"   Medium confidence: {medium_conf}")
        print(f"   Low confidence: {low_conf}")
        print(f"   Hallucinations: {hallucinations}")
        print(f"   Precision: {precision:.2f}")
        print(f"   Citation markers: {len(citation_markers)}")

        # Return the response WITH injected citations
        output_data = ClaimValidatorNodeOutput(
            response=final_response_with_citations,
            citation_metadata=citation_metadata,
            documents=documents
        )
        
        result = output_data.model_dump()
        result['validation_metrics'] = {
            'total_claims': len(claims_with_positions),
            'high_confidence': high_conf,
            'medium_confidence': medium_conf,
            'low_confidence': low_conf,
            'hallucinations': hallucinations,
            'precision': precision,
            'citation_markers_count': len(citation_markers),
            'using_spacy': HAS_SPACY,
            'using_sentence_transformers': True
        }
        # If any hallucinations were detected, include them and request a retry
        # The orchestrator can inspect `retry_requested` and `hallucinated_claims`
        # to decide to re-run the previous LLM node or take corrective action.
        result['retry_requested'] = True if hallucinated_claims else False
        result['hallucinated_claims'] = hallucinated_claims
        
        return result

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        
        return ClaimValidatorNodeOutput(
            response=llm_response,
            citation_metadata=[]
        ).model_dump()