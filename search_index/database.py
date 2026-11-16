#!/usr/bin/env python3
"""
APH SmartSearch AI — SQLite FTS5 Database Layer
Provides:
1. Schema initialization for documents, document_pages, document_pages_fts, and indexing_runs.
2. Atomic transactions for document and page upserts, keeping FTS5 index in sync.
3. Access level classification (PUBLIC, STAFF, CLINICAL, MANAGEMENT).
4. Sensitive content detection and review flagging.
5. High-performance BM25 snippet retrieval with sanitization.
"""

import os
import re
import sqlite3
import hashlib
from typing import Dict, List, Optional, Any, Tuple

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data',
    'aph_knowledge_index.db'
)

# Access Level Constants
ACCESS_PUBLIC = "PUBLIC"
ACCESS_STAFF = "STAFF"
ACCESS_CLINICAL = "CLINICAL"
ACCESS_MANAGEMENT = "MANAGEMENT"

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a configured connection to the SQLite knowledge index."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path, timeout=30.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    return con

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes tables, indexes, and FTS5 virtual table."""
    with get_connection(db_path) as con:
        # 1. Document metadata table
        con.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            badge TEXT NOT NULL,
            url TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            total_pages INTEGER NOT NULL,
            etag TEXT,
            last_modified TEXT,
            sha256_hash TEXT NOT NULL,
            access_level TEXT DEFAULT 'STAFF',
            indexing_status TEXT DEFAULT 'INDEXED',
            requires_review BOOLEAN DEFAULT 0,
            review_reason TEXT,
            error_message TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Page-level content table
        con.execute("""
        CREATE TABLE IF NOT EXISTS document_pages (
            page_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            section_title TEXT,
            page_text TEXT NOT NULL,
            char_count INTEGER NOT NULL,
            word_count INTEGER NOT NULL,
            is_scanned BOOLEAN DEFAULT 0,
            FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
        );
        """)

        con.execute("CREATE INDEX IF NOT EXISTS idx_doc_page ON document_pages(doc_id, page_number);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_page_doc_id ON document_pages(doc_id);")

        # 3. Full-Text Search FTS5 Virtual Table
        con.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS document_pages_fts USING fts5(
            page_id UNINDEXED,
            doc_id UNINDEXED,
            page_number UNINDEXED,
            title,
            category,
            section_title,
            page_text,
            tokenize = 'unicode61 remove_diacritics 2'
        );
        """)

        # 4. Indexing run audit history
        con.execute("""
        CREATE TABLE IF NOT EXISTS indexing_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_catalog_docs INTEGER,
            indexed_docs INTEGER,
            skipped_docs INTEGER,
            failed_docs INTEGER,
            total_pages INTEGER,
            scanned_pages INTEGER,
            duration_seconds REAL,
            run_type TEXT DEFAULT 'FULL',
            status TEXT DEFAULT 'SUCCESS',
            log_summary TEXT
        );
        """)

def classify_access_level(category: str, title: str, url: str) -> str:
    """
    Deterministically assigns access levels:
    - PUBLIC: Patient consent forms, holiday calendars, general public info.
    - CLINICAL: Clinical manuals, ICU protocols, consent templates, nursing records.
    - MANAGEMENT: Committee MOMs, quality committee minutes, administrative charters.
    - STAFF: General employee forms, IT requests, HR procedures.
    """
    cat_lower = (category or "").lower()
    title_lower = (title or "").lower()

    if "consent" in cat_lower or "consent" in title_lower:
        return ACCESS_PUBLIC
    if "holiday" in title_lower or "holidays" in title_lower:
        return ACCESS_PUBLIC

    if any(k in cat_lower for k in ["committee", "mom", "governance"]) or any(k in title_lower for k in ["mom ", "mom_", "minutes of meeting", "committee charter"]):
        return ACCESS_MANAGEMENT

    if any(k in cat_lower for k in ["clinical", "infection", "nabh", "icu", "nursing", "pharmacy", "stock", "formulary"]) or \
       any(k in title_lower for k in ["manual", "protocol", "sop", "guideline", "infection", "sbar", "checklist", "antibiotic"]):
        return ACCESS_CLINICAL

    return ACCESS_STAFF

def detect_sensitive_content(text: str) -> Tuple[bool, Optional[str]]:
    """
    Scans text for sensitive patterns (PAN, Aadhaar, bank numbers, salary details).
    Returns (requires_review: bool, reason: str).
    """
    if not text:
        return False, None

    reasons = []
    # Indian PAN Card format: 5 letters, 4 digits, 1 letter
    if re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text):
        reasons.append("Possible PAN Card number detected")

    # Indian Aadhaar 12-digit format
    if re.search(r'\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b', text):
        reasons.append("Possible Aadhaar number detected")

    # Bank Account mention with digits
    if re.search(r'(?i)(bank\s*a/c|account\s*no|ac\s*no)[\s:]+[0-9]{9,18}', text):
        reasons.append("Possible Bank Account details detected")

    # Specific salary amounts with staff names
    if re.search(r'(?i)(basic\s*pay|gross\s*salary|net\s*pay)[\s:]+(?:rs\.?|inr)?\s*[0-9,]+', text):
        reasons.append("Confidential employee salary figures detected")

    if reasons:
        return True, "; ".join(reasons)
    return False, None

def generate_doc_id(title: str, url: str) -> str:
    """Generates a stable, collision-free document ID."""
    clean_title = re.sub(r'[^a-zA-Z0-9]', '_', title.strip()).strip('_').upper()
    clean_title = re.sub(r'_+', '_', clean_title)[:40]
    url_hash = hashlib.sha256(url.strip().encode('utf-8')).hexdigest()[:8].upper()
    return f"DOC_{clean_title}_{url_hash}"

def upsert_document(
    doc_data: Dict[str, Any],
    pages_data: List[Dict[str, Any]],
    db_path: str = DEFAULT_DB_PATH
) -> None:
    """
    Atomically inserts or updates a document and its pages in SQLite and FTS5.
    Guarantees that database remains consistent even on failure.
    """
    doc_id = doc_data['doc_id']
    with get_connection(db_path) as con:
        cur = con.cursor()
        cur.execute("BEGIN TRANSACTION;")
        try:
            # 1. Clean existing records for doc_id
            cur.execute("DELETE FROM document_pages_fts WHERE doc_id = ?;", (doc_id,))
            cur.execute("DELETE FROM document_pages WHERE doc_id = ?;", (doc_id,))
            cur.execute("DELETE FROM documents WHERE doc_id = ?;", (doc_id,))

            # 2. Insert document record
            cur.execute("""
            INSERT INTO documents (
                doc_id, title, category, badge, url, file_name, file_size, total_pages,
                etag, last_modified, sha256_hash, access_level, indexing_status,
                requires_review, review_reason, error_message, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                doc_id,
                doc_data['title'],
                doc_data.get('category', 'Document'),
                doc_data.get('badge', 'Resource'),
                doc_data['url'],
                doc_data.get('file_name', ''),
                doc_data.get('file_size', 0),
                doc_data.get('total_pages', len(pages_data)),
                doc_data.get('etag'),
                doc_data.get('last_modified'),
                doc_data.get('sha256_hash', ''),
                doc_data.get('access_level', ACCESS_STAFF),
                doc_data.get('indexing_status', 'INDEXED'),
                1 if doc_data.get('requires_review') else 0,
                doc_data.get('review_reason'),
                doc_data.get('error_message')
            ))

            # 3. Batch insert pages
            for p in pages_data:
                cur.execute("""
                INSERT INTO document_pages (
                    doc_id, page_number, section_title, page_text,
                    char_count, word_count, is_scanned
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    doc_id,
                    p['page_number'],
                    p.get('section_title', ''),
                    p['page_text'],
                    len(p['page_text']),
                    len(p['page_text'].split()),
                    1 if p.get('is_scanned') else 0
                ))
                page_id = cur.lastrowid

                # 4. Insert into FTS5 virtual table
                cur.execute("""
                INSERT INTO document_pages_fts (
                    page_id, doc_id, page_number, title, category, section_title, page_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    page_id,
                    doc_id,
                    p['page_number'],
                    doc_data['title'],
                    doc_data.get('category', ''),
                    p.get('section_title', ''),
                    p['page_text']
                ))

            con.commit()
        except Exception as e:
            con.rollback()
            raise e

def mark_document_error(
    doc_id: str,
    title: str,
    url: str,
    error_message: str,
    db_path: str = DEFAULT_DB_PATH
) -> None:
    """Records an error status for an inaccessible or unparseable document without wiping other data."""
    with get_connection(db_path) as con:
        con.execute("""
        INSERT INTO documents (
            doc_id, title, category, badge, url, file_name, file_size, total_pages,
            sha256_hash, indexing_status, error_message, updated_at
        ) VALUES (?, ?, 'Error', 'Failed', ?, '', 0, 0, '', 'ERROR', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(doc_id) DO UPDATE SET
            indexing_status = 'ERROR',
            error_message = excluded.error_message,
            updated_at = CURRENT_TIMESTAMP;
        """, (doc_id, title, url, error_message))

def get_document(doc_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves metadata for a specific document ID."""
    with get_connection(db_path) as con:
        row = con.execute("SELECT * FROM documents WHERE doc_id = ?;", (doc_id,)).fetchone()
        return dict(row) if row else None

def get_all_documents(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves all indexed document records."""
    with get_connection(db_path) as con:
        rows = con.execute("SELECT * FROM documents ORDER BY title ASC;").fetchall()
        return [dict(r) for r in rows]

def delete_document(doc_id: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """Deletes a document and all its indexed pages."""
    with get_connection(db_path) as con:
        con.execute("DELETE FROM document_pages_fts WHERE doc_id = ?;", (doc_id,))
        con.execute("DELETE FROM document_pages WHERE doc_id = ?;", (doc_id,))
        con.execute("DELETE FROM documents WHERE doc_id = ?;", (doc_id,))

def sanitize_fts5_query(query: str, mode: str = "AND") -> str:
    """
    Cleans raw user input into a safe FTS5 query string, escaping special operators.
    mode: "AND" or "OR"
    """
    if not query:
        return ""
    # Strip dangerous FTS5 control characters
    cleaned = re.sub(r'["*^~:(){}\[\]]', ' ', query)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    if not tokens:
        return ""
    safe_terms = [f'"{t}"' for t in tokens]
    joiner = f" {mode} "
    return joiner.join(safe_terms)

def search_passages(
    query: str,
    limit: int = 5,
    access_levels: Optional[List[str]] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """
    Executes a BM25 ranked full-text passage query against document_pages_fts.
    Uses strict AND query first, falling back to multi-term OR query with BM25 ranking.
    Returns matched excerpts with exact page numbers and document URLs.
    """
    if not query or not query.strip():
        return []

    def _execute_query(match_expr: str) -> List[Dict[str, Any]]:
        sql = """
        SELECT 
            p.page_id,
            p.doc_id,
            d.title,
            d.category,
            d.badge,
            d.url,
            d.access_level,
            p.page_number,
            p.section_title,
            snippet(document_pages_fts, 6, '<mark>', '</mark>', '...', 28) AS snippet_text,
            bm25(document_pages_fts, 5.0, 2.0, 3.0, 1.0) AS bm25_score
        FROM document_pages_fts f
        JOIN document_pages p ON f.page_id = p.page_id
        JOIN documents d ON p.doc_id = d.doc_id
        WHERE document_pages_fts MATCH ?
        """
        params = [match_expr]

        if access_levels:
            placeholders = ",".join("?" for _ in access_levels)
            sql += f" AND d.access_level IN ({placeholders})"
            params.extend(access_levels)

        sql += " ORDER BY bm25_score ASC LIMIT ?;"
        params.append(limit)

        with get_connection(db_path) as con:
            try:
                rows = con.execute(sql, params).fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    base_url = item['url']
                    page_num = item['page_number']
                    if '#' in base_url:
                        item['page_url'] = base_url
                    else:
                        item['page_url'] = f"{base_url}#page={page_num}"
                    results.append(item)
                return results
            except sqlite3.OperationalError:
                return []

    # 1. Try strict AND query first
    and_expr = sanitize_fts5_query(query, mode="AND")
    results = _execute_query(and_expr) if and_expr else []

    # 2. If no or few results and multi-word query, fall back to ranked OR query
    if len(results) < 2 and " " in query.strip():
        or_expr = sanitize_fts5_query(query, mode="OR")
        if or_expr and or_expr != and_expr:
            or_results = _execute_query(or_expr)
            # Combine without duplicate pages
            seen_pages = {(r['doc_id'], r['page_number']) for r in results}
            for r in or_results:
                key = (r['doc_id'], r['page_number'])
                if key not in seen_pages:
                    results.append(r)
                    seen_pages.add(key)
                if len(results) >= limit:
                    break

    return results[:limit]

def get_indexing_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Computes comprehensive indexing statistics."""
    with get_connection(db_path) as con:
        total_docs = con.execute("SELECT COUNT(*) FROM documents;").fetchone()[0]
        indexed_docs = con.execute("SELECT COUNT(*) FROM documents WHERE indexing_status = 'INDEXED';").fetchone()[0]
        error_docs = con.execute("SELECT COUNT(*) FROM documents WHERE indexing_status = 'ERROR';").fetchone()[0]
        total_pages = con.execute("SELECT COUNT(*) FROM document_pages;").fetchone()[0]
        scanned_pages = con.execute("SELECT COUNT(*) FROM document_pages WHERE is_scanned = 1;").fetchone()[0]
        review_docs = con.execute("SELECT COUNT(*) FROM documents WHERE requires_review = 1;").fetchone()[0]
        total_chars = con.execute("SELECT COALESCE(SUM(char_count), 0) FROM document_pages;").fetchone()[0]

        cat_rows = con.execute("SELECT category, COUNT(*) as cnt FROM documents GROUP BY category ORDER BY cnt DESC;").fetchall()
        categories = {r['category']: r['cnt'] for r in cat_rows}

        access_rows = con.execute("SELECT access_level, COUNT(*) as cnt FROM documents GROUP BY access_level ORDER BY cnt DESC;").fetchall()
        access_levels = {r['access_level']: r['cnt'] for r in access_rows}

        db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        return {
            "total_documents": total_docs,
            "indexed_documents": indexed_docs,
            "error_documents": error_docs,
            "total_pages": total_pages,
            "scanned_pages": scanned_pages,
            "flagged_for_review": review_docs,
            "total_characters": total_chars,
            "categories": categories,
            "access_levels": access_levels,
            "db_size_bytes": db_size_bytes,
            "db_size_mb": round(db_size_bytes / (1024 * 1024), 2)
        }

def record_indexing_run(stats: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> int:
    """Records completion of an indexing run."""
    with get_connection(db_path) as con:
        cur = con.cursor()
        cur.execute("""
        INSERT INTO indexing_runs (
            total_catalog_docs, indexed_docs, skipped_docs, failed_docs,
            total_pages, scanned_pages, duration_seconds, run_type, status, log_summary, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
        """, (
            stats.get('total_catalog_docs', 0),
            stats.get('indexed_docs', 0),
            stats.get('skipped_docs', 0),
            stats.get('failed_docs', 0),
            stats.get('total_pages', 0),
            stats.get('scanned_pages', 0),
            stats.get('duration_seconds', 0.0),
            stats.get('run_type', 'FULL'),
            stats.get('status', 'SUCCESS'),
            stats.get('log_summary', '')
        ))
        con.commit()
        return cur.lastrowid
