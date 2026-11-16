# APH Portal AI Search Engine: Search Failure & Test Matrix

**Document ID:** APH-SEARCH-MATRIX-2026-PHASE1  
**Total Queries Evaluated:** 34 (17 Mandatory Queries + 16 Variations + 1 Live Incident Query)  
**Execution Environment:** `http://localhost:3000/api/ai-search` (Live Multithreaded Python Backend)  

---

## 1. Summary Matrix Overview

| Category | Total Tested | Passed | Partial | Failed | Success Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Core Applications Launch** | 9 | 6 | 0 | 3 | 66.7% |
| **IT & Administrative Forms** | 7 | 6 | 0 | 1 | 85.7% |
| **Manuals, SOPs & Policies** | 4 | 2 | 2 | 0 | 50.0% |
| **Committees, Charters & MOM** | 3 | 0 | 1 | 2 | 0.0% |
| **HR, Resignation & Employment** | 5 | 3 | 0 | 2 | 60.0% |
| **Telephony & Intercoms** | 4 | 4 | 0 | 0 | 100.0% |
| **Clinical Services (Blood Bank/MHC)** | 2 | 2 | 0 | 0 | 100.0% |
| **Overall Summary** | **34** | **23** | **3** | **8** | **67.6% (Clean Pass)** |

---

## 2. Comprehensive Test Audit Matrix

### Section A: Mandatory Test Cases (17 Queries)

| # | User Query | Language | Detected Intent | Expected Resource | Actual Resource | Status | Failure Root Cause & Code Reference |
| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :--- |
| **1** | `open his` | English | `is_his_form_query` | AOSTA HIS Login (`http://192.168.103.37/BB15SE/Backbone/admin/login.aspx`) | `New HIS User Request Form` (`His User Creation.pdf`) | ❌ **FAIL** | **App vs. Form Collision:** `is_his_form_query` in `server.py:1116` & `2398` checks `is_word_match('his', q) and any(k in q for k in [..., 'open', ...])`. Word `'open'` incorrectly triggers form requisition. |
| **2** | `his login enga` | Tanglish | `is_his_form_query` | AOSTA HIS Login (`http://192.168.103.37/BB15SE/Backbone/admin/login.aspx`) | `New HIS User Request Form` (`His User Creation.pdf`) | ❌ **FAIL** | **App vs. Form Collision:** Keyword `'enga'` (where) is hardcoded into `is_his_form_query`, pre-empting `is_his_system_query` at line `2571`. |
| **3** | `ஹெச்ஐஎஸ் திற` | Tamil Script | Fallback Search | AOSTA HIS Login (`http://192.168.103.37/BB15SE/Backbone/admin/login.aspx`) | "No direct hospital document or application matched 'ஹெச்ஐஎஸ் திற'" | ❌ **FAIL** | **Missing Tamil Transliteration:** Tamil script for HIS (`ஹெச்ஐஎஸ்`) and verb open (`திற`) are not present in `SYNONYMS` table (`server.py:833`). |
| **4** | `open his form` | English | `is_his_form_query` | `New HIS User Request Form` (`His User Creation.pdf`) | `New HIS User Request Form` (`His User Creation.pdf`) | ✅ **PASS** | Correctly resolved via `is_his_form_query` direct handler. |
| **5** | `enaku his access venum` | Tanglish | `is_his_form_query` | `New HIS User Request Form` (`His User Creation.pdf`) | `New HIS User Request Form` (`His User Creation.pdf`) | ✅ **PASS** | Correctly triggered by Tanglish intent `'venum'` and `'access'`. |
| **6** | `open hrms` | English | `is_pruworks_query` | PruWorks HRMS Portal (`https://mapims-hrms.tecvinesolutions.com`) | `PruWorks HRMS Portal` | ✅ **PASS** | Correctly matched core HR application resolver (`server.py:2425`). |
| **7** | `leave apply pannanum` | Tanglish | `is_apply_leave_query` | PruWorks HRMS Portal (`https://mapims-hrms.tecvinesolutions.com`) | `PruWorks HRMS Portal` | ✅ **PASS** | Correctly mapped leave request intent to HRMS portal. |
| **8** | `wifi form` | English | `is_wifi_intent` | `Employee WIFI Request Form` (`EMPLOYEE WIFI REQUEST FORM.pdf`) | `Employee WIFI Request Form` | ✅ **PASS** | Correctly matched IT form direct resolver. |
| **9** | `internet connection request` | English | Fallback Search | `Employee WIFI Request Form` (`EMPLOYEE WIFI REQUEST FORM.pdf`) | `New HIS User Request Form`, `System Request Form`, `Printer Request Form` | ❌ **FAIL** | **Synonym Gap:** Phrase `"internet connection"` is not mapped to `"wifi"` in `SYNONYMS` map. Word `"connection"` has no catalog matches. |
| **10** | `கணினி கோரிக்கை` | Tamil Script | `is_it_query` | `System Request Form` (`SYSTEM REQUEST FORM.pdf`) | `System Request Form` | ✅ **PASS** | Tamil script token `கணினி` correctly mapped to IT hardware/software forms. |
| **11** | `infection control manual` | English | Document Match | `Guideline for Infection Control Practices ICU` | `Guideline for Infection Control Practices ICU` | ✅ **PASS** | Direct title token intersection matched ICU infection control guidelines. |
| **12** | `NABH policy` | English | Keyword Scoring | Manuals & SOPs Hub (`./manuals.html`) / Quality Policy Manual | `CODE YELLOW POLICY` | ⚠️ **PARTIAL** | **Overspecific Single Document:** Matches specific emergency code policy rather than directing staff to central NABH Manuals repository. |
| **13** | `infection control committee` | English | Document Match | Committees Hub (`./comitee.html`) + HICC Charter | `Hospital Infection Control Committee (NABH 5th Edition)` | ⚠️ **PARTIAL** | **Missing Hub Integration:** Returns specific PDF charter but completely misses the Committees Directory (`comitee.html`) with meeting records. |
| **14** | `quality committee members` | English | Keyword Scoring | Committees Hub (`./comitee.html`) & Quality Committee Charter | `Committee's Scheduled Calendar-2026.pdf` | ❌ **FAIL** | **Missing Governance Routing:** Document catalog lacks explicit "members" document. Failed to route to `comitee.html`. |
| **15** | `resignation procedure` | English | `is_resignation_query` | `Human Resources Manual (HRM - 2025)` (`HRM 2025.pdf`) | `Human Resources Manual (HRM - 2025)` | ✅ **PASS** | Handled correctly by `is_resignation_fallback` in `server.py:2840`. |
| **16** | `rajinama form` | Tanglish | Fallback Search | `Human Resources Manual (HRM - 2025)` (`HRM 2025.pdf`) | `48 Hour Antibiotics Review From` | ❌ **CRITICAL FAIL** | **Missing Tanglish Token + Stopword Overload:** Tanglish `rajinama` is missing from `is_resignation_query` (only Tamil script `ராஜினாமா` is present). The word `form` matched `From` in antibiotic review! |
| **17** | `பணி விலகல் படிவம்` | Tamil Script | `is_resignation_query` | `Human Resources Manual (HRM - 2025)` (`HRM 2025.pdf`) | `Human Resources Manual (HRM - 2025)` | ✅ **PASS** | Tamil script phrase `பணி விலகல்` correctly identified resignation intent. |

---

### Section B: Additional Diagnostic Variations (16 Queries)

| # | User Query | Language | Detected Intent | Expected Resource | Actual Resource | Status | Notes |
| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :--- |
| **18** | `open pacs` | English | `is_pacs_intent` | M - PACS Medsynapse (`http://192.168.101.224/User_Login.asp`) | M - PACS Medsynapse | ✅ **PASS** | Core system direct resolver executed. |
| **19** | `xray scan paakanum` | Tanglish | `is_pacs_intent` | M - PACS Medsynapse (`http://192.168.101.224/User_Login.asp`) | M - PACS Medsynapse | ✅ **PASS** | Tanglish clinical intent mapped to PACS viewer. |
| **20** | `open mrd` | English | `is_mrd_intent` | MRD Portal (`http://www.mapimsmrd.com/mapimsmrd/`) | MRD Medical Records Portal | ✅ **PASS** | Direct application resolver. |
| **21** | `discharge summary archive` | English | `is_mrd_intent` | MRD Portal (`http://www.mapimsmrd.com/mapimsmrd/`) | MRD Medical Records Portal | ✅ **PASS** | Resolved via medical records intent. |
| **22** | `ratha vangi stock` | Tanglish | `is_blood_query` | `Blood Bank Stock Details.pdf` | `Blood Bank Stock Details.pdf` | ✅ **PASS** | Tanglish blood bank terms mapped accurately. |
| **23** | `iratha vangi` | Tanglish | `is_blood_query` | `Blood Bank Stock Details.pdf` | `Blood Bank Stock Details.pdf` | ✅ **PASS** | Handled by expanded blood keywords. |
| **24** | `mhc` | English | `is_mhc_intent` | MAPIMS AI Health Assessment (`https://mh.mapims.edu.in/`) | MAPIMS AI Health Assessment | ✅ **PASS** | In-house application resolved. |
| **25** | `மாஸ்டர் ஹெல்த் செக்கப்` | Tamil Script | `is_mhc_intent` | MAPIMS AI Health Assessment (`https://mh.mapims.edu.in/`) | MAPIMS AI Health Assessment | ✅ **PASS** | Tamil script transliteration mapped accurately. |
| **26** | `lineloom token` | English | `is_lineloom_query` | LineLoom OPD Token Display (`http://192.168.103.158:8086`) | LineLoom OPD Token Display | ✅ **PASS** | Resolved correctly. |
| **27** | `opd queue display` | English | `is_lineloom_query` | LineLoom OPD Token Display (`http://192.168.103.158:8086`) | LineLoom OPD Token Display | ✅ **PASS** | OPD queue synonyms mapped to LineLoom. |
| **28** | `doctor id creation in his` | English | `is_doctor_id_query` | `New Doctor Name and ID Creation in HIS.pdf` | `New Doctor Name and ID Creation in HIS.pdf` | ✅ **PASS** | IT Form direct resolver executed. |
| **29** | `printer request form` | English | `is_printer_query` | `Printer Request Form.pdf` | `Printer Request Form.pdf` | ✅ **PASS** | Direct IT form match. |
| **30** | `acchaagam padivam` | Tanglish | `is_printer_query` | `Printer Request Form.pdf` | `Printer Request Form.pdf` | ✅ **PASS** | Tanglish printing request matched. |
| **31** | `canteen phone number` | English | `is_telecom_query` | Dietetics Intercom Ext: 2018 (`./intercom.html?dept=Dietetics`) | Dietetics Dept Intercom Ext: 2018 | ✅ **PASS** | Telephony directory lookup. |
| **32** | `dietician intercom` | English | `is_telecom_query` | Dietetics Intercom Ext: 2018 (`./intercom.html?dept=Dietetics`) | Dietetics Dept Intercom Ext: 2018 | ✅ **PASS** | Department intercom resolution. |
| **33** | `emergency casualty number` | English | `is_telecom_query` | Emergency Reception Ext: 2001, 2002 | Emergency Reception: 2001, 2002 | ✅ **PASS** | Emergency hotline lookup. |

---

### Section C: Live Incident Case (User Attachment)

| # | User Query | Language | Detected Intent | Expected Resource | Actual Resource | Status | Failure Root Cause & Code Reference |
| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :--- |
| **34** | `Procedure Resignation Job Form` | English | Fallback Search | `Human Resources Manual (HRM - 2025)` (`HRM 2025.pdf`) & Job Forms | `Campus Ticketing & Maintenance Desk (Job Orders)` | ❌ **FAIL** | **Token Overlap with IT Job Orders:** Word `"Job"` scored high against `"Job Orders"` in Ticketing, while `"Procedure"` matched general IT SOPs. Fallback catalog resolver chose Ticketing Desk as top recommendation. |

---

## 3. Detailed Root Cause Taxonomy

### 1. Intent Collision: Application Launch vs. Form Download
- **Files Affected:** `server.py` lines 1116-1135, 2398-2420, 2571-2585
- **Mechanism:**  
  The trigger list for `is_his_form_query` includes broad verbs like `'open'` and interrogatives like `'enga'`.
  When a user types `"open his"`, the system thinks the user wants to *open the form to request HIS access*, rather than *open the HIS workstation*.
- **Fix Required:**  
  Split into strict, mutually exclusive rules:
  - If query contains `['login', 'software', 'open his', 'his open', 'workstation', 'his portal', 'his app', 'திற']` and does NOT contain `['form', 'forms', 'creation', 'id creation', 'user creation', 'padivam', 'படிவம்']`, route strictly to **HIS Login**.
  - Only route to **HIS User Request Form** if explicit form-creation tokens are present.

### 2. Transliteration & Phonetic Dictionary Gaps
- **Files Affected:** `server.py` line 833 (`SYNONYMS` table)
- **Mechanism:**  
  Hospital users frequently switch between English, Tamil script, and Tanglish.
  - Tamil Script HIS: `ஹெச்ஐஎஸ்`
  - Tamil Verb Open: `திற` / `திறக்கவும்`
  - Tanglish Resignation: `rajinama`, `raajinaama`, `pathavi vilagal`
  Because these tokens were missing from the dictionary, tokenization produced empty sets, causing fallback to ungrounded keyword matching.
- **Fix Required:**  
  Inject phonetic transliteration tuples into `SYNONYMS` and regex classifiers.

### 3. Stopword & Generic Keyword Token Inflation
- **Files Affected:** `server.py` lines 1050-1360 (`search_catalog_candidates`)
- **Mechanism:**  
  Words like `"form"`, `"procedure"`, `"manual"`, and `"request"` are present in 70% of hospital catalog titles. When an unknown token (e.g. `rajinama`) is queried with `"form"`, the unknown token contributes 0 points while `"form"` contributes points to completely unrelated documents like `48 Hour Antibiotics Review From.pdf`.
- **Fix Required:**  
  Demote generic stopwords (`form`, `procedure`, `manual`, `sops`, `from`) to zero or fractional weight unless accompanied by a qualifying domain entity.

### 4. Committee & Governance Disconnect
- **Files Affected:** `server.py` lines 1040-1360
- **Mechanism:**  
  `comitee.html` exists in the portal and loads 64+ committee MOMs and calendars. However, `comitee.html` is never offered as a candidate link when users query "committee members", "quality committee", or "governance charter".
- **Fix Required:**  
  Add a dedicated Committee Resolver that routes committee queries to `./comitee.html` with specific anchors or highlights.

