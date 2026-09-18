# Adhiparasakthi Hospitals - Dynamic JSON Portal Architecture

All hospital operational resources—including **Clinical & Administrative Forms**, **Accreditation Manuals**, **Quality & Governance Committees**, **Recent Circulars**, and the **Intercom Directory**—are loaded dynamically from clean JSON files in this directory (`/data`).

When adding, editing, or archiving documents, **no HTML, React, or JavaScript changes are required**. The web portal automatically refreshes counts, renders document links, applies badges, and updates real-time search indexing.

---

## Directory Index

| JSON File | Purpose | Associated Page |
| :--- | :--- | :--- |
| `consent-forms.json` | Patient consent & medicolegal forms | `consent.html` |
| `common-forms.json` | Clinical, nursing, ICU, lab & safety forms | `commonforms.html` |
| `hr-forms.json` | HR recruitment, leave, privileges & appraisal | `hrforms.html` |
| `it-forms.json` | HIS user creation, hardware & SIM requests | `itforms.html` |
| `forms.json` | Master forms catalog fallback | `index.html` |
| `manuals.json` | NABH 5th & 6th Edition accreditation manuals | `manuals.html` |
| `committees.json` | Quality committees, calendars & verified MOMs | `comitee.html` |
| `circulars.json` | Executive memos & digital e-circulars | `recent circular.html` |
| `intercom.json` | Hospital extension directory by floor & department | `intercom.html` |
| `announcements.json` | Live top-bar marquee ticker announcements & alerts | `index.html` |

---

## 1. How to Add an Accreditation Manual (`data/manuals.json`)

1. Upload the manual PDF to the hospital file server (e.g. `http://192.168.101.75:3000/files/nabh/Cardiology_Manual.pdf`).
2. Open `data/manuals.json`.
3. Find the target edition and category key:
   - `5-nabh`: 5th Edition NABH
   - `5-clinical`: 5th Edition Clinical Manuals
   - `5-nonclinical`: 5th Edition Non-Clinical Manuals
   - `5-policy`: 5th Edition Policy & Procedures
   - `6-nabh`: 6th Edition NABH Manuals
   - `6-clinical`: 6th Edition Clinical Manuals
   - `6-nonclinical`: 6th Edition Non-Clinical Manuals
   - `6-policy`: 6th Edition Policy & Procedures
4. Append an entry to the array:
   ```json
   {
     "title": "Cardiology Department Manual - 2026",
     "url": "http://192.168.101.75:3000/files/nabh/Cardiology_Manual.pdf",
     "isNew": true
   }
   ```
5. Save the file. When opened, `manuals.html` instantly renders the row, shows the **NEW** badge, updates total counts, and includes it in the table search filter.

---

## 2. How to Add a Committee Charter or MOM (`data/committees.json`)

1. Upload the meeting minutes PDF (e.g. `http://192.168.101.75:3000/files/IPC_MOM_SEP_2026.pdf`).
2. Open `data/committees.json`.
3. Add the new entry (usually at the top so recent minutes appear first):
   ```json
   {
     "title": "IPC MOM SEPTEMBER - 2026",
     "url": "http://192.168.101.75:3000/files/IPC_MOM_SEP_2026.pdf",
     "isNew": true
   }
   ```
4. Save the file. `comitee.html` automatically displays the document, adjusts the count badge, and enables instant search filtering.

---

## 3. How to Add a Recent Circular (`data/circulars.json`)

1. Upload the circular PDF (e.g. `http://192.168.101.75:3000/files/Fire_Safety_Drill_2026.pdf`).
2. Open `data/circulars.json`.
3. Add the circular entry at the top:
   ```json
   {
     "title": "Annual Fire Safety Mock Drill Notice - 2026",
     "date": "24.09.2026",
     "url": "http://192.168.101.75:3000/files/Fire_Safety_Drill_2026.pdf",
     "isNew": true
   }
   ```
4. Save the file. `recent circular.html` renders the new entry with date and direct PDF link.

---

## 4. How to Add or Update Forms (`data/common-forms.json`, etc.)

1. Upload your form PDF (e.g. `http://192.168.101.75:3000/files/Clinical_Trial_Consent.pdf`).
2. Open the matching category file (`consent-forms.json`, `common-forms.json`, `hr-forms.json`, or `it-forms.json`).
3. Add your entry under `"forms"`:
   ```json
   {
     "name": "Clinical Trial Informed Consent Protocol",
     "desc": "Bilingual consent protocol for institutional clinical research trials",
     "url": "http://192.168.101.75:3000/files/Clinical_Trial_Consent.pdf",
     "badge": "RESEARCH"
   }
   ```
4. Save the file. Both `index.html` (category card count, hero search, interactive viewer) and the dedicated subpage update immediately.

---

## 5. How to Update Extension Numbers (`data/intercom.json`)

1. Open `data/intercom.json`.
2. Locate the department card or create a new card object:
   ```json
   {
     "floor": "Ground Floor",
     "dept": "Emergency Triage",
     "extensions": [
       { "ext": "2110", "desc": "Triage Counter 1" },
       { "ext": "2111", "desc": "Triage Counter 2" }
     ]
   }
   ```
3. Save the file. `intercom.html` renders the cards with instant live search.
 
---

## 6. How to Add or Edit Announcements (`data/announcements.json`)

All alerts in the top marquee ticker on the homepage (`index.html`) are managed dynamically via `data/announcements.json`. **No code or HTML changes are needed.**

1. Open `data/announcements.json`.
2. To **add a new alert**, append an entry:
   ```json
   {
     "id": "announcement-5",
     "badge": "Water Maintenance",
     "severity": "warning",
     "message": "Routine water tank cleaning in Block B tomorrow 6:00 AM – 8:00 AM.",
     "linkText": "",
     "linkUrl": "",
     "active": true
   }
   ```
   * **`severity`**: Sets the color theme and icon:
     * `"warning"` ⚠️ — Amber theme (scheduled maintenance, drills, system downtime).
     * `"information"` (or `"info"`) ℹ️ — Blue theme (general announcements, policy updates).
     * `"success"` ✓ — Emerald green theme (cleared audits, restored services, achievements).
     * `"urgent"` 🚨 — Rose/Red theme (emergency blood reserves, critical notices).
   * **`badge`** *(Optional)*: Custom label for the category pill (e.g. `IT Alert`, `NABH`, `Blood Bank`, `Clinical Policy`). If omitted, defaults to the severity name.
   * **`message`**: The alert text displayed in the scrolling ticker.
   * **`linkText` & `linkUrl`** *(Optional)*: Text within the message to turn into a clickable link (e.g. `#forms`, `./manuals.html`, or an external URL).
   * **`active`**: Set to `true` to display in the ticker, or `false` to temporarily hide without deleting.
3. To **turn off an announcement**, simply set `"active": false`.
4. If there are no active announcements (or the array is empty `[]`), the marquee bar **automatically hides itself** so it takes zero space.
5. Save the file. The homepage marquee refreshes dynamically.
