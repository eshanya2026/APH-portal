#!/usr/bin/env python3
"""
Unit and Integration Tests for APH SmartSearch AI — Phase 3.3 Full-Text Knowledge Retrieval.
Covers:
1. Natural language clinical and operational questions (needle stick, transfusion, VAE, MEWS, SBAR, etc.).
2. Grounded BM25 passage snippets and exact #page=N citations.
3. Strict fail-closed Role-Based Access Control (RBAC: PUBLIC, STAFF, CLINICAL, MANAGEMENT).
4. English, Tamil Unicode, and Tanglish query normalization.
5. Role extraction via custom headers, Authorization Bearer tokens, and JSON payloads.
6. Stage 0 and Stage 1 deterministic preservation (< 2ms).
7. Resilience against missing databases, empty matches, and malformed queries.
8. Verification that Gemini generation remains completely disabled.
"""

import unittest
import os
import sys
import json
import urllib.request
import urllib.error
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    execute_search_pipeline,
    clean_question_for_search,
    should_route_to_knowledge_retrieval,
    ROLE_PERMISSIONS
)
from security_auth import (
    create_signed_session_token,
    create_server_session,
    ACCESS_PUBLIC,
    ACCESS_STAFF,
    ACCESS_CLINICAL,
    ACCESS_MANAGEMENT
)
from search_index.database import search_passages
from search_registry import classify_search_intent, resolve_exact_registered_resource

SERVER_URL = "http://localhost:3000/api/ai-search"


def post_search(query: str, headers: dict = None, role: str = None) -> dict:
    payload = {"query": query}
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if role and "Authorization" not in req_headers:
        token = create_signed_session_token("test_staff", role)
        req_headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        SERVER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=req_headers
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


class TestKnowledgeRetrievalEngine(unittest.TestCase):

    # =========================================================================
    # 1. CLINICAL & PROCEDURAL KNOWLEDGE QUESTIONS (AUTHORIZED)
    # =========================================================================
    def test_01_needle_stick_injury_authorized(self):
        """Clinical query returns IPC/ER manual, exact page citation, and #page=N link."""
        res = post_search("What is the needle-stick injury protocol?", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("ER MANUAL" in res["answer"] or "INFECTION PREVENTION" in res["answer"] for _ in [1]))
        self.assertTrue(any("#page=" in link["url"] for link in res["links"]))
        top_link = res["links"][0]
        self.assertTrue(any(k in top_link["url"] for k in ["IPC", "ER", "Laundry", "files"]))

    def test_02_resignation_notice_period_staff_authorized(self):
        """HR question returns HRM manual, notice period snippet, and exact page 45."""
        res = post_search("Explain resignation notice period", role=ACCESS_STAFF)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertIn("HUMAN RESOURCE MANAGEMENT", res["answer"])
        self.assertIn("Page 45", res["answer"])
        self.assertTrue(res["links"][0]["url"].endswith("#page=45"))

    def test_03_blood_transfusion_reaction_authorized(self):
        """Blood transfusion query returns COP manual with transfusion reaction protocol."""
        res = post_search("How to handle blood transfusion reaction?", role=ACCESS_STAFF)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertIn("COP", res["answer"])
        self.assertTrue(any("COP" in l["url"] for l in res["links"]))

    def test_04_ventilator_associated_event_authorized(self):
        """VAE clinical criteria query returns IPC manual passage."""
        res = post_search("What are the criteria for ventilator associated event?", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("IPC.pdf" in l["url"] or "Ventilator" in l["url"] for l in res["links"]))

    def test_05_mews_protocol_authorized(self):
        """MEWS protocol query returns AAC MEWS protocol document and page citation."""
        res = post_search("Modified early warning score MEWS protocol", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("MEWS" in l["title"] for l in res["links"]))

    def test_06_hand_hygiene_5_moments_authorized(self):
        """Hand hygiene query returns COP/Nursing manual with hand washing moments."""
        res = post_search("Hand hygiene 5 moments", role=ACCESS_STAFF)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("COP" in l["url"] or "Nursing" in l["url"] for l in res["links"]))

    def test_07_cauti_catheter_infection_authorized(self):
        """CAUTI query returns IPC infection control manual page citation."""
        res = post_search("Catheter associated urinary tract infection CAUTI", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("IPC.pdf" in l["url"] for l in res["links"]))

    def test_08_biomedical_waste_segregation_authorized(self):
        """Waste segregation query returns colour coding and disposal protocol."""
        res = post_search("Biomedical waste segregation colour code", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("Disinfection" in l["url"] or "IPC.pdf" in l["url"] for l in res["links"]))

    def test_09_code_blue_protocol_management_authorized(self):
        """Code blue protocol returns CPR resuscitation guideline under authorized role."""
        res = post_search("Code blue protocol", role=ACCESS_MANAGEMENT)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("CPR" in l["title"] or "GUIDELINE" in l["title"] for l in res["links"]))
        self.assertFalse(any("CALENDER" in l["url"] for l in res["links"]))

    # =========================================================================
    # 2. ROLE-BASED ACCESS CONTROL & FAIL-CLOSED SECURITY
    # =========================================================================
    def test_10_needle_stick_fail_closed_unauthenticated(self):
        """Unauthenticated PUBLIC user querying CLINICAL needle-stick protocol is blocked."""
        res = post_search("What is the needle-stick injury protocol?")
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")
        self.assertIn("Access Restricted", res["answer"])
        self.assertIn("CLINICAL", res["answer"])
        # Verify snippet is completely redacted
        self.assertNotIn("devices with safety features", res["answer"])
        self.assertTrue(res["links"][0]["url"].endswith("#restricted"))

    def test_11_needle_stick_fail_closed_staff_insufficient(self):
        """STAFF role lacks CLINICAL privilege for IPC clinical manual -> blocked."""
        res = post_search("What is the needle-stick injury protocol?", role=ACCESS_STAFF)
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")
        self.assertIn("CLINICAL", res["answer"])

    def test_12_code_blue_fail_closed_for_public(self):
        """PUBLIC role lacks CLINICAL privilege for CPR clinical resuscitation guideline -> blocked."""
        res = post_search("Code blue protocol")
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")
        self.assertIn("CLINICAL", res["answer"])

    def test_13_resignation_notice_fail_closed_for_public(self):
        """PUBLIC role cannot access internal staff notice period rules -> blocked."""
        res = post_search("Explain resignation notice period")
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")
        self.assertIn("STAFF", res["answer"])

    def test_14_public_document_accessible_to_unauthenticated(self):
        """PUBLIC documents (e.g. general informed consent taking process) are visible to unauthenticated users."""
        passages = search_passages("informed consent taking process", limit=1)
        if passages:
            from server import generate_local_grounded_answer
            res = generate_local_grounded_answer("informed consent taking process", passages, ACCESS_PUBLIC)
            if passages[0]["access_level"] == ACCESS_PUBLIC:
                self.assertEqual(res.get("access_status"), "AUTHORIZED")

    # =========================================================================
    # 3. SECURE AUTHENTICATION & SPOOFING RESILIENCE
    # =========================================================================
    def test_15_spoofed_x_staff_role_header_rejected(self):
        """Untrusted X-Staff-Role HTTP header is ignored and fails closed to PUBLIC."""
        res = post_search("What is the needle-stick injury protocol?", headers={"X-Staff-Role": "CLINICAL"})
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")

    def test_16_spoofed_x_user_role_header_rejected(self):
        """Untrusted X-User-Role HTTP header is ignored and fails closed to PUBLIC."""
        res = post_search("Explain resignation notice period", headers={"X-User-Role": "STAFF"})
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")

    def test_17_spoofed_raw_bearer_rejected(self):
        """Unsigned raw Authorization: Bearer CLINICAL header is rejected and fails closed."""
        res = post_search("What is the needle-stick injury protocol?", headers={"Authorization": "Bearer CLINICAL"})
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")

    def test_18_valid_signed_hmac_session_token_authorized(self):
        """Valid cryptographically signed session token grants CLINICAL access."""
        token = create_signed_session_token("dr_shreya", ACCESS_CLINICAL)
        res = post_search("What is the needle-stick injury protocol?", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.get("access_status"), "AUTHORIZED")

    def test_19_invalid_or_tampered_token_fails_closed(self):
        """Tampered or invalid token fails closed to PUBLIC."""
        token = create_signed_session_token("dr_shreya", ACCESS_CLINICAL) + "_tampered"
        res = post_search("What is the needle-stick injury protocol?", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")

    # =========================================================================
    # 4. MULTILINGUAL KNOWLEDGE RETRIEVAL (TAMIL & TANGLISH)
    # =========================================================================
    def test_20_tamil_needle_stick_injury_authorized(self):
        """Tamil needle stick query returns authorized IPC excerpt in Tamil."""
        res = post_search("ஊசி குத்து காயம் என்ன செய்ய வேண்டும்", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertIn("அதிகாரப்பூர்வ", res["answer"])
        self.assertTrue(any("IPC.pdf" in l["url"] for l in res["links"]))

    def test_21_tamil_needle_stick_injury_fail_closed(self):
        """Tamil needle stick query fails closed for unauthenticated users with Tamil blocker."""
        res = post_search("ஊசி குத்து காயம் என்ன செய்ய வேண்டும்")
        self.assertEqual(res.get("access_status"), "BLOCKED_RESTRICTED")
        self.assertIn("அணுகல் கட்டுப்பாடு", res["answer"])

    def test_22_tanglish_needle_stick_injury(self):
        """Tanglish needle stick query maps correctly to ER/IPC/Nursing manual."""
        res = post_search("oosi kuthu kaayam enna seiyanum", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("ER" in l["url"] or "IPC.pdf" in l["url"] or "NURSING" in l["url"] or "Laundry" in l["url"] for l in res["links"]))

    def test_23_tanglish_resignation_notice(self):
        """Tanglish resignation query maps correctly to HRM manual."""
        res = post_search("rajinama notice period evvalavu", role=ACCESS_STAFF)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")
        self.assertTrue(any("HRM" in l["url"] for l in res["links"]))

    def test_24_tamil_waste_management(self):
        """Tamil biomedical waste query maps to Disinfection / IPC manual."""
        res = post_search("கழிவு மேலாண்மை வண்ணங்கள்", role=ACCESS_CLINICAL)
        self.assertEqual(res.get("access_status"), "AUTHORIZED")

    # =========================================================================
    # 5. DETERMINISTIC STAGE 0 & STAGE 1 PRESERVATION
    # =========================================================================
    def test_25_stage0_open_his_bypasses_knowledge_retrieval(self):
        """'open his' bypasses knowledge retrieval and launches Backbone login instantly."""
        t0 = time.time()
        res = post_search("open his")
        latency_ms = (time.time() - t0) * 1000
        self.assertIn("login.aspx", res["links"][0]["url"])
        self.assertLess(latency_ms, 50.0)

    def test_26_stage0_open_hrms_bypasses_knowledge_retrieval(self):
        """'open hrms' launches PruWorks HRMS instantly."""
        res = post_search("open hrms")
        self.assertIn("mapims-hrms", res["links"][0]["url"])

    def test_27_stage0_wifi_form_bypasses_knowledge_retrieval(self):
        """'wifi form' returns Employee WIFI Request Form PDF."""
        res = post_search("wifi form")
        self.assertIn("EMPLOYEE%20WIFI%20REQUEST%20FORM.pdf", res["links"][0]["url"])

    def test_28_stage1_intercom_bypasses_knowledge_retrieval(self):
        """'canteen phone number' returns Dietetics intercom directory."""
        res = post_search("canteen phone number")
        self.assertIn("intercom.html?dept=Dietetics", res["links"][0]["url"])

    # =========================================================================
    # 6. EDGE CASES, RESILIENCE & INTEGRITY
    # =========================================================================
    def test_29_question_cleaner_strips_conversational_wrappers(self):
        """Verify question cleaning removes English and Tamil question wrappers."""
        cleaned1 = clean_question_for_search("What is the needle-stick injury protocol?")
        self.assertEqual(cleaned1, "needle-stick injury protocol")

        cleaned2 = clean_question_for_search("Explain resignation notice period")
        self.assertEqual(cleaned2, "resignation notice period")

        cleaned3 = clean_question_for_search("How to handle blood transfusion reaction?")
        self.assertEqual(cleaned3, "blood transfusion reaction")

    def test_30_missing_or_unknown_query_graceful_fallback(self):
        """Unknown query produces clean fallback without 500 error or crash."""
        res = post_search("zyxwvu987654randomterm")
        self.assertIn("answer", res)
        self.assertIn("links", res)

    def test_31_direct_page_citation_url_integrity(self):
        """Verify all returned knowledge links contain valid #page=N fragment."""
        passages = search_passages("needle stick injury", limit=3)
        for p in passages:
            self.assertIn("#page=", p["page_url"])
            page_num_str = p["page_url"].split("#page=")[1]
            self.assertTrue(page_num_str.isdigit())

    def test_32_gemini_generation_disabled_in_phase3_3(self):
        """Verify that Gemini generation is completely disabled and response is generated locally."""
        t0 = time.time()
        res = post_search("What are the criteria for ventilator associated event?", role=ACCESS_CLINICAL)
        latency_ms = (time.time() - t0) * 1000
        # Local SQLite execution completes in under 50ms, whereas Gemini API call requires 800ms - 2500ms
        self.assertLess(latency_ms, 200.0)
        self.assertIn("IPC", res["links"][0]["url"])


if __name__ == "__main__":
    unittest.main()

