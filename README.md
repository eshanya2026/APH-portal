# Adhiparasakthi Hospitals & Research Institute (APH) — Intranet Portal

[![Hospital Status](https://img.shields.io/badge/Hospital-MAPIMS%20%2F%20APH-blue.svg)](https://www.mapims.org)
[![Accreditation](https://img.shields.io/badge/Accreditation-NABH%20%7C%20JCI%20Standards-emerald.svg)](#)
[![Tech Stack](https://img.shields.io/badge/Stack-HTML5%20%7C%20TailwindCSS%20%7C%20Vanilla%20JS-38bdf8.svg)](#)
[![License](https://img.shields.io/badge/License-Internal%20Hospital%20Use-slate.svg)](#)

A centralized, responsive enterprise intranet portal designed for **Adhiparasakthi Hospitals & Research Institute (Melmaruvathur, Tamil Nadu)**. The portal provides hospital clinicians, nurses, administrative staff, and technicians with instant, unified access to core clinical systems, in-house web applications, NABH/JCI accreditation governance, standardized medical forms, live circulars, and departmental directories.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Portal Architecture & Modules](#-portal-architecture--modules)
- [Directory Structure](#-directory-structure)
- [Technology Stack](#-technology-stack)
- [Quick Start / How to Run](#-quick-start--how-to-run)
- [Module Breakdown & Dedicated Hubs](#-module-breakdown--dedicated-hubs)
  - [1. Core Enterprise Systems](#1-core-enterprise-systems)
  - [2. In-House Clinical Applications](#2-in-house-clinical-applications)
  - [3. Accreditation & Governance Hub](#3-accreditation--governance-hub)
  - [4. Standardized Forms & Requisitions Vault](#4-standardized-forms--requisitions-vault)
  - [5. Intercom & Telephony Directory](#5-intercom--telephony-directory)
  - [6. Digital Circulars & Transparency Data](#6-digital-circulars--transparency-data)
  - [7. Quick Help & Contacts (Help Desk)](#7-quick-help--contacts-help-desk)
- [Intranet Network Configuration](#-intranet-network-configuration)
- [Maintenance & Development Guidelines](#-maintenance--development-guidelines)
- [Institution Details](#-institution-details)

---

## 🌟 Key Features

* **Single Pane of Glass**: Direct single-click entry into AOSTA HIS, PACS Radiology, LIMS Lab, HRMS, and Pharmacy Management.
* **Instant Intranet Search**: Real-time keyword filtering and fuzzy search across hospital forms, committee records, intercom extensions, tariffs, and SOPs.
* **Accreditation Governance (NABH / JCI)**: Dedicated hubs for quality manuals, standard operating procedures, and 24+ statutory committee records.
* **Standardized Clinical & Operational Forms**: Direct access to 70+ officially approved PDFs, including bilingual English & Tamil surgical consents, ICU checklists, SBAR handover sheets, and HR applications.
* **Real-Time Telephony Directory**: Searchable intercom directory with live departmental search and instant emergency extension lookups (Casualty, Code Blue, ICU, Blood Bank).
* **Interactive Ticketing & Checklists**: In-browser interactive modals for IT breakdown logging, daily clinical audit checklists, and zero-billing paperless workflows.
* **Mobile-First Responsive Layout**: Built with Tailwind CSS and fully responsive across mobile phones, tablets, nurse station workstations, and OPD desktop monitors.

---

## 🏛️ Portal Architecture & Modules

```
                    ┌──────────────────────────────────────────────┐
                    │      APH Hospital Master Intranet Portal     │
                    │                 (index.html)                 │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌───────────────────┬─────────────┴───────┬───────────────────┐
         │                   │                     │                   │
┌────────▼────────┐ ┌────────▼────────┐   ┌────────▼────────┐ ┌────────▼────────┐
│ Enterprise Apps │ │ Governance Hub  │   │   Forms Vault   │ │ Campus Directory│
├─────────────────┤ ├─────────────────┤   ├─────────────────┤ ├─────────────────┤
│ • AOSTA HIS     │ │ • manuals.html  │   │ • consent.html  │ │ • intercom.html │
│ • PACS Imaging  │ │ • comitee.html  │   │ • commonforms.html│ • Intercom PDF  │
│ • LineLoom Token│ │ • circular.html │   │ • hrforms.html  │ │ • Emergency Hot-│
│ • Eye Camp App  │ │ • Apex / CQIC   │   │ • itforms.html  │ │   lines         │
└─────────────────┘ └─────────────────┘   └─────────────────┘ └─────────────────┘
```

---

## 📂 Directory Structure

```plaintext
aph-portal/
├── index.html                  # Main Hospital Intranet Landing Hub
├── manuals.html                # Quality Manuals, NABH/JCI SOPs & Policies
├── comitee.html                # Hospital Accreditation Committees & Charters
├── recent circular.html        # Administrative Memorandums, Rosters & Circulars
├── consent.html                # Medicolegal Informed Consent Forms (Bilingual)
├── commonforms.html            # Clinical Protocols, ICU Checklists & Indents
├── hrforms.html                # HR Staff Applications, Appraisals & Manuals
├── itforms.html                # IT Provisioning, HIS Credentials & Breakdown Desk
├── intercom.html               # Searchable Campus Intercom & Telephone Directory
├── Intercom Directory.pdf      # Official Printable Telephony Directory PDF
├── assets/
│   ├── images/                 # System Logos, Clinical Icons, Campus Photography
│   │   ├── aosta-proper.png    # AOSTA HIS Logo
│   │   ├── mapims.png          # MAPIMS Official Seal
│   │   ├── LineLoom.png        # Queue & Token Management Icon
│   │   ├── Eyecamp.png         # Community Ophthalmology Icon
│   │   ├── Pathology.png       # Laboratory Information System Icon
│   │   └── ...                 # Additional UI assets
│   └── sub files/              # Sub-hub legacy templates and resources
└── README.md                   # Project Documentation (this file)
```

---

## 💻 Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Markup & Semantics** | HTML5 with ARIA accessibility roles and metadata |
| **Styling & Design System** | Tailwind CSS (v3+), custom gradients, responsive flexbox & CSS grid |
| **Icons & Typography** | Inline SVG icons (Lucide / Feather inspired), Google Fonts (*Plus Jakarta Sans* & *Inter*) |
| **Interactivity & Search** | Vanilla JavaScript (ES6+), pure client-side fast search indexing |
| **Serverless Feedback** | Web3Forms REST API for employee query submissions without custom backend |
| **Target Viewports** | Desktop (1920x1080, 1440x900), Tablets (iPad 768px), Mobile (iPhone / Android 375px - 412px) |

---

## 🚀 Quick Start / How to Run

Because the portal is built using standard modern web technologies, it requires **no complex build tool or compiler**. It can be served using any web server.

### 1. Using Python (Recommended for Local Dev & Testing)
Open a terminal in the project root directory and run:
```bash
# Python 3
python3 -m http.server 3000
```
Then visit:
👉 **`http://localhost:3000/index.html`**

### 2. Using Node.js / npx
```bash
# Using 'serve'
npx serve . -p 3000
```

### 3. Using PHP Built-in Server
```bash
php -S localhost:3000
```

### 4. Production Deployment (Nginx / Apache / IIS)
Place the contents of this repository into your web server's public root (e.g. `/var/www/html/` for Nginx/Apache or `C:\inetpub\wwwroot\` for IIS). Ensure that:
- `index.html` is configured as the default index document.
- MIME types for `.pdf`, `.png`, `.jpg`, and `.svg` are properly enabled.

---

## 🔍 Module Breakdown & Dedicated Hubs

### 1. Core Enterprise Systems
Located at the top of `index.html`, providing rapid authentication gateways:
- **AOSTA HIS**: Patient registration, OPD/IPD billing, consultation orders, ward management.
- **PACS Imaging**: High-speed DICOM viewer for Radiology (X-Ray, CT, MRI, Ultrasound).
- **LIMS Lab**: Real-time pathology sample tracking, analyzer telemetry, and automated report sign-offs.
- **HRMS Portal**: Employee biometrics, attendance logging, leave approval, and monthly salary slips.
- **Pharmacy System**: Central drug stock, expiry tracking, narcotic registers, and ward dispensing.
- **EMR Clinical**: Longitudinal electronic patient records and clinical history.

### 2. In-House Clinical Applications
Dedicated section highlighting hospital-developed technological innovations:
- **LineLoom Token Display**: Smart OPD queue display system with department-wise token sequencing.
- **Patient Barcode Generator**: Code-128 barcode generator for sample tubes, wristbands, and casefiles.
- **Eye Camp Screening App**: Mobile-optimized field screening tool for rural community outreach camps.
- **MAPIMS AI Tele-Consultation**: AI-assisted clinical guideline prompt system for telemedicine.
- **Clinical Audit Checklist**: Interactive modal for daily IPD case documentation and nursing safety audits.
- **Paperless Zero-Billing Desk**: Streamlined NMC-compliant free medicine and subsidized surgical workflow.

### 3. Accreditation & Governance Hub
Compliant with **NABH 5th Edition** and **JCI Standards**:
- `manuals.html`: Access to hospital quality manuals, departmental SOPs, infection control manuals, and medication safety guidelines.
- `comitee.html`: Detailed directory of 24 statutory hospital governance committees including Apex Quality, Hospital Infection Control (HICC), Pharmacovigilance, Code Blue Audit, and Disaster Management.
- `recent circular.html`: Administrative gazette, duty rosters, holiday schedules, and urgent notifications.

### 4. Standardized Forms & Requisitions Vault
Categorized repository of official, uneditable hospital forms:
- `consent.html`: Informed consent documents (Bilingual English & Tamil surgical consents, blood transfusion, DAMA, pediatric care).
- `commonforms.html`: Clinical documentation templates (ICU casesheet checklists, SBAR handover, ADR forms, emergency medication lists).
- `hrforms.html`: HR requisition documents (Teaching faculty applications, staff promotions, training feedback, non-teaching recruitment).
- `itforms.html`: Systems & hardware provisioning (HIS account creation, doctor clinician IDs, Wi-Fi authorization, toner replacements).

### 5. Intercom & Telephony Directory
- `intercom.html`: Fully interactive digital phonebook featuring instant search by extension number, department name, or staff designation.
- High-priority quick hotlines permanently highlighted:
  - **Casualty / Trauma**: Ext. `2100` / `2101`
  - **ICU / Code Blue**: Ext. `5555`
  - **Blood Bank Station**: Ext. `2450`
  - **IT Help Desk / Server**: Ext. `8888`
- Printable official copy available via `Intercom Directory.pdf`.

### 6. Digital Circulars & Transparency Data
- **Live Duty Rosters**: Direct links to daily Casualty CMO and Nursing Supervisor rosters.
- **Blood Bank Stocks**: Live inventory status of PRBC, FFP, Platelets, and rare group reserves.
- **Hospital Billing Tariff & Formulary**: Detailed package rates and essential medicine drug lists.

### 7. Quick Help & Contacts (Help Desk)
- Centered digital form on the homepage routed directly to IT Management (`itmgmt@mapims.edu.in`) via Web3Forms API.
- Captures Employee Name, Official Email, Employee ID, Extension, and detailed feedback or facility issue notes.

---

## 🌐 Intranet Network Configuration

The portal references authentic intranet storage repositories. For full document download capability within the hospital local area network:
- **Intranet File Server IP**: `192.168.101.75:3000/files/`
- Documents are served over standard HTTP with `target="_blank"` and `rel="noopener noreferrer"` for security and uninterrupted navigation.
- If deploying to a different subnet or offline standalone server, update the base file URLs or place corresponding PDFs in a local `files/` folder.

---

## 🛠️ Maintenance & Development Guidelines

1. **Adding New Forms**:
   - Save the approved PDF file to the intranet file server.
   - Add a row in the respective category sub-file (`consent.html`, `commonforms.html`, `hrforms.html`, or `itforms.html`).
   - If the form is a top-priority item, add a quick link in Section 9 of `index.html`.
   - Update the searchable index in `index.html` inside the `searchDatabase` array.

2. **Styling Best Practices**:
   - Maintain the institutional color palette:
     - **Blue** (`#2563eb`): Medicolegal & Primary Corporate actions
     - **Amber / Orange** (`#d97706`): Clinical indent, pharmacy & ICU operations
     - **Purple** (`#9333ea`): HR & Privileging
     - **Teal / Emerald** (`#0d9488`): IT, Network & Infrastructure
     - **Rose / Red** (`#e11d48`): Emergency, Code Blue & Casualty
   - Ensure all interactive elements have appropriate `:hover`, `:focus-visible`, and active transition states.

---

## 🏥 Institution Details

**Melmaruvathur Adhiparasakthi Institute of Medical Sciences and Research (MAPIMS / APH)**  
Melmaruvathur, Cheyyur Taluk, Chengalpattu / Kancheepuram District,  
Tamil Nadu - 603319, India.  

*Official Portal for Internal Hospital & Medical College Personnel.*
