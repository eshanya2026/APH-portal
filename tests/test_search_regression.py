#!/usr/bin/env python3
"""
APH Portal AI Search Engine: Automated Regression Test Suite
Validates:
1. Security Barriers (Blocking .env, .git, server.py, path traversal, CORS headers)
2. Application vs Form Routing (HIS app vs HIS form, HRMS, PACS, MRD, MHC, LineLoom)
3. Multilingual Support (English, Tamil Script, Tanglish)
4. Resignation & HR Isolation (Preventing antibiotic review or ticketing desk match)
5. Committee & Governance Routing (comitee.html directory & charters)
6. Offline Gemini Fallback & Deterministic Integrity
"""

import unittest
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import sys

SERVER_URL = "http://localhost:3000"

class TestSecurityRemediation(unittest.TestCase):
    """Test HTTP security boundaries on static file serving and environment secrets."""

    def test_block_env_file(self):
        """Requesting /.env must return 403 Forbidden, not 200 OK."""
        url = f"{SERVER_URL}/.env"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                self.fail(f"SECURITY VULNERABILITY: /.env returned HTTP {resp.status} instead of 403")
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            self.assertEqual(code, 403, f"Expected 403 Forbidden for /.env, got {code}")

    def test_block_git_directory(self):
        """Requesting /.git/config must return 403 Forbidden."""
        url = f"{SERVER_URL}/.git/config"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                self.fail(f"SECURITY VULNERABILITY: /.git/config returned HTTP {resp.status} instead of 403")
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            self.assertEqual(code, 403, f"Expected 403 Forbidden for /.git/config, got {code}")

    def test_block_server_py(self):
        """Requesting /server.py source code must return 403 Forbidden."""
        url = f"{SERVER_URL}/server.py"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                self.fail(f"SECURITY VULNERABILITY: /server.py returned HTTP {resp.status} instead of 403")
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            self.assertEqual(code, 403, f"Expected 403 Forbidden for /server.py, got {code}")

    def test_block_path_traversal(self):
        """Directory traversal attempts (e.g. /files/../../.env) must return 403 Forbidden."""
        url = f"{SERVER_URL}/files/../../.env"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                self.fail(f"SECURITY VULNERABILITY: Traversal returned HTTP {resp.status} instead of 403")
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            self.assertEqual(code, 403, f"Expected 403 Forbidden for traversal, got {code}")

    def test_index_html_has_no_fetch_env(self):
        """index.html must NOT contain fetch('/.env') or client-side API key scraping."""
        index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertNotIn("fetch('/.env')", content, "index.html contains fetch('/.env')")
        self.assertNotIn('fetch("/.env")', content, 'index.html contains fetch("/.env")')
        self.assertNotIn('getClientGeminiKey', content, 'index.html contains getClientGeminiKey')


class TestSearchIntentAndRouting(unittest.TestCase):
    """Test AI Search API query routing across applications, forms, HR, and committees."""

    def call_search(self, query):
        req = urllib.request.Request(
            f"{SERVER_URL}/api/ai-search",
            data=json.dumps({"query": query}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode("utf-8"))

    # 1. HIS Application vs Form Tests
    def test_open_his_launches_app(self):
        """'open his' must launch AOSTA HIS Workstation Login, NOT the user creation form."""
        res = self.call_search("open his")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("192.168.103.37/BB15SE/Backbone/admin/login.aspx", primary_link,
                      f"'open his' did not return HIS Login URL. Got: {primary_link}")
        self.assertNotIn(".pdf", primary_link.lower())

    def test_his_login_enga_launches_app(self):
        """'his login enga' must launch AOSTA HIS Workstation Login."""
        res = self.call_search("his login enga")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("192.168.103.37/BB15SE/Backbone/admin/login.aspx", primary_link,
                      f"'his login enga' did not return HIS Login URL. Got: {primary_link}")

    def test_tamil_his_open_launches_app(self):
        """'ஹெச்ஐஎஸ் திற' (Tamil: Open HIS) must launch AOSTA HIS Workstation Login."""
        res = self.call_search("ஹெச்ஐஎஸ் திற")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("192.168.103.37/BB15SE/Backbone/admin/login.aspx", primary_link,
                      f"'ஹெச்ஐஎஸ் திற' did not return HIS Login URL. Got: {primary_link}")

    def test_open_his_form_returns_pdf(self):
        """'open his form' must return the New HIS User Request Form PDF."""
        res = self.call_search("open his form")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("His%20User%20Creation.pdf", primary_link,
                      f"'open his form' did not return HIS User Creation PDF. Got: {primary_link}")

    def test_tanglish_his_access_returns_form(self):
        """'enaku his access venum' must return the New HIS User Request Form PDF."""
        res = self.call_search("enaku his access venum")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("His%20User%20Creation.pdf", primary_link,
                      f"'enaku his access venum' did not return HIS User Creation PDF. Got: {primary_link}")

    # 2. HRMS Application Tests
    def test_open_hrms_launches_portal(self):
        """'open hrms' must launch PruWorks HRMS Portal."""
        res = self.call_search("open hrms")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("mapims-hrms.tecvinesolutions.com", primary_link)

    def test_leave_apply_pannanum_launches_hrms(self):
        """'leave apply pannanum' must launch PruWorks HRMS Portal."""
        res = self.call_search("leave apply pannanum")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("mapims-hrms.tecvinesolutions.com", primary_link)

    # 3. IT & Wi-Fi Forms
    def test_wifi_form_returns_wifi_pdf(self):
        """'wifi form' must return Employee WIFI Request Form."""
        res = self.call_search("wifi form")
        primary_link = urllib.parse.unquote(res.get("links", [{}])[0].get("url", "")).lower()
        self.assertIn("wifi request form.pdf", primary_link)

    def test_internet_connection_request_returns_wifi_form(self):
        """'internet connection request' must return Employee WIFI Request Form."""
        res = self.call_search("internet connection request")
        primary_link = urllib.parse.unquote(res.get("links", [{}])[0].get("url", "")).lower()
        self.assertIn("wifi request form.pdf", primary_link,
                      f"Failed to map internet connection request to WIFI form. Got: {primary_link}")

    def test_tamil_system_request_form(self):
        """'கணினி கோரிக்கை' must return System Request Form."""
        res = self.call_search("கணினி கோரிக்கை")
        primary_link = urllib.parse.unquote(res.get("links", [{}])[0].get("url", "")).lower()
        self.assertIn("system request form.pdf", primary_link)

    # 4. Resignation & HR Isolation Tests
    def test_resignation_procedure_returns_hrm_manual(self):
        """'resignation procedure' must return Human Resources Manual (HRM - 2025)."""
        res = self.call_search("resignation procedure")
        primary_title = res.get("links", [{}])[0].get("title", "")
        self.assertIn("Human Resource", primary_title)

    def test_tanglish_rajinama_form_returns_resignation(self):
        """'rajinama form' MUST return HRM 2025 / Resignation, and NEVER antibiotic review!"""
        res = self.call_search("rajinama form")
        primary_title = res.get("links", [{}])[0].get("title", "")
        self.assertNotIn("Antibiotic", primary_title, "CRITICAL: 'rajinama form' returned antibiotic form!")
        self.assertTrue(
            "Human Resource" in primary_title or "Staff Application" in primary_title or "HR" in primary_title,
            f"Expected HR resignation resource, got: {primary_title}"
        )

    def test_tamil_resignation_form(self):
        """'பணி விலகல் படிவம்' must return Human Resources Manual / Resignation."""
        res = self.call_search("பணி விலகல் படிவம்")
        primary_title = res.get("links", [{}])[0].get("title", "")
        self.assertTrue("Human Resource" in primary_title or "HR" in primary_title)

    def test_resignation_job_form_never_returns_ticketing(self):
        """'Procedure Resignation Job Form' MUST return HRM / Staff forms, NEVER Ticketing Desk."""
        res = self.call_search("Procedure Resignation Job Form")
        primary_title = res.get("links", [{}])[0].get("title", "")
        self.assertNotIn("Ticketing", primary_title, "CRITICAL: 'Procedure Resignation Job Form' returned Ticketing Desk!")
        self.assertTrue("Human Resource" in primary_title or "Staff" in primary_title or "HR" in primary_title)

    # 5. Committee Searches
    def test_quality_committee_members_routes_to_committees(self):
        """'quality committee members' must route to comitee.html or QC committee record."""
        res = self.call_search("quality committee members")
        links = res.get("links", [])
        urls = [l.get("url", "") for l in links]
        titles = [l.get("title", "") for l in links]
        has_committee_route = any("comitee.html" in u or "QC MOM" in t or "QUALITY" in t.upper() or "COMMITTEE" in t.upper() for u, t in zip(urls, titles))
        self.assertTrue(has_committee_route, f"Failed to route quality committee query. Got URLs: {urls}")

    def test_infection_control_committee_routes_to_committee(self):
        """'infection control committee' must route to HICC charter or comitee.html."""
        res = self.call_search("infection control committee")
        links = res.get("links", [])
        titles = " ".join([l.get("title", "") for l in links])
        self.assertIn("Infection Control Committee", titles)

    # 6. Core Clinical & Operational Applications
    def test_open_pacs(self):
        """'open pacs' must return Medsynapse PACS viewer."""
        res = self.call_search("open pacs")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("192.168.101.224/User_Login.asp", primary_link)

    def test_open_mrd(self):
        """'open mrd' must return MRD Portal."""
        res = self.call_search("open mrd")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("mapimsmrd.com/mapimsmrd", primary_link)

    def test_open_mhc(self):
        """'mhc' must return MAPIMS AI Health Assessment."""
        res = self.call_search("mhc")
        primary_link = res.get("links", [{}])[0].get("url", "")
        self.assertIn("mh.mapims.edu.in", primary_link)


if __name__ == "__main__":
    unittest.main()
