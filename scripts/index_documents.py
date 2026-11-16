#!/usr/bin/env python3
"""
APH SmartSearch AI — Document Extraction & Ingestion Engine
Part of Phase 3.2: Document Intelligence Implementation.

Performs:
1. Document Discovery: Reads portal catalog, filters approved PDFs, excludes external apps/spreadsheets,
   generates stable document IDs, and records excluded/duplicate entries.
2. Local Incremental Synchronization: Downloads/caches PDFs locally, compares ETags/Last-Modified/SHA-256,
   and skips unchanged files.
3. Poppler PDF Extraction: Extracts text page-by-page preserving 1-based page numbers and Tamil Unicode,
   detects scanned pages (<50 chars), and flags sensitive content.
4. Atomic SQLite FTS5 Ingestion: Upserts metadata into `documents`, page texts into `document_pages`,
   and synchronizes the `document_pages_fts` virtual table.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import hashlib
import subprocess
import argparse
import re
from typing import Dict, List, Optional, Tuple, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from search_index.database import (
    DEFAULT_DB_PATH,
    init_db,
    get_connection,
    upsert_document,
    mark_document_error,
    get_document,
    classify_access_level,
    detect_sensitive_content,
    generate_doc_id,
    record_indexing_run,
    get_indexing_stats
)

CATALOG_PATH = os.path.join(BASE_DIR, 'data', 'portal_catalog.json')
PDF_CACHE_DIR = os.path.join(BASE_DIR, 'data', 'pdf_cache')

# Approved 5 sample documents for verification testing
SAMPLE_PATTERNS = [
    "HRM 2025",
    "Guideline for infection control practices ICU",
    "Informed Consent Form For Surgery or Procedures-Tamil",
    "System Request Form",
    "HOSPITAL INFECTION CONTROL COMMITTEE"
]

def normalize_and_quote_url(url: str) -> str:
    """Safely normalizes and URL-encodes spaces and special characters in URL path."""
    if not url:
        return ""
    parts = urllib.parse.urlsplit(url.strip())
    # Unquote first to prevent double-encoding, then quote
    quoted_path = urllib.parse.quote(urllib.parse.unquote(parts.path))
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, quoted_path, parts.query, parts.fragment))

def discover_approved_documents(catalog_path: str = CATALOG_PATH) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Discovers approved PDF documents from portal catalog.
    Excludes applications, spreadsheets, directories, and invalid URLs.
    Deduplicates by normalized file name and canonical URL.
    Returns (approved_docs, excluded_docs).
    """
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")

    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    approved = []
    excluded = []
    seen_urls = set()
    seen_filenames = set()

    for item in catalog:
        title = item.get('title', '').strip()
        url = item.get('url', '').strip()
        category = item.get('category', 'Document').strip()
        badge = item.get('badge', 'Resource').strip()

        if not url or url == '#':
            excluded.append({"title": title, "url": url, "reason": "EMPTY_OR_PLACEHOLDER"})
            continue

        # Exclude known web applications
        if any(app_url in url for app_url in [
            '192.168.103.37', '192.168.101.224', 'mapims-hrms', 'mapimsmrd.com',
            'mh.mapims.edu.in', '192.168.103.158', 'mapimshis.com', 'checklist.mapims'
        ]):
            excluded.append({"title": title, "url": url, "reason": "WEB_APPLICATION"})
            continue

        # Exclude spreadsheets
        if url.lower().endswith('.xlsx') or url.lower().endswith('.xls'):
            excluded.append({"title": title, "url": url, "reason": "UNSUPPORTED_SPREADSHEET"})
            continue

        # Exclude internal HTML hubs
        if url.endswith('.html') or '.html?' in url:
            excluded.append({"title": title, "url": url, "reason": "INTERNAL_HTML_PAGE"})
            continue

        # Exclude directory paths or incomplete file URLs
        if url.endswith('/') or not (url.lower().endswith('.pdf') or 'files/' in url):
            excluded.append({"title": title, "url": url, "reason": "DIRECTORY_OR_NON_PDF"})
            continue

        # Canonicalize URL for deduplication
        unquoted_url = urllib.parse.unquote(url)
        file_name = os.path.basename(unquoted_url).strip()

        if not file_name or not file_name.lower().endswith('.pdf'):
            excluded.append({"title": title, "url": url, "reason": "INVALID_PDF_FILENAME"})
            continue

        norm_fname = file_name.lower()
        if unquoted_url in seen_urls or norm_fname in seen_filenames:
            excluded.append({"title": title, "url": url, "reason": "DUPLICATE_ENTRY"})
            continue

        seen_urls.add(unquoted_url)
        seen_filenames.add(norm_fname)

        doc_id = generate_doc_id(title, unquoted_url)
        access_level = classify_access_level(category, title, unquoted_url)

        approved.append({
            "doc_id": doc_id,
            "title": title,
            "url": url,
            "canonical_url": unquoted_url,
            "category": category,
            "badge": badge,
            "file_name": file_name,
            "access_level": access_level
        })

    return approved, excluded

def download_or_get_cached_pdf(
    doc: Dict[str, Any],
    cache_dir: str = PDF_CACHE_DIR,
    timeout: int = 25
) -> Tuple[str, int, str, Optional[str], Optional[str]]:
    """
    Downloads or retrieves cached PDF file.
    Returns (local_path, file_size, sha256_hash, etag, last_modified).
    """
    os.makedirs(cache_dir, exist_ok=True)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', doc['file_name'])
    local_path = os.path.join(cache_dir, clean_name)
    url = normalize_and_quote_url(doc['url'])

    etag = None
    last_modified = None

    # Try sending HEAD request to get HTTP headers
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=8) as resp:
            headers = resp.headers
            etag = headers.get('ETag')
            last_modified = headers.get('Last-Modified')
    except Exception:
        # If HEAD fails or is not supported, proceed with direct GET
        pass

    # Check if we already have the local file
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        with open(local_path, 'rb') as f:
            content = f.read()
        sha256 = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        return local_path, file_size, sha256, etag, last_modified

    # Download file over LAN / HTTP
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'APH-SmartSearch-Indexer/1.0'}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read()

    file_size = len(content)
    if file_size == 0:
        raise ValueError("Downloaded PDF file is 0 bytes.")

    sha256 = hashlib.sha256(content).hexdigest()

    # Save to local cache
    with open(local_path, 'wb') as f:
        f.write(content)

    return local_path, file_size, sha256, etag, last_modified

def extract_pdf_pages_poppler(
    local_path: str,
    max_pages: int = 1500
) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
    """
    Extracts text page-by-page from a PDF using Poppler pdftotext.
    Preserves 1-based exact page numbers and Tamil Unicode.
    Detects scanned pages (<50 characters) and sensitive information.
    Returns (pages_data, requires_review, review_reasons).
    """
    # 1. Run pdfinfo to inspect page count and encryption
    info_cmd = ['pdfinfo', local_path]
    res = subprocess.run(info_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
    if res.returncode != 0:
        raise RuntimeError(f"pdfinfo failed: {res.stderr.strip()[:100]}")

    total_pages = 0
    for line in res.stdout.splitlines():
        if line.startswith('Pages:'):
            total_pages = int(line.split(':')[1].strip())
            break
        if line.startswith('Encrypted:') and 'yes' in line.lower():
            raise PermissionError("PDF is encrypted and cannot be parsed.")

    if total_pages == 0:
        raise ValueError("PDF has 0 pages.")

    if total_pages > max_pages:
        total_pages = max_pages

    # 2. Extract full document with form-feed separation
    txt_cmd = ['pdftotext', '-layout', local_path, '-']
    res = subprocess.run(txt_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {res.stderr.strip()[:100]}")

    raw_pages = res.stdout.split('\x0c')
    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()

    # Fallback to page-by-page extraction if count does not match
    if len(raw_pages) != total_pages:
        raw_pages = []
        for p_num in range(1, total_pages + 1):
            single_cmd = ['pdftotext', '-layout', '-f', str(p_num), '-l', str(p_num), local_path, '-']
            s_res = subprocess.run(single_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            raw_pages.append(s_res.stdout if s_res.returncode == 0 else "")

    pages_data = []
    doc_requires_review = False
    all_reasons = []

    for idx, page_raw in enumerate(raw_pages, start=1):
        # Normalize whitespace while preserving line structure
        lines = [line.rstrip() for line in page_raw.splitlines()]
        # Strip consecutive blank lines
        clean_lines = []
        prev_blank = False
        for l in lines:
            is_blank = (len(l.strip()) == 0)
            if is_blank and prev_blank:
                continue
            clean_lines.append(l)
            prev_blank = is_blank

        clean_text = "\n".join(clean_lines).strip()
        char_count = len(clean_text)

        # Flag scanned page if character count is suspiciously low
        is_scanned = (char_count < 50)

        # Extract plausible section title (first non-empty line of 4-80 chars)
        section_title = ""
        for line in clean_lines:
            stripped = line.strip()
            if 4 <= len(stripped) <= 80 and not stripped.startswith('Page'):
                section_title = stripped
                break

        # Check for sensitive data
        has_sensitive, reason = detect_sensitive_content(clean_text)
        if has_sensitive:
            doc_requires_review = True
            if reason and reason not in all_reasons:
                all_reasons.append(reason)

        pages_data.append({
            "page_number": idx,
            "section_title": section_title,
            "page_text": clean_text,
            "char_count": char_count,
            "word_count": len(clean_text.split()),
            "is_scanned": is_scanned
        })

    review_reason_str = "; ".join(all_reasons) if all_reasons else None
    return pages_data, doc_requires_review, review_reason_str

def index_single_document(
    doc: Dict[str, Any],
    cache_dir: str = PDF_CACHE_DIR,
    db_path: str = DEFAULT_DB_PATH,
    force: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """
    Indexes a single document.
    Returns (status, result_dict) where status in ('INDEXED', 'SKIPPED', 'ERROR').
    """
    doc_id = doc['doc_id']
    title = doc['title']
    url = doc['url']

    # 1. Incremental Check: Check if document exists in DB
    existing = get_document(doc_id, db_path=db_path)
    if existing and existing.get('indexing_status') == 'INDEXED' and not force:
        # Check if local file exists and hash matches
        clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', doc['file_name'])
        cached_file = os.path.join(cache_dir, clean_name)
        if os.path.exists(cached_file) and os.path.getsize(cached_file) > 0:
            with open(cached_file, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            if current_hash == existing.get('sha256_hash'):
                return "SKIPPED", {
                    "doc_id": doc_id,
                    "title": title,
                    "reason": "MATCHING_SHA256",
                    "pages": existing.get('total_pages', 0)
                }

    # 2. Download / Cache PDF
    try:
        local_path, file_size, sha256_hash, etag, last_modified = download_or_get_cached_pdf(
            doc, cache_dir=cache_dir
        )
    except Exception as e:
        err_msg = f"Download failed: {str(e)}"
        mark_document_error(doc_id, title, url, err_msg, db_path=db_path)
        return "ERROR", {"doc_id": doc_id, "title": title, "error": err_msg}

    # Check hash again if we already have indexed version
    if existing and existing.get('sha256_hash') == sha256_hash and existing.get('indexing_status') == 'INDEXED' and not force:
        return "SKIPPED", {
            "doc_id": doc_id,
            "title": title,
            "reason": "UNCHANGED_CONTENT",
            "pages": existing.get('total_pages', 0)
        }

    # 3. Extract Text via Poppler
    try:
        pages_data, requires_review, review_reason = extract_pdf_pages_poppler(local_path)
    except Exception as e:
        err_msg = f"Extraction failed: {str(e)}"
        mark_document_error(doc_id, title, url, err_msg, db_path=db_path)
        return "ERROR", {"doc_id": doc_id, "title": title, "error": err_msg}

    # 4. Atomic Database Upsert
    doc_payload = {
        "doc_id": doc_id,
        "title": title,
        "category": doc.get('category', 'Document'),
        "badge": doc.get('badge', 'Resource'),
        "url": url,
        "file_name": doc['file_name'],
        "file_size": file_size,
        "total_pages": len(pages_data),
        "etag": etag,
        "last_modified": last_modified,
        "sha256_hash": sha256_hash,
        "access_level": doc.get('access_level', 'STAFF'),
        "indexing_status": 'INDEXED',
        "requires_review": requires_review,
        "review_reason": review_reason,
        "error_message": None
    }

    try:
        upsert_document(doc_payload, pages_data, db_path=db_path)
    except Exception as e:
        err_msg = f"Database upsert failed: {str(e)}"
        mark_document_error(doc_id, title, url, err_msg, db_path=db_path)
        return "ERROR", {"doc_id": doc_id, "title": title, "error": err_msg}

    scanned_count = sum(1 for p in pages_data if p.get('is_scanned'))
    return "INDEXED", {
        "doc_id": doc_id,
        "title": title,
        "pages": len(pages_data),
        "scanned_pages": scanned_count,
        "requires_review": requires_review,
        "size_kb": round(file_size / 1024, 1)
    }

def run_indexing_pipeline(
    sample_only: bool = False,
    limit: Optional[int] = None,
    force: bool = False,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Executes the document extraction and indexing pipeline.
    """
    t0 = time.time()
    init_db(db_path)

    print("==================================================================")
    print("APH SmartSearch AI: Document Extraction & Ingestion Engine")
    print(f"Target Database: {db_path}")
    print(f"Local Cache:    {PDF_CACHE_DIR}")
    print("==================================================================\n")

    # 1. Discover Documents
    approved, excluded = discover_approved_documents()
    print(f"📋 Discovery Complete:")
    print(f"   - Approved PDF Documents: {len(approved)}")
    print(f"   - Excluded / Non-PDF Entries: {len(excluded)}")

    # Filter to sample documents if requested
    if sample_only:
        filtered = []
        for pat in SAMPLE_PATTERNS:
            for d in approved:
                if pat.lower() in d['title'].lower() or pat.lower() in d['file_name'].lower():
                    if d not in filtered:
                        filtered.append(d)
        approved = filtered
        print(f"\n🔬 Sample Verification Mode: Testing {len(approved)} approved sample documents.")

    if limit and limit > 0:
        approved = approved[:limit]
        print(f"⚠️ Limited execution: Indexing first {len(approved)} documents.")

    print(f"\n🚀 Commencing extraction & indexing for {len(approved)} documents...\n")

    indexed_count = 0
    skipped_count = 0
    failed_count = 0
    total_pages_count = 0
    scanned_pages_count = 0

    for idx, doc in enumerate(approved, start=1):
        title = doc['title']
        status, res = index_single_document(doc, cache_dir=PDF_CACHE_DIR, db_path=db_path, force=force)

        if status == "INDEXED":
            indexed_count += 1
            pages = res.get('pages', 0)
            scanned = res.get('scanned_pages', 0)
            total_pages_count += pages
            scanned_pages_count += scanned
            rev = " ⚠️ REVIEW" if res.get('requires_review') else ""
            print(f"[{idx:3d}/{len(approved)}] ✅ INDEXED ({pages} pages, {res['size_kb']} KB){rev}: '{title}'")
        elif status == "SKIPPED":
            skipped_count += 1
            pages = res.get('pages', 0)
            total_pages_count += pages
            print(f"[{idx:3d}/{len(approved)}] ⏩ SKIPPED (Unchanged, {pages} pages): '{title}'")
        else:
            failed_count += 1
            print(f"[{idx:3d}/{len(approved)}] ❌ ERROR: '{title}' -> {res.get('error')}")

    duration = time.time() - t0
    stats = get_indexing_stats(db_path)

    run_summary = {
        "total_catalog_docs": len(approved),
        "indexed_docs": indexed_count,
        "skipped_docs": skipped_count,
        "failed_docs": failed_count,
        "total_pages": total_pages_count,
        "scanned_pages": scanned_pages_count,
        "duration_seconds": round(duration, 2),
        "run_type": "SAMPLE" if sample_only else "FULL",
        "status": "SUCCESS" if failed_count == 0 else "PARTIAL",
        "log_summary": f"Indexed {indexed_count}, Skipped {skipped_count}, Failed {failed_count} in {duration:.1f}s"
    }

    record_indexing_run(run_summary, db_path=db_path)

    print("\n==================================================================")
    print("INDEXING PIPELINE SUMMARY")
    print("==================================================================")
    print(f"⏱️  Duration:            {duration:.2f} seconds")
    print(f"📄 Documents Processed: {len(approved)}")
    print(f"   - Newly Indexed:     {indexed_count}")
    print(f"   - Skipped (Clean):   {skipped_count}")
    print(f"   - Failed / Errors:   {failed_count}")
    print(f"📑 Total Pages Extracted: {stats['total_pages']}")
    print(f"🔍 Scanned Pages:        {stats['scanned_pages']}")
    print(f"🚩 Flagged for Review:   {stats['flagged_for_review']}")
    print(f"💾 SQLite Database Size: {stats['db_size_mb']} MB")
    print("==================================================================\n")

    return {**stats, **run_summary}

def main():
    parser = argparse.ArgumentParser(description="APH SmartSearch AI: Document Extraction & Ingestion Engine")
    parser.add_argument("--sample", action="store_true", help="Index only the 5 approved verification sample documents")
    parser.add_argument("--limit", type=int, default=0, help="Limit indexing to first N documents")
    parser.add_argument("--force", action="store_true", help="Force re-extraction even if SHA-256 matches")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Path to SQLite knowledge database")
    parser.add_argument("--stats", action="store_true", help="Display current indexing stats and exit")

    args = parser.parse_args()

    if args.stats:
        if not os.path.exists(args.db):
            print(f"Database does not exist: {args.db}")
            sys.exit(1)
        stats = get_indexing_stats(args.db)
        print(json.dumps(stats, indent=2))
        return

    run_indexing_pipeline(
        sample_only=args.sample,
        limit=args.limit,
        force=args.force,
        db_path=args.db
    )

if __name__ == '__main__':
    main()
