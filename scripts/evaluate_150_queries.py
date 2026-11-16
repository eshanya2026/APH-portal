#!/usr/bin/env python3
"""
Generate and evaluate 150 realistic hospital staff queries across English, Tamil, and Tanglish.
Includes typos, misspellings, colloquial expressions, and ambiguous requests.
"""

import urllib.request
import json
import time
import sys

SERVER_URL = "http://localhost:3000/api/ai-search"

# 150 Realistic Queries across 7 categories
QUERIES = [
    # Category 1: HIS & Core Hospital Workstations (25 queries)
    ("open his", "HIS Workstation", ["login.aspx", "admin/login"]),
    ("his login", "HIS Workstation", ["login.aspx"]),
    ("his login enga", "HIS Workstation", ["login.aspx"]),
    ("opn his", "HIS Workstation", ["login.aspx"]),
    ("hiss login", "HIS Workstation", ["login.aspx"]),
    ("his workstation open", "HIS Workstation", ["login.aspx"]),
    ("aosta his portal", "HIS Workstation", ["login.aspx"]),
    ("backbone login", "HIS Workstation", ["login.aspx"]),
    ("ஹெச்ஐஎஸ் திற", "HIS Workstation", ["login.aspx"]),
    ("ஹிஸ் லாகின்", "HIS Workstation", ["login.aspx"]),
    ("ஹெச் ஐ எஸ் போர்டல்", "HIS Workstation", ["login.aspx"]),
    ("his open panna mudiyuma", "HIS Workstation", ["login.aspx"]),
    ("his enga iruku", "HIS Workstation", ["login.aspx"]),
    ("where is his software", "HIS Workstation", ["login.aspx"]),
    ("open pacs", "PACS Viewer", ["192.168.101.224/User_Login.asp"]),
    ("pacs viewer", "PACS Viewer", ["User_Login.asp"]),
    ("xray scan paakanum", "PACS Viewer", ["User_Login.asp"]),
    ("medsynapse login", "PACS Viewer", ["User_Login.asp"]),
    ("ct scan viewer", "PACS Viewer", ["User_Login.asp"]),
    ("open mrd", "MRD Portal", ["mapimsmrd.com/mapimsmrd"]),
    ("mrd records", "MRD Portal", ["mapimsmrd.com/mapimsmrd"]),
    ("discharge summary archive", "MRD Portal", ["mapimsmrd.com/mapimsmrd"]),
    ("open hrms", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("hrms staff login", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("pruworks portal", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),

    # Category 2: HRMS, Leave, Attendance & Payslips (20 queries)
    ("leave apply pannanum", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("how to apply leave", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("leavu apply", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("vidumurai vinnappam", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("விடுமுறை விண்ணப்பம்", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("leave balance enga paakanum", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("payslip download", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("monthly salary slip", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("sambalam slip", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("சம்பள ரசீது", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("biometric punch regularisation", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("attendance portal", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("varugai pathivu", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("வருகை பதிவு", "HRMS Portal", ["mapims-hrms.tecvinesolutions.com"]),
    ("mhc", "MHC Application", ["mh.mapims.edu.in"]),
    ("master health checkup portal", "MHC Application", ["mh.mapims.edu.in"]),
    ("மாஸ்டர் ஹெல்த் செக்கப்", "MHC Application", ["mh.mapims.edu.in"]),
    ("lineloom token", "LineLoom Display", ["192.168.103.158:8086"]),
    ("opd queue display", "LineLoom Display", ["192.168.103.158:8086"]),
    ("opd token machine", "LineLoom Display", ["192.168.103.158:8086"]),

    # Category 3: IT Hardware, Network & Wi-Fi Forms (20 queries)
    ("wifi form", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("wifi foam", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("wi-fi application", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("internet connection request", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("wifi access venum", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("laptop wifi permission", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("வைஃபை படிவம்", "WIFI Form", ["WIFI REQUEST FORM.pdf"]),
    ("system request form", "System Request", ["SYSTEM REQUEST FORM.pdf"]),
    ("new computer request", "System Request", ["SYSTEM REQUEST FORM.pdf"]),
    ("kanini request", "System Request", ["SYSTEM REQUEST FORM.pdf"]),
    ("கணினி கோரிக்கை", "System Request", ["SYSTEM REQUEST FORM.pdf"]),
    ("desktop system form", "System Request", ["SYSTEM REQUEST FORM.pdf"]),
    ("printer request form", "Printer Request", ["PRINTER REQUEST FORM.pdf"]),
    ("toner replacement form", "Printer Request", ["PRINTER REQUEST FORM.pdf"]),
    ("acchaagam padivam", "Printer Request", ["PRINTER REQUEST FORM.pdf"]),
    ("பிரிண்டர் படிவம்", "Printer Request", ["PRINTER REQUEST FORM.pdf"]),
    ("official email id request form", "Email Form", ["OFFICIAL EMAIL ID REQUEST FORM.pdf"]),
    ("email form", "Email Form", ["OFFICIAL EMAIL ID REQUEST FORM.pdf"]),
    ("sim cug request form", "CUG SIM Form", ["SIM CUG REQUEST FORM.pdf"]),
    ("cug sim padivam", "CUG SIM Form", ["SIM CUG REQUEST FORM.pdf"]),

    # Category 4: HIS Forms & Requisitions (15 queries)
    ("open his form", "HIS User Creation", ["His User Creation.pdf"]),
    ("his user form", "HIS User Creation", ["His User Creation.pdf"]),
    ("new his user creation", "HIS User Creation", ["His User Creation.pdf"]),
    ("enaku his access venum", "HIS User Creation", ["His User Creation.pdf"]),
    ("his account create pannanum", "HIS User Creation", ["His User Creation.pdf"]),
    ("his username form", "HIS User Creation", ["His User Creation.pdf"]),
    ("ஹெச்ஐஎஸ் பயனர் படிவம்", "HIS User Creation", ["His User Creation.pdf"]),
    ("his id venum", "HIS User Creation", ["His User Creation.pdf"]),
    ("doctor id creation in his", "Doctor ID Form", ["Doctor Name and ID Creation.pdf"]),
    ("new doctor id form", "Doctor ID Form", ["Doctor Name and ID Creation.pdf"]),
    ("maruthuvar id creation", "Doctor ID Form", ["Doctor Name and ID Creation.pdf"]),
    ("மருத்துவர் ஐடி உருவாக்கம்", "Doctor ID Form", ["Doctor Name and ID Creation.pdf"]),
    ("item creation in his form", "Item Creation", ["Item Creation Form.pdf", "Item Creation.pdf"]),
    ("pharmacy item addition in his", "Item Creation", ["Item Creation Form.pdf", "Item Creation.pdf"]),
    ("marunthu porul his addition", "Item Creation", ["Item Creation Form.pdf", "Item Creation.pdf"]),

    # Category 5: HR Resignation, Staff Applications & Protocols (20 queries)
    ("resignation procedure", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("resignation letter procedure", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("resignation process", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("notice period rules", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("exit clearance rules", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("no dues form procedure", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("relieving order rules", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("rajinama form", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("raajinaama procedure", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("rajinama pannanum", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("பணி விலகல் படிவம்", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("பணி விலகல் நடைமுறை", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("ராஜினாமா விதிமுறைகள்", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("Procedure Resignation Job Form", "HRM 2025 Manual", ["HRM 2025.pdf"]),
    ("non teaching staff application", "Non-Teaching Form", ["Non Teaching.pdf"]),
    ("job application form for staff", "Non-Teaching Form", ["Non Teaching.pdf"]),
    ("staff recruitment form", "Non-Teaching Form", ["Non Teaching.pdf"]),
    ("teaching faculty application", "Teaching Form", ["Teaching.pdf"]),
    ("faculty appraisal form", "Teaching Form", ["Teaching.pdf"]),
    ("list of holidays 2026", "Holidays Calendar", ["LIST OF HOLIDAYS FOR THE YEAR 2026.pdf"]),

    # Category 6: Clinical Checklists & Medicolegal Consent Forms (25 queries)
    ("informed consent form for surgery english", "Surgical Consent EN", ["INFORMED CONSENT FORM FOR SURGERY OR PROCEDURES -English.pdf", "consent.html"]),
    ("surgery consent tamil", "Surgical Consent TA", ["INFORMED CONSENT FORM FOR SURGERY OR PROCEDURES-Tamil.pdf", "consent.html"]),
    ("aruvai sikitsai oputhal padivam", "Surgical Consent TA", ["INFORMED CONSENT FORM FOR SURGERY OR PROCEDURES-Tamil.pdf", "consent.html"]),
    ("அறுவை சிகிச்சை ஒப்புதல் படிவம்", "Surgical Consent TA", ["INFORMED CONSENT FORM FOR SURGERY OR PROCEDURES-Tamil.pdf", "consent.html"]),
    ("paediatric consent form", "Pediatric Consent", ["paedconsent.pdf", "consent.html"]),
    ("pediatric consent", "Pediatric Consent", ["paedconsent.pdf", "consent.html"]),
    ("kuzhanthai consent form", "Pediatric Consent", ["paedconsent.pdf", "consent.html"]),
    ("குழந்தை ஒப்புதல் படிவம்", "Pediatric Consent", ["paedconsent.pdf", "consent.html"]),
    ("consent for blood component transfusions", "Blood Consent", ["Blood Transfusion Reaction Form version 2.pdf", "consent.html"]),
    ("blood transfusion consent", "Blood Consent", ["Blood Transfusion Reaction Form version 2.pdf", "consent.html"]),
    ("ratha vangi consent", "Blood Consent", ["Blood Transfusion Reaction Form version 2.pdf", "consent.html"]),
    ("ரத்த தான ஒப்புதல்", "Blood Consent", ["Blood Transfusion Reaction Form version 2.pdf", "consent.html"]),
    ("dama consent form", "DAMA Consent", ["DAMA (Discharge Against Medical Advice) Consent.pdf", "consent.html"]),
    ("discharge against medical advice", "DAMA Consent", ["DAMA (Discharge Against Medical Advice) Consent.pdf", "consent.html"]),
    ("general consent for admission", "General Consent", ["General Consent for Admission.pdf", "consent.html"]),
    ("admission consent", "General Consent", ["General Consent for Admission.pdf", "consent.html"]),
    ("not willing consent form", "Not Willing Consent", ["NOT WILLING FOR INVESTIGATION OR PROCEDURE CONSENT.pdf", "consent.html"]),
    ("icu casesheet checklist", "ICU Checklist", ["ICU Casesheet Checklist.pdf"]),
    ("icu checklist ward shifting", "Ward Shift Checklist", ["ICU CHECKLIST - WARD SHIFTING.pdf"]),
    ("ward shifting form", "Ward Shift Checklist", ["ICU CHECKLIST - WARD SHIFTING.pdf"]),
    ("handing over sbar record", "SBAR Record", ["HANDING OVER SBAR.pdf"]),
    ("sbar sheet", "SBAR Record", ["HANDING OVER SBAR.pdf"]),
    ("mews score sheet", "MEWS Score", ["MEWS SCORE SHEET.pdf"]),
    ("emergency patient transfer record", "Emergency Transfer", ["EMERGENCY PATIENT TRANSFER RECORD.pdf"]),
    ("food token requisition form", "Food Token", ["FOOD TOKEN REQUISITION FORM.pdf"]),

    # Category 7: Committees, Manuals, Telephony & Fallback (25 queries)
    ("quality committee members", "Committees Directory", ["comitee.html", "QC MOM"]),
    ("quality committee charter", "Committees Directory", ["comitee.html", "QC MOM"]),
    ("qc mom", "Committees Directory", ["QC MOM", "comitee.html"]),
    ("infection control committee", "HICC Charter", ["comitee.html", "HOSPITAL INFECTION CONTROL COMMITTEE.pdf"]),
    ("hicc members list", "Committees Directory", ["comitee.html", "HOSPITAL INFECTION CONTROL COMMITTEE.pdf", "HICC MOM"]),
    ("committee scheduled calendar 2026", "Committee Calendar", ["Committee’s Scheduled Calendar-2026.pdf", "comitee.html"]),
    ("hospital committees list", "Committees Directory", ["comitee.html"]),
    ("safety committee mom", "Committees Directory", ["SAFETY MOM", "comitee.html"]),
    ("bmw mom", "Committees Directory", ["BMW MOM", "comitee.html"]),
    ("guideline for infection control practices icu", "ICU Infection Control", ["Guideline for Infection Control Practices ICU.pdf"]),
    ("blood bank stock details", "Blood Bank Stock", ["Blood Bank Stock Details.pdf"]),
    ("ratha vangi stock", "Blood Bank Stock", ["Blood Bank Stock Details.pdf"]),
    ("drug stores stock details", "Drug Stores Stock", ["Drug Stores Stock Details.pdf"]),
    ("purchase process", "Purchase Process", ["Instruments and Equipment APR 2025.pdf"]),
    ("canteen phone number", "Dietetics Intercom", ["intercom.html?dept=Dietetics"]),
    ("dietician intercom", "Dietetics Intercom", ["intercom.html?dept=Dietetics"]),
    ("emergency casualty number", "Emergency Medicine Intercom", ["intercom.html?dept=Emergency Medicine", "intercom.html?dept=Emergency%20Medicine", "2001"]),
    ("blood bank intercom", "Blood Bank Intercom", ["intercom.html?dept=Blood Bank", "intercom.html?dept=Blood%20Bank", "2131"]),
    ("icu intercom extension", "ICU Intercom", ["intercom.html?dept=ICU", "2156"]),
    ("it helpdesk number", "IT Intercom", ["intercom.html", "2226", "2228"]),
    ("campus intercom directory", "Intercom Directory", ["intercom.html"]),
    ("recent circulars", "Circulars Directory", ["recent circular.html", "circulars.json"]),
    ("unknown hospital query xyz 123", "Fallback", ["index.html", "vault", "portal", "manual", "consent"]),
    ("some completely random text that does not exist", "Fallback", ["index.html", "vault", "portal", "clinical", "consent"]),
    ("where is the forms section", "Forms Hub", ["index.html#forms", "commonforms.html", "itforms.html"])
]

def run():
    passed = 0
    total = len(QUERIES)
    results = []

    print(f"Executing 150-query hospital readiness evaluation against {SERVER_URL}...\n")

    for i, (q, exp, targets) in enumerate(QUERIES, start=1):
        t0 = time.time()
        req = urllib.request.Request(
            SERVER_URL,
            data=json.dumps({"query": q}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            results.append((i, q, exp, "ERROR", str(e), 0, False))
            print(f"[{i:3d}/150] ❌ ERROR Query: '{q}' -> {e}")
            continue

        ms = (time.time() - t0) * 1000
        links = data.get("links", [])
        top_url = urllib.parse.unquote(links[0].get("url", "")).lower() if links else ""
        top_title = links[0].get("title", "") if links else ""

        all_returned_text = " ".join([
            urllib.parse.unquote(l.get("url", "")).lower() + " " + l.get("title", "").lower()
            for l in links[:3]
        ])

        matched = any(urllib.parse.unquote(t).lower() in all_returned_text for t in targets)

        # Anti-pattern checks
        if "rajinama" in q.lower() and "antibiotic" in top_title.lower():
            matched = False
        if "resignation" in q.lower() and "ticketing" in top_title.lower():
            matched = False
        if q.lower() in ["open his", "his login enga", "ஹெச்ஐஎஸ் திற"] and "his user creation" in top_title.lower():
            matched = False

        if matched:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        results.append((i, q, exp, top_title, top_url, ms, matched))
        if i % 25 == 0 or not matched:
            print(f"[{i:3d}/150] {status} [{ms:5.1f}ms] '{q}' -> '{top_title}'")

    acc = (passed / total) * 100
    print(f"\n=======================================================")
    print(f"150-QUERY READINESS EVALUATION: {passed}/{total} PASSED ({acc:.1f}%)")
    print(f"=======================================================")

    return passed, total, results

if __name__ == "__main__":
    run()
