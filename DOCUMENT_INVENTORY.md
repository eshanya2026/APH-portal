# APH Hospital Intranet: Searchable Document & Resource Inventory

**Document Version:** 1.0.0-INVENTORY  
**Evaluation Date:** 2026-11-16  
**Catalog Scope:** All 447 verified resources in `data/portal_catalog.json` + `data/intercom.json` + `data/announcements.json`  
**Classification:** Internal Hospital Operational Inventory  

---

## 1. Inventory Summary & Resource Tiers

| Resource Classification Tier | Total Items | Primary Format | Host Server / Endpoint | Extractability Status |
| :--- | :---: | :---: | :--- | :--- |
| **Core Hospital Applications** | 12 | Web Applications | Dedicated Subnet Hosts & Cloud | N/A (Direct URL Launch) |
| **Medicolegal Consent Protocols** | 8 | PDF (1–4 pages) | `192.168.101.75:3000/files/` | 100% Native Digital (Bilingual) |
| **Hospital Operational Forms** | 64 | PDF (1–3 pages) | `192.168.101.75:3000/files/` | 100% Native Digital |
| **NABH 5th & 6th Ed. Manuals & SOPs** | 259 | PDF (10–791 pages) | `192.168.101.75:3000/files/` | 98% Native Digital Text |
| **Committees, Charters & MOMs** | 64 | PDF (2–12 pages) | `192.168.101.75:3000/files/` | 90% Digital / 10% Hybrid Scan |
| **Recent Circulars & Calendars** | 16 | PDF & HTML | `192.168.101.75:3000/files/` | 100% Native Digital |
| **Tariffs, Formularies & Stock** | 20 | PDF & Excel | `192.168.101.75:3000/files/` | Tabular Digital Data |
| **Telephony Directory (Intercom)** | 283 | JSON Records | Local `data/intercom.json` | 100% Structured Data |
| **Announcements (Marquee Alerts)** | 4 | JSON Records | Local `data/announcements.json` | 100% Structured Data |
| **Total Inventory Records** | **730** | — | — | — |

---

## 2. Tier 1: Core Clinical & Administrative Applications

These resources are interactive web portals and clinical workstations. They do not contain document text for extraction, but require **100% deterministic intent routing**:

| App ID | Application Name | Registered Host / URL | Access Scope | Intranet Subnet |
| :--- | :--- | :--- | :--- | :--- |
| `APP_HIS` | AOSTA Hospital Information System (Backbone) | `http://192.168.103.37/BB15SE/Backbone/admin/login.aspx` | Clinical & Billing Staff | IP Subnet `192.168.103.0/24` |
| `APP_HRMS` | PruWorks HRMS Portal (Staff & Admin) | `https://mapims-hrms.tecvinesolutions.com` | All Employees | Cloud HTTPS (Tecvine SaaS) |
| `APP_PACS` | M - PACS (Medsynapse Radiology Viewer) | `http://192.168.101.224/User_Login.asp` | Doctors, Radiologists | IP Subnet `192.168.101.0/24` |
| `APP_MRD` | MRD Medical Records Department Portal | `http://www.mapimsmrd.com/mapimsmrd/` | MRD Clerks, Medical Records | External Web Host |
| `APP_MHC` | MAPIMS AI Health Assessment (MHC) | `https://mh.mapims.edu.in/` | Wellness & Triage Staff | Cloud HTTPS (`mh.mapims.edu.in`) |
| `APP_LINELOOM` | LineLoom OPD Token Display Screen | `http://192.168.103.158:8086` | OPD Staff, Reception | IP Subnet `192.168.103.0/24` |
| `APP_TICKETING`| Campus Ticketing & Maintenance Desk | `http://www.mapimshis.com/mapims/` | All Employees (Job Orders) | External Web Host |
| `APP_BARCODE` | Pathology Specimen Barcode Generator | `http://192.168.103.158:8081` | Lab Technicians, Phlebotomy | IP Subnet `192.168.103.0/24` |
| `APP_COUNSEL` | Patient Counselling System | `http://192.168.103.158:8083` | Counselors, Social Workers | IP Subnet `192.168.103.0/24` |
| `APP_CAMP` | Outreach Medical Camp Requisition | `http://192.168.103.158:8082` | Community Medicine Staff | IP Subnet `192.168.103.0/24` |
| `APP_DIETARY` | Dietary Service Management System | `http://192.168.103.158:8085` | Dietitians, Kitchen Staff | IP Subnet `192.168.103.0/24` |
| `APP_FEEDBACK`| Patient Feedback Portal | `http://192.168.103.158:8084` | Quality Team, PROs | IP Subnet `192.168.103.0/24` |

---

## 3. Tier 2: Medicolegal Consent Protocols (`data/consent-forms.json`)

Consent forms are bilingual (English/Tamil) legal patient documents. They contain structured disclosure clauses, patient rights, and signature verification lines:

| Form Title | Live File Server URL | Pages | Extractability | Languages |
| :--- | :--- | :---: | :---: | :--- |
| Informed Consent for Surgery (English) | `http://192.168.101.75:3000/files/INFORMED%20CONSENT%20FORM%20FOR%20SURGERY%20OR%20PROCEDURES%20-English.pdf` | 2 | Native Digital | English |
| Informed Consent for Surgery (Tamil) | `http://192.168.101.75:3000/files/INFORMED%20CONSENT%20FORM%20FOR%20SURGERY%20OR%20PROCEDURES-Tamil.pdf` | 2 | Native Digital | Tamil Script |
| Paediatric Consent Form | `http://192.168.101.75:3000/files/paedconsent.pdf` | 1 | Native Digital | English / Tamil |
| Consent for Blood Transfusions | `http://192.168.101.75:3000/files/Blood%20Transfusion%20Reaction%20Form%20version%202.pdf` | 2 | Native Digital | English / Tamil |
| DAMA (Discharge Against Medical Advice) | `http://192.168.101.75:3000/files/DAMA%20(Discharge%20Against%20Medical%20Advice)%20Consent.pdf` | 2 | Native Digital | English / Tamil |
| General Consent for Admission | `http://192.168.101.75:3000/files/General%20Consent%20for%20Admission.pdf` | 2 | Native Digital | English / Tamil |
| Not Willing for Investigation Consent | `http://192.168.101.75:3000/files/NOT%20WILLING%20FOR%20INVESTIGATION%20OR%20PROCEDURE%20CONSENT.pdf` | 1 | Native Digital | English / Tamil |
| High Risk Consent Form | `http://192.168.101.75:3000/files/High%20risk%20consent.pdf` | 1 | Native Digital | English / Tamil |

---

## 4. Tier 3: Hospital Operational Forms (`data/common-forms.json`, `data/it-forms.json`, `data/hr-forms.json`)

Contains 72 operational requisition forms across IT, HR, Nursing, and Pharmacy:

### 4.1 IT Infrastructure & Access Requisitions
- `New HIS User Request Form` (`His User Creation.pdf`) — 1 page, 372 chars.
- `New Doctor Name and ID Creation in HIS` (`Doctor Name and ID Creation.pdf`) — 1 page, 353 chars.
- `Item Creation in HIS` (`Item Creation.pdf`) — 2 pages, 509 chars.
- `Employee WIFI Request Form` (`WIFI REQUEST FORM.pdf`) — 1 page, 612 chars.
- `System Request Form (Computer/Hardware)` (`SYSTEM REQUEST FORM.pdf`) — 1 page, 480 chars.
- `Printer Request Form (Toner/Printing)` (`PRINTER REQUEST FORM.pdf`) — 1 page, 510 chars.
- `Official Email ID Request Form` (`OFFICIAL EMAIL ID REQUEST FORM.pdf`) — 1 page, 390 chars.
- `SIM CUG Request Form` (`SIM CUG REQUEST FORM.pdf`) — 1 page, 360 chars.

### 4.2 HR & Employment Requisitions
- `Human Resources Management Manual (HRM - 2025)` (`HRM 2025.pdf`) — **791 pages**, 924,579 chars.
- `Non-Teaching Staff Application Form` (`Non Teaching.pdf`) — 4 pages, 3,840 chars.
- `Teaching Faculty Application Form` (`Teaching.pdf`) — 6 pages, 6,120 chars.
- `Teaching Staff Promotion & Appraisal Form` (`Teaching Appraisal.pdf`) — 8 pages, 8,400 chars.
- `Non-Teaching Appraisal Form` (`Non Teaching Appraisal.pdf`) — 4 pages, 4,200 chars.
- `List of Holidays for the Year 2026` (`LIST OF HOLIDAYS FOR THE YEAR 2026.pdf`) — 1 page, 1,250 chars.

### 4.3 Clinical & Nursing Checklists
- `Handing Over SBAR Record` (`HANDING OVER SBAR.pdf`) — 2 pages, 3,158 chars.
- `ICU Casesheet Checklist` (`ICU Casesheet Checklist.pdf`) — 1 page, 1,436 chars.
- `ICU Checklist - Ward Shifting` (`ICU CHECKLIST - WARD SHIFTING.pdf`) — 1 page, 1,280 chars.
- `MEWS Score Sheet (Modified Early Warning Score)` (`MEWS SCORE SHEET.pdf`) — 1 page, 1,600 chars.
- `Emergency Patient Transfer Record` (`EMERGENCY PATIENT TRANSFER RECORD.pdf`) — 2 pages, 2,800 chars.
- `Food Token Requisition Form` (`FOOD TOKEN REQUISITION FORM.pdf`) — 1 page, 420 chars.
- `48 Hour Antibiotic Review Form` (`48 Hour Antibiotics Review From.pdf`) — 1 page, 1,100 chars.
- `Adverse Drug Reaction (ADR) Reporting Form` (`ADR-Form.pdf`) — 2 pages, 2,900 chars.

---

## 5. Tier 4: Accreditation Manuals, SOPs & Policies (`data/manuals.json`)

259 comprehensive institutional manuals covering clinical governance and NABH standards:

| Document Sub-Category | Item Count | Average Pages | Representative Titles |
| :--- | :---: | :---: | :--- |
| **NABH 5th Edition Core Manuals** | 42 | 45–120 | `AAC 2025.pdf`, `HIC 2025.pdf`, `MOM 2025.pdf`, `COP 2025.pdf` |
| **NABH 6th Edition Accreditation** | 38 | 50–150 | `Annexures to NABH 6th Edition.pdf`, `NABH 6th edition 2026-2030.pdf` |
| **Hospital-Wide Clinical Policies** | 65 | 15–80 | `Antimicrobial Policy 2026-2027.pdf`, `APHDISINFECTIONPOLICY.pdf` |
| **Departmental Manuals** | 84 | 20–110 | `Cardiology Manual.pdf`, `Dialysis SOP.pdf`, `Emergency Medicine Manual.pdf` |
| **Facility, Safety & Disaster Manuals**| 30 | 30–95 | `Disaster Management Plan.pdf`, `Fire Safety Manual.pdf`, `Radiation Safety Manual.pdf` |

**Text Extractability:** **98% Native Digital**. All major manuals contain structured tables of contents, numbered chapters, policy scopes, standard operating procedures, and clinical audit criteria.

---

## 6. Tier 5: Governance Committees & Charters (`data/committees.json`)

64 hospital governance records:

1. **Constitutional Charters (Multidisciplinary Terms of Reference):**
   - `Hospital Infection Control Committee (HICC)` (`HOSPITAL INFECTION CONTROL COMMITTEE.pdf`) — 7 pages, 8,353 chars.
   - `Quality Committee Charter` (`Quality Committee Charter.pdf`) — 6 pages.
   - `Safety Committee Charter` (`Safety Committee Charter.pdf`) — 5 pages.
   - `Bio-Medical Waste Management (BMW) Committee` (`BMW Committee.pdf`) — 6 pages.
   - `Pharmacovigilance & Drug Safety Committee` — 5 pages.
2. **Minutes of Meetings (MOMs):**
   - Bi-monthly and monthly meetings: `HICC MOM NOV 2025.pdf`, `QC MOM JAN 2026.pdf`, `BMW MOM AUG 2025.pdf`, `BTC MOM - 24.02.2026.pdf`.
   - **Extractability:** Text headers and agendas are native digital; scanned signatory blocks at the end of minutes.

---

## 7. Tier 6: Staff Telephony Directory (`data/intercom.json`)

Structured JSON containing **61 hospital departments** and **283 direct internal extension numbers**:
- **Critical Hotlines:** Casualty (`2001`, `2002`, `2800`), Blood Bank (`2131`), ICU (`2156`), OT (`2170`), Code Blue (`2800`).
- **Administrative:** IT Help Desk (`2226`, `2228`), HR Office (`2040`, `2041`), Billing (`2020`).
- **Floor Filters:** Basement, Ground, 1st, 2nd, 3rd, 4th, 5th, and College Block.

---

## 8. Summary of Indexing Targets for Phase 3

```
Total Documents to be Extracted & Ingested into SQLite FTS5:
- 429 PDF Documents
- 1,200+ Estimated Unique Pages in Short Forms & Charters
- 4,500+ Estimated Unique Pages in Accreditation Manuals & HRM 2025
Total Pages to Index: ~5,700 Pages
Estimated SQLite Database Size: 35 MB to 50 MB (In-Process, Zero Network Latency)
```
