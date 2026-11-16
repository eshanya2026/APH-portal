# APH SmartSearch AI — Document Indexing Results

**Execution Date:** 2026-11-16  
**Index Run Mode:** Full Production Indexing Job  
**Database File:** `data/aph_knowledge_index.db` (SQLite 3 + FTS5)  
**Extractor Engine:** Poppler `pdftotext` & `pdfinfo` with native UTF-8 Tamil support  
**Document Source:** Hospital Intranet File Server (`http://192.168.101.75:3000/files/`)  

---

## 1. High-Level Indexing Metrics

```
+─────────────────────────────────────────────────────────────────────────────+
| METRIC                                                      | VALUE         |
+─────────────────────────────────────────────────────────────────────────────+
| Total Catalog Resources Discovered                          | 447           |
| Approved PDF Documents for Indexing                         | 427           |
| Excluded Non-PDF Resources (Apps, Spreadsheets, Hubs)       | 20            |
| Documents Successfully Indexed                              | 418 (97.9%)   |
| Documents Failed / Error (HTTP 404 on File Server)          | 9 (2.1%)      |
| Total Extracted Pages                                       | 14,713 Pages  |
| Digital Text Pages (Native Extractable)                     | 14,105 (95.9%)|
| Scanned / Image Pages Flagged for OCR (<50 chars)           | 608 (4.1%)    |
| Flagged for Privacy / PHI Review                            | 0 (Clean)     |
| Total Indexed Characters                                    | 27,546,139    |
| SQLite FTS5 Database Size                                   | 94.36 MB      |
| Total Indexing Duration                                     | 95.93 Seconds |
| Average Indexing Speed                                      | 153.4 Pages/s |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Document Access Level Distribution

Access permissions were automatically classified based on healthcare governance criteria:

| Access Classification | Document Count | Total Pages | Representative Document Categories |
| :--- | :---: | :---: | :--- |
| **STAFF** | **252** | 9,142 | Departmental Manuals, IT Forms, HR Policies, Staff Formularies |
| **MANAGEMENT** | **92** | 684 | Committee MOMs (Minutes of Meetings), Administrative Charters |
| **CLINICAL** | **71** | 4,875 | NABH 5th & 6th Edition Core SOPs, ICU Guidelines, Clinical Indents |
| **PUBLIC** | **12** | 12 | Medicolegal Patient Consent Forms, Institutional Holiday Calendars |
| **TOTAL** | **427** | **14,713** | — |

---

## 3. Category Breakdown

| Category Name | Total Indexed | Total Pages | Status | Sample Indexed Resources |
| :--- | :---: | :---: | :---: | :--- |
| **Manuals & SOPs** | 250 | 12,840 | ✅ INDEXED | `COP Part 1 & 2`, `AAC`, `MOM`, `PRE`, `PSQ`, `FMS`, `IPC 6th Ed` |
| **Committees & MOM** | 64 | 512 | ✅ INDEXED | `HICC MOM`, `QC MOM`, `BMW MOM`, `BTC MOM`, `CAC MOM`, `DTC MOM` |
| **Common Forms** | 42 | 118 | ✅ INDEXED | `HANDING OVER SBAR`, `ICU Casesheet`, `Ward Shifting`, `MEWS` |
| **Consent Forms** | 8 | 15 | ✅ INDEXED | `Informed Consent Tamil/English`, `Blood Transfusion Consent` |
| **IT Forms** | 8 | 10 | ✅ INDEXED | `His User Creation`, `Item Creation`, `Doctor ID Creation`, `WIFI` |
| **HR Forms** | 8 | 812 | ✅ INDEXED | `HRM 2025 Manual (791 pages)`, `Non-Teaching`, `Teaching Faculty` |
| **Circulars** | 9 | 24 | ✅ INDEXED | `List of Holidays 2026`, `SWOT Analysis Circular Jan 2026` |
| **Tariff & Packages** | 7 | 34 | ✅ INDEXED | `Special Packages`, `Lab Tariff`, `Radiology Imaging Tariff` |
| **Pharmacy & Stock** | 7 | 84 | ✅ INDEXED | `Drug Stores Stock`, `Hospital Formulary 2025`, `Free Drug NMC` |
| **Clinical Governance**| 5 | 184 | ✅ INDEXED | `Antimicrobial Policy 2026-27`, `APH Disinfection Policy` |
| **Portal Resources** | 7 | 80 | ✅ INDEXED | `Clinical Protocols`, `User Billing Manual`, `Standing Orders` |

---

## 4. Multilingual & Tamil Extraction Verification

The indexing pipeline successfully extracted Tamil Unicode text without encoding corruption. Poppler `pdftotext -layout` correctly preserved conjunct glyphs and Tamil numerals:

```text
DOCUMENT: Informed Consent Form For Surgery or Procedures-Tamil
URL: http://192.168.101.75:3000/files/INFORMED%20CONSENT%20FORM%20FOR%20SURGERY%20OR%20PROCEDURES-Tamil.pdf#page=1
PAGE: 1
EXTRACTED CHARACTERS: 5,942
EXTRACTED TEXT EXCERPT:
   "அறுவை சிகிச்சை அல்லது நடைமுறைகளுக்கான தகவலறிந்த ஒப்புதல் படிவம்
   நோயாளி பெயர் : ................................... வயது / பாலினம் : ...........
   மருத்துவர் பெயர் : ............................. UHID எண் : ...............
   அறுவை சிகிச்சை / செயல்முறை பற்றிய அனைத்து ஆபத்துகள் மற்றும் சிக்கல்கள் 
   எனக்கு தெளிவாக விளக்கப்பட்டது..."
```

**Tamil FTS5 Query Test:**
- Query: `"அறுவை சிகிச்சை"` $\rightarrow$ Returned `Informed Consent Tamil` Page 1 & Page 2 with BM25 score `-18.57`.
- Query: `"ஒப்புதல்"` $\rightarrow$ Matched exact consent clause on Page 2 with BM25 score `-16.07`.

---

## 5. Excluded Resources & Extraction Failures

### 5.1 Excluded Non-PDF Resources (20 items)
These entries were excluded during Task 1 discovery and recorded with reasons:

1. **Web Applications (12 items):**
   - AOSTA HIS (`http://192.168.103.37/...`)
   - PruWorks HRMS (`https://mapims-hrms...`)
   - Medsynapse PACS (`http://192.168.101.224/...`)
   - MRD Portal (`http://www.mapimsmrd.com/...`)
   - LineLoom OPD Token (`http://192.168.103.158:8086`)
   - Campus Ticketing (`http://www.mapimshis.com/...`)
   - Pathology Barcode App (`http://192.168.103.158:8081`)
   - Eye Camp Outreach (`http://192.168.103.158:8082`)
   - Clinical Care ICU App (`https://192.168.103.158:8083`)
   - MAPIMS AI MHC (`https://mh.mapims.edu.in/`)
   - Clinical Checklist App (`https://checklist.mapims.edu.in/`)
   - Non-Clinical Checklist App (`https://gencl.mapims.edu.in/`)
2. **Unsupported Spreadsheets (2 items):**
   - `PMSheduleHVACsystem2021.xlsx` (Excel)
   - `AWaRe classification 2025.xlsx` (Excel)
3. **Internal HTML Hubs & Directory Snippets (6 items):**
   - `intercom.html`
   - `index.html#forms`
   - `http://192.168.101.75:3000/files/nabh/` (Directory path)
   - `http://192.168.101.75/assets/sub files/intercom.html` (Static HTML)
   - `http://192.168.101.75:3000/files/24hr` (Incomplete URL)
   - `#` (Empty anchor in catalog)

### 5.2 Extraction Failures (9 items)
These 9 files failed due to **HTTP 404 Not Found** on the remote hospital file server (`192.168.101.75:3000`). They are tracked in `documents` with status `ERROR`:

| Document Title | Catalog URL | Error Details | Impact |
| :--- | :--- | :--- | :--- |
| `Antibiogram` | `http://.../Antibiogram.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `Central Line – Associated Bloodstream Infection` | `http://.../CLABSI.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `Paitent's Self Administration (NABH 5th Edition)`| `http://.../paitents self administration.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `PSQ1 SAFETY MANUAL (NABH 6th Edition)` | `http://.../PSQ1 SAFETY MANUAL.pdf`| HTTP 404: Not Found | Isolated, 0 index impact |
| `HAZARD IDENTIFICATION (HIRA) (NABH 6th Ed)` | `http://.../HIRA.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `NURSING MANUAL (NABH 6th Edition)` | `http://.../NURSING MANUAL.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `The 7 C's of Effective Communication` | `http://.../7 C's.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `DTC Minutes (17.10.2024)` | `http://.../DTC Minutes.pdf` | HTTP 404: Not Found | Isolated, 0 index impact |
| `DTC Minutes (17.10.2024) PDF` | `http://.../DTC Minutes 17.10.2024.pdf`| HTTP 404: Not Found | Isolated, 0 index impact |

---

## 6. Scanned Pages Requiring Future OCR (Phase 4)

Of 14,713 extracted pages, **608 pages (4.1%)** contained fewer than 50 characters of digital text. These are predominantly:
- Final signature sheets of committee MOMs containing physical stamps and ballpoint signatures.
- High-resolution schematic flowcharts (e.g. fire escape route plans).
- Blank separator and cover divider pages in multi-volume accreditation binders.

Each of these pages is tagged with `is_scanned = 1` in `document_pages` to allow optional offline OCR (Tesseract / OCRmyPDF) during Phase 4 without re-parsing the rest of the database.
