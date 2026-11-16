#!/usr/bin/env python3
"""
Evaluate the 34 Phase 1 Audit queries against the updated Search Engine.
Reports exact query, returned title, URL, correctness, and speed.
"""

import urllib.request
import json
import time

SERVER_URL = "http://localhost:3000/api/ai-search"

TEST_CASES = [
    # 17 Mandatory Queries
    ("open his", "AOSTA HIS Login", ["192.168.103.37/BB15SE/Backbone/admin/login.aspx"]),
    ("his login enga", "AOSTA HIS Login", ["192.168.103.37/BB15SE/Backbone/admin/login.aspx"]),
    ("ஹெச்ஐஎஸ் திற", "AOSTA HIS Login", ["192.168.103.37/BB15SE/Backbone/admin/login.aspx"]),
    ("open his form", "New HIS User Request Form", ["His User Creation.pdf"]),
    ("enaku his access venum", "New HIS User Request Form", ["His User Creation.pdf"]),
    ("open hrms", "PruWorks HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("leave apply pannanum", "PruWorks HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("wifi form", "Employee WIFI Request Form", ["EMPLOYEE WIFI REQUEST FORM.pdf"]),
    ("internet connection request", "Employee WIFI Request Form", ["EMPLOYEE WIFI REQUEST FORM.pdf"]),
    ("கணினி கோரிக்கை", "System Request Form", ["SYSTEM REQUEST FORM.pdf"]),
    ("infection control manual", "Infection Control Guideline/Manual", ["Guideline for Infection Control Practices ICU.pdf", "manuals.html"]),
    ("NABH policy", "Manuals/Policy Hub or Quality Manual", ["CODE YELLOW POLICY.pdf", "manuals.html", "PSQ.pdf"]),
    ("infection control committee", "HICC Charter / Committees Directory", ["HOSPITAL INFECTION CONTROL COMMITTEE.pdf", "comitee.html"]),
    ("quality committee members", "Committees Directory / QC Record", ["comitee.html", "QC MOM"]),
    ("resignation procedure", "Human Resources Manual (HRM - 2025)", ["HRM 2025.pdf"]),
    ("rajinama form", "Human Resources Manual / Staff Application", ["HRM 2025.pdf", "Non Teaching.pdf"]),
    ("பணி விலகல் படிவம்", "Human Resources Manual (HRM - 2025)", ["HRM 2025.pdf"]),

    # 16 Additional Variations
    ("open pacs", "M - PACS Medsynapse", ["192.168.101.224/User_Login.asp"]),
    ("xray scan paakanum", "M - PACS Medsynapse", ["192.168.101.224/User_Login.asp"]),
    ("open mrd", "MRD Medical Records Portal", ["mapimsmrd.com/mapimsmrd"]),
    ("discharge summary archive", "MRD Medical Records Portal", ["mapimsmrd.com/mapimsmrd"]),
    ("ratha vangi stock", "Blood Bank Stock Details", ["Blood Bank Stock Details.pdf"]),
    ("iratha vangi", "Blood Bank Stock Details", ["Blood Bank Stock Details.pdf"]),
    ("mhc", "MAPIMS AI Health Assessment (MHC)", ["mh.mapims.edu.in"]),
    ("மாஸ்டர் ஹெல்த் செக்கப்", "MAPIMS AI Health Assessment (MHC)", ["mh.mapims.edu.in"]),
    ("lineloom token", "LineLoom OPD Token Display", ["192.168.103.158:8086"]),
    ("opd queue display", "LineLoom OPD Token Display", ["192.168.103.158:8086"]),
    ("doctor id creation in his", "Doctor Name and ID Creation Form", ["Doctor Name and ID Creation.pdf"]),
    ("printer request form", "Printer Request Form", ["PRINTER REQUEST FORM.pdf"]),
    ("acchaagam padivam", "Printer Request Form", ["PRINTER REQUEST FORM.pdf"]),
    ("canteen phone number", "Dietetics Intercom", ["intercom.html?dept=Dietetics"]),
    ("dietician intercom", "Dietetics Intercom", ["intercom.html?dept=Dietetics"]),
    ("emergency casualty number", "Emergency Medicine Intercom", ["emergency medicine", "emergency", "2001"]),

    # Live Incident Query
    ("Procedure Resignation Job Form", "Human Resources Manual (HRM - 2025)", ["HRM 2025.pdf", "Non Teaching.pdf"])
]

def run():
    passed = 0
    total = len(TEST_CASES)
    results = []

    for query, expected_desc, target_urls in TEST_CASES:
        t0 = time.time()
        req = urllib.request.Request(
            SERVER_URL,
            data=json.dumps({"query": query}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            results.append((query, expected_desc, "ERROR", str(e), 0, False))
            continue

        latency_ms = (time.time() - t0) * 1000
        links = data.get("links", [])
        top_url = links[0].get("url", "") if links else ""
        top_title = links[0].get("title", "") if links else ""

        # Check match (unquoting URL so spaces and %20 match)
        unquoted_links = [
            (urllib.parse.unquote(l.get("url", "")).lower(), l.get("title", "").lower())
            for l in links[:3]
        ]
        matched = any(
            any(t.lower() in u or t.lower() in title for t in target_urls)
            for u, title in unquoted_links
        )

        # Check specific anti-patterns
        if "rajinama" in query and "antibiotic" in top_title.lower():
            matched = False
        if "resignation" in query and "ticketing" in top_title.lower():
            matched = False
        if query in ["open his", "his login enga", "ஹெச்ஐஎஸ் திற"] and "his user creation" in top_title.lower():
            matched = False

        if matched:
            passed += 1

        results.append((query, expected_desc, top_title, top_url, latency_ms, matched))

    print(f"\n=======================================================")
    print(f"SEARCH ENGINE ACCURACY EVALUATION: {passed}/{total} PASSED ({passed/total*100:.1f}%)")
    print(f"=======================================================\n")
    for q, exp, title, url, ms, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} [{ms:5.1f}ms] Query: '{q}' -> Top: '{title}' ({url[:60]})")

    return passed, total, results

if __name__ == "__main__":
    run()
