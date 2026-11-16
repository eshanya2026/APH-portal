#!/usr/bin/env python3
"""
APH SmartSearch AI — Automated Document Indexing & FTS5 Regression Test Suite
Validates:
1. Document Discovery (Approved PDFs vs excluded applications/spreadsheets)
2. Text Extraction & Page-Numbering Integrity (1-based index matching #page=N)
3. Tamil Unicode Script Preservation
4. SQLite FTS5 Schema, Storage & Full-Text Search
5. Incremental Indexing & SHA-256 Checksum Avoidance
6. Inaccessible & Corrupt Document Fault Tolerance
7. Access Level Classification & Sensitive Content Detection
"""

import os
import sys
import unittest
import tempfile
import sqlite3
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from search_index.database import (
    init_db,
    get_connection,
    upsert_document,
    get_document,
    get_all_documents,
    mark_document_error,
    search_passages,
    classify_access_level,
    detect_sensitive_content,
    generate_doc_id,
    get_indexing_stats,
    ACCESS_PUBLIC,
    ACCESS_STAFF,
    ACCESS_CLINICAL,
    ACCESS_MANAGEMENT
)
from scripts.index_documents import (
    discover_approved_documents,
    index_single_document,
    normalize_and_quote_url
)

class TestDocumentDiscovery(unittest.TestCase):
    """Tests catalog filtering and document identification."""

    def test_discovery_filters_web_apps(self):
        approved, excluded = discover_approved_documents()
        self.assertGreater(len(approved), 400, "Expected >400 approved PDF documents")
        self.assertGreater(len(excluded), 10, "Expected >10 excluded items")

        # Verify no external applications were admitted
        for doc in approved:
            url = doc['url'].lower()
            self.assertFalse(url.endswith('.xlsx'), f"Admitted Excel spreadsheet: {url}")
            self.assertFalse('mapims-hrms' in url, f"Admitted HRMS web app: {url}")
            self.assertFalse('admin/login.aspx' in url, f"Admitted HIS web workstation: {url}")
            self.assertTrue(url.endswith('.pdf') or 'files/' in url, f"Invalid admitted resource: {url}")

    def test_doc_id_stability(self):
        id1 = generate_doc_id("Human Resources Manual (HRM - 2025)", "http://192.168.101.75:3000/files/HRM%202025.pdf")
        id2 = generate_doc_id("Human Resources Manual (HRM - 2025)", "http://192.168.101.75:3000/files/HRM%202025.pdf")
        self.assertEqual(id1, id2, "Document ID generation must be deterministic and stable")
        self.assertTrue(id1.startswith("DOC_HUMAN_RESOURCES_MANUAL"))

    def test_url_quoting(self):
        url = "http://192.168.101.75:3000/files/Qc/Guideline for infection control practices ICU.pdf"
        quoted = normalize_and_quote_url(url)
        self.assertNotIn(" ", quoted, "Quoted URL must not contain spaces")
        self.assertIn("%20", quoted)


class TestAccessClassification(unittest.TestCase):
    """Tests healthcare access classification rules."""

    def test_access_level_rules(self):
        self.assertEqual(
            classify_access_level("Consent Forms", "Informed Consent Tamil", "http://..."),
            ACCESS_PUBLIC
        )
        self.assertEqual(
            classify_access_level("Committees & MOM", "HICC MOM NOV 2025", "http://..."),
            ACCESS_MANAGEMENT
        )
        self.assertEqual(
            classify_access_level("Manuals & SOPs", "Cardiology ICU Manual", "http://..."),
            ACCESS_CLINICAL
        )
        self.assertEqual(
            classify_access_level("IT Forms", "System Request Form", "http://..."),
            ACCESS_STAFF
        )

    def test_sensitive_data_detection(self):
        has_sens, _ = detect_sensitive_content("Employee PAN: ABCDE1234F submitted for verification")
        self.assertTrue(has_sens, "Failed to detect PAN Card pattern")

        has_sens, _ = detect_sensitive_content("Aadhaar: 3456 7890 1234")
        self.assertTrue(has_sens, "Failed to detect Aadhaar number pattern")

        has_sens, _ = detect_sensitive_content("Routine hand hygiene policy guideline")
        self.assertFalse(has_sens, "False positive on routine hospital policy")


class TestDatabaseAndFTS5(unittest.TestCase):
    """Tests SQLite FTS5 database creation, transactions, and search."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_knowledge.db")
        init_db(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_upsert_and_retrieve_document(self):
        doc_data = {
            "doc_id": "DOC_TEST_01",
            "title": "Hospital Infection Control Policy",
            "category": "Clinical Manuals",
            "badge": "Clinical",
            "url": "http://192.168.101.75:3000/files/hic.pdf",
            "file_name": "hic.pdf",
            "file_size": 10240,
            "total_pages": 2,
            "sha256_hash": "testhash12345",
            "access_level": ACCESS_CLINICAL,
            "indexing_status": "INDEXED"
        }
        pages_data = [
            {
                "page_number": 1,
                "section_title": "Scope & Purpose",
                "page_text": "Hospital Infection Control guidelines for all surgical suites.",
                "is_scanned": False
            },
            {
                "page_number": 2,
                "section_title": "Hand Hygiene Protocols",
                "page_text": "Staff must perform hand rubbing with alcohol rub for 20 seconds.",
                "is_scanned": False
            }
        ]
        upsert_document(doc_data, pages_data, db_path=self.db_path)

        doc = get_document("DOC_TEST_01", db_path=self.db_path)
        self.assertIsNotNone(doc)
        self.assertEqual(doc['title'], "Hospital Infection Control Policy")
        self.assertEqual(doc['total_pages'], 2)

        # Verify FTS5 query
        results = search_passages("alcohol rub", db_path=self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['page_number'], 2)
        self.assertIn("alcohol", results[0]['snippet_text'])
        self.assertIn("rub", results[0]['snippet_text'])
        self.assertEqual(results[0]['page_url'], "http://192.168.101.75:3000/files/hic.pdf#page=2")

    def test_tamil_unicode_fts5(self):
        doc_data = {
            "doc_id": "DOC_TAMIL_01",
            "title": "அறுவை சிகிச்சை ஒப்புதல் படிவம்",
            "category": "Consent Forms",
            "badge": "Medicolegal",
            "url": "http://192.168.101.75:3000/files/tamil_consent.pdf",
            "file_name": "tamil_consent.pdf",
            "file_size": 5000,
            "total_pages": 1,
            "sha256_hash": "tamilhash123",
            "access_level": ACCESS_PUBLIC,
            "indexing_status": "INDEXED"
        }
        pages_data = [
            {
                "page_number": 1,
                "section_title": "ஒப்புதல் விதிமுறைகள்",
                "page_text": "அறுவை சிகிச்சை செய்வதற்கு முன்பாக நோயாளி அல்லது உறவினர் ஒப்புதல் கையொப்பம் இட வேண்டும்.",
                "is_scanned": False
            }
        ]
        upsert_document(doc_data, pages_data, db_path=self.db_path)

        res = search_passages("சிகிச்சை", db_path=self.db_path)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['doc_id'], "DOC_TAMIL_01")
        self.assertEqual(res[0]['page_number'], 1)

    def test_fault_tolerance_marks_error(self):
        mark_document_error("DOC_ERR_01", "Missing Document", "http://bad.url/missing.pdf", "HTTP 404 Not Found", db_path=self.db_path)
        doc = get_document("DOC_ERR_01", db_path=self.db_path)
        self.assertIsNotNone(doc)
        self.assertEqual(doc['indexing_status'], "ERROR")
        self.assertIn("404", doc['error_message'])


class TestIncrementalIndexing(unittest.TestCase):
    """Tests SHA-256 skip behavior on unchanged documents."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_knowledge.db")
        self.cache_dir = os.path.join(self.test_dir, "cache")
        init_db(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_skip_matching_hash(self):
        doc = {
            "doc_id": "DOC_SYS_REQ",
            "title": "System Request Form",
            "url": "http://192.168.101.75:3000/files/System%20Request%20Form.pdf",
            "file_name": "System Request Form.pdf",
            "category": "IT Forms",
            "badge": "IT",
            "access_level": ACCESS_STAFF
        }
        # First index run: downloads and indexes
        status1, res1 = index_single_document(doc, cache_dir=self.cache_dir, db_path=self.db_path)
        self.assertEqual(status1, "INDEXED")
        self.assertEqual(res1['pages'], 1)

        # Second index run: detects unchanged hash and skips extraction
        status2, res2 = index_single_document(doc, cache_dir=self.cache_dir, db_path=self.db_path)
        self.assertEqual(status2, "SKIPPED")
        self.assertEqual(res2['reason'], "MATCHING_SHA256")


if __name__ == '__main__':
    unittest.main()
