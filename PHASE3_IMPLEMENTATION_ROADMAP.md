# APH SmartSearch AI — Phase 3 Implementation Roadmap

**Document Version:** 1.0.0-ROADMAP  
**Evaluation Date:** 2026-11-16  
**Implementation Phases:** Phase 3.2 through Phase 3.5  
**Target Completion:** Enterprise Hospital Knowledge Engine with Zero Vector DB Overhead  

---

## 1. Phased Execution Overview

Phase 3 transitions the search engine from metadata routing to deep document intelligence. To prevent regressions and ensure uninterrupted hospital operations, execution is partitioned into four disciplined stages:

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| PHASE 3 IMPLEMENTATION STAGES                                                                     |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
| Phase 3.1: Analysis & Architecture Design [COMPLETED - THIS DELIVERABLE]                         |
|   - Catalog audit, text extractability forensics, FTS5 schema, and risk assessment                |
|                                                                                                   |
| Phase 3.2: Extraction & Ingestion Pipeline Worker (scripts/index_documents.py)                   |
|   - Poppler text extractor, page chunker, SQLite FTS5 database builder, incremental sync          |
|                                                                                                   |
| Phase 3.3: In-Process Hybrid Search Engine Integration (search_engine.py / server.py)            |
|   - Stage 0 Deterministic Intent check -> Stage 1 FTS5 BM25 Passage Matcher                       |
|                                                                                                   |
| Phase 3.4: Grounded Knowledge Synthesis & Citation Engine                                         |
|   - Gemini prompt injection with page citations, bilingual Tamil/Tanglish reasoning               |
|                                                                                                   |
| Phase 3.5: Rigorous Verification, Staff Benchmarking & Staged Cutover                             |
|   - 50 new clinical passage queries, latency verification, zero-regression audit, production merge|
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Detailed Phase Breakdown

### Phase 3.2: Extraction & Ingestion Worker (`scripts/index_documents.py`)
- **Objective:** Build an offline batch indexing script that reads `data/portal_catalog.json`, downloads/reads PDFs from the hospital file server (`192.168.101.75:3000`), extracts text page-by-page, and constructs `data/aph_knowledge_index.db`.
- **Key Modules:**
  1. `HTTPFileSync`: Fast connection to `192.168.101.75:3000/files/` with ETag caching and conditional HTTP `GET`.
  2. `PopplerPageExtractor`: Wraps `/usr/bin/pdftotext -layout -f N -l N` with 5-second per-page timeouts and UTF-8 sanitization.
  3. `FTS5DatabaseManager`: Manages SQLite transactions, batch inserts (`executemany`), and FTS5 virtual table synchronization.
- **Estimated Build Time:** 1 engineering session.
- **Indexing Duration:** ~3–5 minutes for all 429 PDFs (~5,700 total pages).

### Phase 3.3: In-Process Hybrid Search Engine Integration
- **Objective:** Integrate SQLite FTS5 passage queries into `server.py` without introducing external network dependencies or modifying frontend contracts.
- **Key Modules:**
  1. `KnowledgeRetrievalEngine`: Opens a read-only SQLite connection to `data/aph_knowledge_index.db` at server startup.
  2. `PassageScorer`: Executes BM25 full-text queries against `document_pages_fts`, applying boost factors to Title (5.0), Section (3.0), and Category (2.0).
  3. `SnippetHighlighter`: Extracts clean 30-word context windows around matching clinical keywords.
- **Estimated Build Time:** 1 engineering session.

### Phase 3.4: Grounded Knowledge Synthesis & Citation Engine
- **Objective:** Upgrade `query_gemini_ai` in `server.py` to synthesize clinical answers using retrieved page passages.
- **Key Capabilities:**
  1. Injects top 3–5 page passages with document titles and page numbers into Gemini context.
  2. Synthesizes a factual, 2–4 sentence answer in English or Tamil.
  3. Appends structured page-anchored URLs (e.g. `http://192.168.101.75:3000/files/HRM%202025.pdf#page=54`).
  4. Returns instant fallback if Gemini is offline or rate-limited.
- **Estimated Build Time:** 1 engineering session.

### Phase 3.5: Verification, Benchmarking & Staged Cutover
- **Objective:** Validate search accuracy across 50 realistic clinical and procedural policy questions.
- **Verification Gates:**
  1. **Phase 2 Regression Suite:** Re-run `tests/test_search_regression.py` (Must maintain 24/24 100%).
  2. **Phase 2 34-Query Benchmark:** Re-run `scripts/evaluate_34_queries.py` (Must maintain 34/34 100%).
  3. **Phase 2 150-Query Suite:** Re-run `scripts/evaluate_150_queries.py` (Must maintain 150/150 100%).
  4. **Phase 3 50-Query Policy Knowledge Suite:** New test suite `tests/test_document_knowledge.py` verifying page citation accuracy.

---

## 3. Technical Dependencies & Sizing

| Component | Dependency / Tool | Version | License | Host Availability |
| :--- | :--- | :--- | :--- | :--- |
| **PDF Text Extractor** | `pdftotext` (poppler-utils) | 24.02.0+ | GPL / Open Source | Verified Installed (`/usr/bin/pdftotext`) |
| **PDF Metadata Inspector**| `pdfinfo` (poppler-utils) | 24.02.0+ | GPL / Open Source | Verified Installed (`/usr/bin/pdfinfo`) |
| **Database Engine** | `sqlite3` + FTS5 module | 3.45.0+ | Public Domain | Verified Installed & Enabled in Python |
| **Search Backend** | Python Standard Library | 3.12+ | Python Software License | Native System Python |
| **LLM Synthesis** | Google Gemini API | 2.5 Flash / Flash Lite| Google Cloud Commercial | Server-Side HTTP REST via `urllib` |

### Storage & Hardware Requirements
- **Disk Footprint:**
  - SQLite Index Database (`data/aph_knowledge_index.db`): **35 MB to 50 MB**
  - Temporary PDF extraction buffer: **< 100 MB** (auto-cleaned)
- **RAM Usage:** In-process SQLite requires only **8 MB to 16 MB** of shared buffer memory.
- **CPU Impact:** Microsecond read latency (<1 ms for FTS5 BM25 search); indexing runs as an off-peak maintenance script.

---

## 4. Risk Assessment & Mitigation Matrix

| Risk ID | Identified Risk | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :---: | :---: | :--- |
| **R-01** | **File Server Temporary Downtime** (`192.168.101.75:3000` unreachable) | Medium | Low | Indexer caches PDFs locally in `data/pdf_cache/`. Search runs completely off the local SQLite DB even if the file server is offline. |
| **R-02** | **Over-Reliance on Gemini for Direct App Queries** | High | Low | Stage 0 Deterministic Registry (`search_registry.py`) evaluates *before* FTS5 or Gemini, guaranteeing <2ms launch for `open his`, `open hrms`, etc. |
| **R-03** | **Hallucination of Hospital Policies** | High | Low | Zero-shot grounding prompt with negative constraint: *"If the policy is not explicitly stated in the retrieved passages, respond that it is not in the hospital records."* |
| **R-04** | **Extraction Timeout on Giant PDFs** (`HRM 2025.pdf` - 791 pages) | Medium | Medium | Implement per-page chunking with batch commits every 50 pages; script can be paused and resumed without restarting. |
| **R-05** | **Gemini Quota Exceeded or Network Outage** | Medium | Low | Seamless fallback: When Gemini API call fails, the search engine returns the top matching FTS5 snippets directly to the user interface. |
| **R-06** | **Patient Health Information (PHI) Leakage** | Critical | Negligible | Indexing crawler is restricted strictly to `data/portal_catalog.json` static policy manuals. No access to HIS/MRD patient databases. |

---

## 5. Decision & Next Steps

Phase 3.1 Analysis and Architecture are complete. All four required foundational documents have been generated:

1. [PHASE3_STEP1_ANALYSIS.md](file:///mnt/84F0DAA2F0DA9A2E/aph%20portal/PHASE3_STEP1_ANALYSIS.md)
2. [DOCUMENT_INVENTORY.md](file:///mnt/84F0DAA2F0DA9A2E/aph%20portal/DOCUMENT_INVENTORY.md)
3. [DOCUMENT_INDEXING_ARCHITECTURE.md](file:///mnt/84F0DAA2F0DA9A2E/aph%20portal/DOCUMENT_INDEXING_ARCHITECTURE.md)
4. [PHASE3_IMPLEMENTATION_ROADMAP.md](file:///mnt/84F0DAA2F0DA9A2E/aph%20portal/PHASE3_IMPLEMENTATION_ROADMAP.md)

**Status:** Implementation of Phase 3.2 (Extraction & Ingestion Worker) is stopped and waiting for user approval.
