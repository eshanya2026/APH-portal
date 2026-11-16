# APH SmartSearch AI — Document Indexing & Retrieval Architecture

**Document Version:** 1.0.0-INDEX-ARCH  
**Evaluation Date:** 2026-11-16  
**Scope:** SQLite FTS5 Schema, Ingestion Pipeline, Page-Level Citation Engine & Gemini Synthesis  
**Technology Stack:** Native Python 3, SQLite 3 FTS5, Poppler (`pdftotext`), Google Gemini API  

---

## 1. Architectural Principles

1. **Zero External Vector Databases:** No Pinecone, ChromaDB, Weaviate, or Milvus. Modern SQLite with the **FTS5 (Full-Text Search 5)** extension provides native BM25 token relevance, trigram tokenization, phrase queries, snippet extraction, and sub-millisecond keyword retrieval directly within Python's built-in `sqlite3` library.
2. **Page-Level Grounding & Verifiable Citations:** A hospital worker reading an AI clinical summary must be able to click directly to the verified page number (`http://192.168.101.75:3000/files/HRM%202025.pdf#page=54`) to cross-check hospital policy.
3. **Preserve Phase 2 Determinism First:** System launches, core applications, direct PDF form requests, and intercom lookups are resolved in **Stage 0** (`search_registry.py`) in **<2 ms**, completely bypassing full-text passage retrieval and generative synthesis.
4. **Zero PHI / PII Exfiltration:** Patient Health Information (PHI) and confidential employee records must never be stored in the index or transmitted to Gemini. Only verified institutional policies, manuals, forms, and minutes are indexed.

---

## 2. System Architecture Diagram

```
+---------------------------------------------------------------------------------------------------+
| USER QUERY (English / Tamil Unicode / Tanglish)                                                   |
+---------------------------------------------------------------------------------------------------+
                                  │
                                  ▼
           [STAGE 0: DETERMINISTIC INTENT & REGISTRY RESOLVER]
                   (classify_search_intent & search_registry.py)
                                  │
            Matched Explicit App / Form / Intercom Number?
                       ┌──────────┴──────────┐
                      YES                    NO
                       │                     │
                       ▼                     ▼
           [INSTANT CANONICAL RESULT]    [STAGE 1: BM25 FULL-TEXT RETRIEVAL]
               (Latency: 1.2 - 2.5 ms)        (SQLite FTS5 Full-Text Engine)
            - Launch HIS / PACS / HRMS       - Tokenize query & expand synonyms
            - Open exact form PDF            - Query `document_pages_fts`
            - Show Dept Intercom             - Retrieve top 5 page chunks with BM25
                       │                     │
                       │                     ▼
                       │         [STAGE 2: PASSAGE SNIPPET & CITATION SNAPPING]
                       │             - Extract exact page snippets
                       │             - Assemble verified link: `URL#page=N`
                       │             - Verify document access level
                       │                     │
                       │                     ▼
                       │         [STAGE 3: GROUNDED GEMINI KNOWLEDGE SYNTHESIS]
                       │             - System prompt: Answer ONLY from passages
                       │             - Cite exact document title and page number
                       │             - Output structured JSON answer + links
                       │                     │
                       └──────────┬──────────┘
                                  │
                                  ▼
            [UNIFIED JSON RESPONSE TO BILINGUAL FRONTEND]
             - Markdown answer with citations
             - Clickable card links with `#page=N`
             - Quick follow-up query suggestions
```

---

## 3. Database Schema (SQLite 3 + FTS5)

The database will be stored locally at `data/aph_knowledge_index.db` (~40 MB disk footprint).

### 3.1 Document Metadata Table (`documents`)
Tracks file-level properties, ETags, and incremental re-indexing timestamps:

```sql
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,               -- e.g. "DOC_HRM_2025", "FORM_HIS_USER"
    title TEXT NOT NULL,                  -- "Human Resources Management Manual (HRM - 2025)"
    category TEXT NOT NULL,               -- "HR Forms", "Manuals & SOPs", "Consent Forms"
    badge TEXT NOT NULL,                  -- "HR Manual", "Clinical", "IT Form"
    url TEXT NOT NULL,                    -- "http://192.168.101.75:3000/files/HRM%202025.pdf"
    file_name TEXT NOT NULL,              -- "HRM 2025.pdf"
    file_size INTEGER NOT NULL,           -- Byte size
    total_pages INTEGER NOT NULL,         -- Page count (e.g. 791)
    etag TEXT,                            -- HTTP ETag from file server
    last_modified TEXT,                   -- Last-Modified HTTP header
    sha256_hash TEXT NOT NULL,            -- Content checksum to detect edits
    access_level TEXT DEFAULT 'PUBLIC',   -- 'PUBLIC', 'STAFF', 'CLINICAL', 'MANAGEMENT'
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Page-Level Content Table (`document_pages`)
Stores clean extracted text for every individual page of every document:

```sql
CREATE TABLE IF NOT EXISTS document_pages (
    page_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,         -- 1-based page index (for #page=N)
    section_title TEXT,                   -- Extracted header/clause if present
    page_text TEXT NOT NULL,              -- Extracted UTF-8 plain text
    char_count INTEGER NOT NULL,
    FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_doc_page ON document_pages(doc_id, page_number);
```

### 3.3 SQLite FTS5 Full-Text Virtual Table (`document_pages_fts`)
Provides high-performance BM25 full-text indexing, prefix matching, and keyword highlighting:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS document_pages_fts USING fts5(
    page_id UNINDEXED,                    -- Reference back to document_pages
    doc_id UNINDEXED,                     -- Reference back to documents
    page_number UNINDEXED,                -- Page index
    title,                                -- Document Title
    category,                             -- Category (weighted)
    section_title,                        -- Section Header (weighted)
    page_text,                            -- Body text (stemmed, BM25 searched)
    tokenize = 'unicode61 remove_diacritics 2'
);
```

---

## 4. Extraction & Ingestion Pipeline

### 4.1 Page-Level PDF Text Extraction
Extraction is powered by `/usr/bin/pdftotext` (Poppler utilities):

```python
import subprocess
import os

def extract_pdf_page_text(pdf_path, page_num):
    """
    Extracts plain UTF-8 text from an exact single page.
    Flags:
      -f <page_num>: First page
      -l <page_num>: Last page
      -layout: Preserves columns and table formatting
    """
    cmd = ['pdftotext', '-layout', '-f', str(page_num), '-l', str(page_num), pdf_path, '-']
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
    if res.returncode != 0:
        return ""
    return res.stdout.strip()
```

### 4.2 Text Normalization & Cleaning Rules
1. **Hyphenation Repair:** Fix word wraps across line breaks (e.g., `infec-\ntion` $\rightarrow$ `infection`).
2. **Whitespace Normalization:** Convert multiple spaces and blank lines into single spaces while preserving paragraph breaks.
3. **Header/Footer Stripping:** Detect repeated page headers (`"MAPIMS / NABH / HRM / 09"`) and footer page numbers to prevent keyword skewing.
4. **Bilingual Encoding:** Enforce strict UTF-8 decoding to support Tamil script in consent forms and circulars.

---

## 5. Incremental Re-Indexing & Synchronization

To avoid re-indexing all 429 PDFs on every update:
1. **Head Check:** The indexing script queries the hospital file server (`http://192.168.101.75:3000/files/...`) with an HTTP `HEAD` request.
2. **ETag & Last-Modified Comparison:** If the `ETag` and `Last-Modified` headers match the record in the `documents` table, the document is skipped.
3. **On Change / Addition:**
   - Download the new or updated PDF to a temporary staging folder.
   - Compute SHA-256 checksum.
   - If changed, delete existing rows for `doc_id` from `document_pages` and `document_pages_fts`.
   - Extract and insert updated page records.
   - Update `documents` metadata table.

---

## 6. Retrieval & Gemini Grounding Pipeline

### 6.1 FTS5 Passage Retrieval
When a user query does not trigger an explicit Stage 0 app/form launch:

```sql
SELECT 
    p.page_id,
    p.doc_id,
    d.title,
    d.url,
    p.page_number,
    p.section_title,
    snippet(document_pages_fts, 6, '<b>', '</b>', '...', 32) AS matched_snippet,
    bm25(document_pages_fts, 0.0, 0.0, 0.0, 5.0, 2.0, 3.0, 1.0) AS rank_score
FROM document_pages_fts f
JOIN document_pages p ON f.page_id = p.page_id
JOIN documents d ON p.doc_id = d.doc_id
WHERE document_pages_fts MATCH ?
ORDER BY rank_score ASC
LIMIT 5;
```

### 6.2 Grounded Gemini Prompt Construction
Retrieved passages are injected into a constrained prompt:

```text
You are the APH Hospital AI Knowledge Assistant for Adhiparasakthi Hospitals.
Answer the staff member's query STRICTLY and ONLY using the verified document passages below.

RULES:
1. Answer factually in 2 to 4 concise sentences.
2. If the user asked in Tamil or Tanglish, reply in polite professional Tamil.
3. Cite the EXACT document title and page number for every stated policy or clinical rule (e.g., "[HRM 2025 Manual, Page 54]").
4. Do NOT invent, assume, or extrapolate policies not present in the excerpts.
5. If the excerpts do not contain the answer, state clearly that the official protocol is not available in the retrieved hospital records and provide the primary document link.

VERIFIED HOSPITAL PASSAGES:
[PASSAGE 1]
Document: Human Resources Management Manual (HRM - 2025)
Page: 54
URL: http://192.168.101.75:3000/files/HRM%202025.pdf#page=54
Text: "Resignation Notice Period: All confirmed nursing and administrative staff must serve a mandatory 30-day notice period or pay 1 month gross salary in lieu of notice..."

[PASSAGE 2]
...
```

---

## 7. Security, Privacy & Hospital Boundary Safeguards

1. **Zero Patient Health Information (PHI):**
   - The document crawler indexes only static hospital manuals, policies, and blank forms.
   - Under no circumstances does the crawler index patient discharge summaries, medical charts, or database records from HIS or MRD.
2. **Local Processing of Hospital Text:**
   - Full-text tokenization and passage search run 100% locally on the hospital workstation in SQLite FTS5.
   - Only the specific top 3–5 policy passages needed to answer a query are transmitted to Google Gemini over encrypted HTTPS.
3. **No Training on Hospital Data:**
   - Gemini API calls use the official Enterprise / API tier where prompt data is not retained for model training.
4. **URL & Fragment Snapping:**
   - All URLs returned to the user are validated against the internal catalog. The page fragment (`#page=N`) is attached only if verified against the indexed page count.
