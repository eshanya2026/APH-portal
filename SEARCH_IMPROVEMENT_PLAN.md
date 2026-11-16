# APH Portal AI Search Engine: Phase 2 Search Improvement Plan

**Document ID:** APH-SEARCH-PLAN-2026-PHASE2  
**Author:** Senior AI/ML Architect, Python Backend Engineer & Multilingual Search Engineer  
**Status:** Proposal Draft — Awaiting User Approval  
**Architecture Guardrails:** Zero External Dependencies (Standard Python 3), Zero Vector Database Bloat, Preserve All Existing URLs and Intranet Portal Features  

---

## 1. Executive Summary & Improvement Objectives

Based on the forensic audit conducted in `SEARCH_AUDIT_REPORT.md` and failure analysis in `SEARCH_FAILURE_TEST_MATRIX.md`, this improvement plan outlines a surgical, phased upgrade to achieve **100% precision across all test queries**.

### Key Architectural Decisions
1. **Preserve Current Zero-Dependency Architecture:**  
   The system will continue to run with native Python 3 (`http.server`, `urllib`, `re`, `json`). No heavy vector databases (Chroma, Pinecone, FAISS) or PyTorch packages will be introduced.
2. **Deterministic Fast-Path Priority:**  
   Deterministic intent resolution operates in **<1.5 ms** with 100% reliability and zero token cost. We will structure intent resolvers into strict hierarchical layers that eliminate collisions between application launching and PDF form requisition.
3. **Close the Security Vulnerability Immediately:**  
   Block HTTP access to `/.env` in `server.py` and remove browser-side key sniffing in `index.html`.

---

## 2. Phased Implementation Roadmap

```mermaid
flowchart LR
    subgraph Phase 2A
        P2A1[App vs Form Disambiguation] --> P2A2[Priority Resolver Hierarchy]
    end
    subgraph Phase 2B
        P2B1[Phonetic Tanglish Expansion] --> P2B2[Tamil Script Transliterations]
    end
    subgraph Phase 2C
        P2C1[Committees Directory Integration] --> P2C2[MOM & Charter Resolvers]
    end
    subgraph Phase 2D
        P2D1[Stopword Weight Suppression] --> P2D2[Exact Domain Entity Boost]
    end
    subgraph Phase 2E
        P2E1[Block HTTP /.env Access] --> P2E2[Remove Client-Side Key Sniffing]
    end

    Phase 2A --> Phase 2B --> Phase 2C --> Phase 2D --> Phase 2E
```

---

## 3. Detailed Phase Breakdown

### Phase 2A: Intent Disambiguation Engine & Priority Hierarchy

#### Objective
Eliminate collisions between **Core Application Launchers** (e.g. HIS Workstation, HRMS Portal, PACS Viewer) and **Administrative/Requisition Forms** (e.g. HIS User Creation PDF).

#### Implementation Details
1. **Refactor HIS Intent Routing (`server.py`):**
   - Create two mutually exclusive classification blocks:
     ```python
     # 1. HIS Application Launch Intent
     is_his_app_launch = (
         not is_other_app_query and
         (is_word_match('his', q_lower) or 'aosta' in q_lower or 'backbone' in q_lower or 'ஹெச்ஐஎஸ்' in q_lower) and
         any(k in q_lower for k in ['login', 'portal', 'software', 'open his', 'his open', 'system', 'workstation', 'திற', 'access his', 'thira']) and
         not any(k in q_lower for k in ['form', 'forms', 'padivam', 'படிவம்', 'creation', 'id create', 'user create', 'apply', 'vinnappam'])
     )

     # 2. HIS Form Requisition Intent
     is_his_form_requisition = (
         not is_other_app_query and
         (is_word_match('his', q_lower) or 'ஹெச்ஐஎஸ்' in q_lower) and
         any(k in q_lower for k in ['form', 'forms', 'padivam', 'படிவம்', 'creation', 'id creation', 'user creation', 'account create', 'access venum', 'access vendum', 'vinnappam'])
     )
     ```
   - In `handle_ai_search()` and `generate_catalog_fallback_result()`, place `is_his_app_launch` **BEFORE** `is_his_form_requisition`.
2. **HR Resignation vs. IT Ticketing Separation:**
   - Ensure the token `'job'` only matches Ticketing when paired with IT hardware/fault keywords (`order`, `repair`, `breakdown`, `fault`, `maintenance`).
   - If `'resignation'`, `'resign'`, `'rajinama'`, or `'relieving'` is present, strictly suppress Ticketing Desk results.

---

### Phase 2B: Multilingual Lexicon & Phonetic Transliteration Expansion

#### Objective
Support colloquial hospital Tamil and Tanglish variations across clinical and administrative staff queries.

#### Implementation Details
1. **Expand `SYNONYMS` Table in `server.py`:**
   ```python
   EXPANDED_SYNONYMS = {
       # HIS System & Forms
       'ஹெச்ஐஎஸ்': 'his aosta backbone hospital information system',
       'திற': 'open launch login portal',
       'திறக்கவும்': 'open launch login portal',
       'thira': 'open launch login portal',
       
       # Resignation & HR
       'rajinama': 'resignation resign relieving exit clearance hrm manual',
       'raajinaama': 'resignation resign relieving exit clearance hrm manual',
       'ராஜினாமா': 'resignation resign relieving exit clearance hrm manual',
       'pathavi vilagal': 'resignation relieving hrm manual',
       'பணி விலகல்': 'resignation relieving hrm manual',
       
       # Internet & Network
       'internet connection': 'wifi employee wireless network form',
       'internet': 'wifi employee wireless network',
       'inaiyam': 'internet wifi network',
       'இணையம்': 'internet wifi network',
       
       # Committees & Governance
       'committee members': 'committees mom charters governance schedule',
       'charter': 'committee charter constitution mom governance',
       'குழு': 'committee charter mom governance',
       
       # Pharmacy & Blood Bank
       'iratha vangi': 'blood bank transfusion stock',
       'ratha vangi': 'blood bank transfusion stock',
       'radha vangi': 'blood bank transfusion stock',
       'raththa vangi': 'blood bank transfusion stock',
       'மருந்தகம்': 'pharmacy drug stores formulary medicine',
   }
   ```
2. **Multi-token Compound Tokenizer Matching:**
   Ensure `expand_tokens()` processes multi-word expressions like `"internet connection request"` and `"quality committee members"` before single tokens are resolved.

---

### Phase 2C: Committee & Governance Indexing Integration

#### Objective
Ensure queries regarding hospital governance, quality committees, HICC, and minutes of meeting route accurately to `./comitee.html` rather than returning raw calendar PDFs.

#### Implementation Details
1. **Dedicated Committee Intent Resolver (`server.py`):**
   ```python
   is_committee_query = any(k in q_lower for k in [
       'committee', 'committees', 'charter', 'charters', 'mom', 'minutes of meeting',
       'governance', 'குழு', 'meeting minutes'
   ])
   ```
2. **Committee Hub Dynamic Response:**
   When a user searches for `"quality committee members"`, `"infection control committee"`, or `"committees list"`:
   - Provide direct links to:
     1. **APH Hospital Committees & MOM Directory** (`./comitee.html`).
     2. Specific Committee Charters (e.g. `Hospital Infection Control Committee (NABH 5th Edition)`).
     3. Recent Minutes of Meeting (e.g. `QC MOM OCT - 2026`).
   - Deliver clear AI guidance explaining that statutory committee charters, member lists, and MOM archives are maintained in the Committees Directory.

---

### Phase 2D: Document Retrieval Scoring Optimization

#### Objective
Prevent generic words like `"form"`, `"procedure"`, `"manual"`, and `"request"` from causing false-positive matches (such as `"rajinama form"` matching antibiotic review forms).

#### Implementation Details
1. **Stopword Penalty Matrix:**
   ```python
   GENERIC_PENALTY_TOKENS = {
       'form', 'forms', 'from', 'padivam', 'படிவம்',
       'manual', 'manuals', 'sop', 'sops', 'guideline', 'guidelines',
       'procedure', 'procedures', 'policy', 'policies',
       'request', 'application', 'vinnappam', 'விண்ணப்பம்'
   }
   ```
2. **Scoring Logic Adjustment:**
   - If an informative domain keyword is matched (e.g. `antibiotics`, `resignation`, `wifi`), allow the generic token to act as a secondary filter.
   - If an informative domain keyword is NOT matched, assign **zero points** to generic penalty tokens to prevent irrelevant fallback matches.

---

### Phase 2E: Security Hardening & Zero-Exposure Architecture

#### Objective
Completely seal environment variables, protect the Gemini API key, and remove unsafe client-side fetch calls.

#### Implementation Details
1. **Block `/.env` in `server.py` Request Handler:**
   ```python
   def do_GET(self):
       # Security Barrier: Reject requests for sensitive environment and system files
       clean_path = urllib.parse.urlparse(self.path).path.lower()
       if clean_path in ['/.env', '/.env.local', '/server.py', '/requirements.txt'] or clean_path.startswith('/.'):
           self.send_response(403)
           self.send_header('Content-Type', 'text/plain; charset=utf-8')
           self.end_headers()
           self.wfile.write(b"403 Forbidden: Access to configuration files is strictly prohibited.")
           return
   ```
2. **Remove Key-Sniffing in `index.html`:**
   - Delete `getClientGeminiKey()` function (lines 3007-3023).
   - Ensure client queries route **exclusively** through the backend `/api/ai-search` endpoint.
   - If the backend is temporarily unreachable, render a local client-side offline message rather than attempting to fetch `/.env` from the client browser.

---

## 4. Verification & Regression Testing Protocol

Following implementation, the 34-query test matrix will be re-executed against the live server. Acceptance requires:
1. **100% Pass Rate** across all 17 mandatory queries.
2. **Zero False Positives** (e.g. "rajinama form" must never return antibiotic review forms).
3. **Zero App/Form Collisions** ("open his" -> HIS Workstation, "open his form" -> User Creation PDF).
4. **Verified Security Verification:** `curl -s -I http://localhost:3000/.env` must return `HTTP 403 Forbidden`.

---

## 5. Phase 1 Completion Confirmation

As mandated by project instructions:
> **"Do not modify production code yet... After completing the audit, stop and wait for approval before implementing Phase 2."**

Phase 1 Audit is fully complete. All findings, test matrices, and improvement plans have been documented in:
1. `SEARCH_AUDIT_REPORT.md`
2. `SEARCH_FAILURE_TEST_MATRIX.md`
3. `SEARCH_IMPROVEMENT_PLAN.md`

**Next Step:** Awaiting user review and authorization to proceed with Phase 2 implementation.

