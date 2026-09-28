#!/usr/bin/env python3
"""
Generates data/portal_catalog.json by compiling all verified forms, documents,
manuals, committees, circulars, tariffs, and systems across the APH Portal.
Normalizes URLs and captures every single document link across JSON and HTML files.
"""
import json
import os
import re
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

catalog = []
seen_canonical_urls = set()

def canonicalize_url(u):
    """Normalize URL by stripping spaces, unquoting, and lowercasing for de-duplication."""
    if not u:
        return ''
    u = u.strip()
    # Unquote and re-normalize
    unquoted = urllib.parse.unquote(u)
    return unquoted.strip()

def add_entry(title, url, category, description='', badge='PDF', hub_page=''):
    title = (title or '').strip()
    url = (url or '').strip()
    if not title or not url:
        return
    # Skip JS template literals
    if '${' in title or '${' in url:
        return
    # Clean HTML tags and excessive whitespace
    title = re.sub(r'<[^>]+>', ' ', title)
    title = ' '.join(title.split())
    if not title or title.lower() in ['open pdf document', 'view pdf', 'view', 'download', 'read more', 'click here']:
        return

    # Strip any accidental trailing whitespace from URL
    url = url.strip()
    canon = canonicalize_url(url)
    
    if canon in seen_canonical_urls:
        return
    seen_canonical_urls.add(canon)
    
    catalog.append({
        "title": title,
        "url": url,
        "canonicalUrl": canon,
        "category": category,
        "description": description.strip() if description else f"{title} ({category})",
        "badge": badge.strip() if badge else "Document",
        "hubPage": hub_page
    })

# 1. Consent Forms
try:
    with open(os.path.join(DATA_DIR, 'consent-forms.json'), 'r', encoding='utf-8') as f:
        d = json.load(f)
        for item in d.get('forms', []):
            add_entry(
                title=item.get('name'),
                url=item.get('url'),
                category="Consent Forms",
                description=item.get('desc', 'Medicolegal clinical consent protocol'),
                badge="Medicolegal",
                hub_page="./consent.html"
            )
except Exception as e:
    print(f"Error loading consent-forms.json: {e}")

# 2. Common & Clinical Forms
try:
    with open(os.path.join(DATA_DIR, 'common-forms.json'), 'r', encoding='utf-8') as f:
        d = json.load(f)
        for item in d.get('forms', []):
            add_entry(
                title=item.get('name'),
                url=item.get('url'),
                category="Common Forms",
                description=item.get('desc', 'Clinical operational indent, checklist and protocol'),
                badge="Clinical",
                hub_page="./commonforms.html"
            )
except Exception as e:
    print(f"Error loading common-forms.json: {e}")

# 3. HR Forms & Policies
try:
    with open(os.path.join(DATA_DIR, 'hr-forms.json'), 'r', encoding='utf-8') as f:
        d = json.load(f)
        for item in d.get('forms', []):
            add_entry(
                title=item.get('name'),
                url=item.get('url'),
                category="HR Forms",
                description=item.get('desc', 'Human Resources application, policy or manual'),
                badge="HR",
                hub_page="./hrforms.html"
            )
except Exception as e:
    print(f"Error loading hr-forms.json: {e}")

# 4. IT Forms & Hardware Requests
try:
    with open(os.path.join(DATA_DIR, 'it-forms.json'), 'r', encoding='utf-8') as f:
        d = json.load(f)
        for item in d.get('forms', []):
            add_entry(
                title=item.get('name'),
                url=item.get('url'),
                category="IT Forms",
                description=item.get('desc', 'IT infrastructure, HIS access & hardware requisition'),
                badge="IT",
                hub_page="./itforms.html"
            )
except Exception as e:
    print(f"Error loading it-forms.json: {e}")

# 5. Committees & Meeting Minutes (MOM)
try:
    with open(os.path.join(DATA_DIR, 'committees.json'), 'r', encoding='utf-8') as f:
        items = json.load(f)
        for item in items:
            add_entry(
                title=item.get('title'),
                url=item.get('url'),
                category="Committees & MOM",
                description="Statutory hospital committee meeting minutes, audit calendar, or clinical governance record",
                badge="Committee",
                hub_page="./comitee.html"
            )
except Exception as e:
    print(f"Error loading committees.json: {e}")

# 6. Recent Circulars & Administrative Orders
try:
    with open(os.path.join(DATA_DIR, 'circulars.json'), 'r', encoding='utf-8') as f:
        items = json.load(f)
        for item in items:
            add_entry(
                title=item.get('title'),
                url=item.get('url'),
                category="Circulars",
                description=f"Official institutional circular dated {item.get('date', '2026')}",
                badge="Circular",
                hub_page="./recent circular.html"
            )
except Exception as e:
    print(f"Error loading circulars.json: {e}")

# 7. NABH Manuals, SOPs & Policies
try:
    with open(os.path.join(DATA_DIR, 'manuals.json'), 'r', encoding='utf-8') as f:
        m = json.load(f)
        for cat_key, items in m.items():
            edition = "NABH 5th Edition" if cat_key.startswith("5") else "NABH 6th Edition"
            sub_type = "Clinical SOP" if "clinical" in cat_key else ("Policy Manual" if "policy" in cat_key else ("Non-Clinical SOP" if "nonclinical" in cat_key else "Departmental Manual"))
            for item in items:
                add_entry(
                    title=f"{item.get('title')} ({edition})",
                    url=item.get('url'),
                    category="Manuals & SOPs",
                    description=f"{edition} {sub_type} departmental standard operating procedure",
                    badge="Manual",
                    hub_page="./manuals.html"
                )
except Exception as e:
    print(f"Error loading manuals.json: {e}")

# 8. Core Hospital Applications & Portals
systems = [
    {
        "title": "HIS System (Backbone / Admin Login)",
        "url": "http://192.168.103.37/BB15SE/Backbone/admin/login.aspx",
        "category": "Core Systems",
        "description": "Hospital Information System for patient IP/OP registration, billing, orders & clinical documentation",
        "badge": "HIS System",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "M - PACS (Medsynapse Radiology DICOM Viewer)",
        "url": "http://192.168.101.224/User_Login.asp",
        "category": "Core Systems",
        "description": "Radiology PACS DICOM viewer for X-Ray, CT scans, Ultrasound & MRI medical imaging",
        "badge": "PACS System",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "PruWorks HRMS (Staff Attendance, Leave & Payroll)",
        "url": "https://mapims-hrms.tecvinesolutions.com",
        "category": "Core Systems",
        "description": "Employee biometric attendance, leave applications, pay slips, salary and shift schedule portal",
        "badge": "HRMS",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "HRMS Staff Self-Service Login",
        "url": "http://www.mapims.online/staff",
        "category": "Core Systems",
        "description": "Hospital employee self-service login portal",
        "badge": "HRMS",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "HRMS Admin Management Portal",
        "url": "http://www.mapims.online/",
        "category": "Core Systems",
        "description": "Administration portal for HR management, recruitment and employee records",
        "badge": "HRMS",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Campus Ticketing & Maintenance Desk (Job Orders)",
        "url": "http://www.mapimshis.com/mapims/",
        "category": "Core Systems",
        "description": "Institutional ticketing system to lodge IT, HIS, biomedical, civil and electrical job orders",
        "badge": "Ticketing",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Medical Records Department (FIT MRD Portal)",
        "url": "http://www.mapimsmrd.com/mapimsmrd/",
        "category": "Core Systems",
        "description": "Digital discharge summary archiving and patient medical records tracking",
        "badge": "MRD Portal",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Laboratory Pathology Barcode App v2.4.4",
        "url": "http://192.168.103.158:8081",
        "category": "Clinical Apps",
        "description": "Central clinical laboratory sample barcoding and tube tracking module",
        "badge": "Clinical App",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Community Health Eye Camp-25 Outreach",
        "url": "http://192.168.103.158:8082",
        "category": "Clinical Apps",
        "description": "Ophthalmology community outreach, camp registration and patient screening tool",
        "badge": "Clinical App",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Clinical Care Counselling & ICU App",
        "url": "https://192.168.103.158:8083",
        "category": "Clinical Apps",
        "description": "Critical care counselling notes, psychological consults and ICU encrypted logs",
        "badge": "Clinical App",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "LineLoom Token Engine (OPD Live Stream)",
        "url": "http://192.168.103.158:8086",
        "category": "Clinical Apps",
        "description": "Real-time OPD queue flow, patient token engine and digital waiting display",
        "badge": "Clinical App",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "MAPIMS AI Health Assessment",
        "url": "https://mh.mapims.edu.in/",
        "category": "Clinical Apps",
        "description": "Health assessment and digital clinical screening application",
        "badge": "Clinical App",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Clinical Checklist App",
        "url": "https://checklist.mapims.edu.in/",
        "category": "Clinical Apps",
        "description": "Daily nursing checklists and paperless clinical workflows",
        "badge": "Clinical App",
        "hub_page": "./index.html#applications"
    },
    {
        "title": "Non-Clinical Checklist App",
        "url": "https://gencl.mapims.edu.in/",
        "category": "Operational Apps",
        "description": "Hospital sanitation, housekeeping and general facilities checklists",
        "badge": "Checklist App",
        "hub_page": "./index.html#applications"
    }
]
for s in systems:
    add_entry(s["title"], s["url"], s["category"], s["description"], s["badge"], s["hub_page"])

# 9. Hospital Tariffs, Drug Stocks & Operational Documents from index.html
portal_docs = [
    {
        "title": "Special Treatment & Health Packages (04.05.2026)",
        "url": "http://192.168.101.75:3000/files/Adhiparasakthi Hospitals Special Packages (04.05.2026).pdf",
        "category": "Tariff & Packages",
        "description": "Approved hospital inpatient admission and surgical package charges",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Laboratory Investigation Tariff",
        "url": "http://192.168.101.75:3000/files/Lab Tariff.pdf",
        "category": "Tariff & Packages",
        "description": "Pathology, biochemistry, microbiology and haematology lab test charges",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Radiology Imaging Tariff",
        "url": "http://192.168.101.75:3000/files/Radiology Tariff.pdf",
        "category": "Tariff & Packages",
        "description": "X-Ray, Ultrasound, CT, MRI and interventional imaging investigation charges",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Physiotherapy Department Tariff",
        "url": "http://192.168.101.75:3000/files/Physiotherapy Tariff.pdf",
        "category": "Tariff & Packages",
        "description": "Physical therapy, rehabilitation, electrotherapy and traction treatment rates",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "General Ward Surgery OT Tariff",
        "url": "http://192.168.101.75:3000/files/General Ward Surgery OT Tariff.pdf",
        "category": "Tariff & Packages",
        "description": "Operating theatre charges, surgeon fees and general ward surgical packages",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "ICU and Special Ward Room Tariff",
        "url": "http://192.168.101.75:3000/files/ICU and Special Ward Room Tariff.pdf",
        "category": "Tariff & Packages",
        "description": "Intensive Care Unit bed charges, deluxe room, AC and special ward tariffs",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Other Departments Tariff",
        "url": "http://192.168.101.75:3000/files/Other Department Tariff.pdf",
        "category": "Tariff & Packages",
        "description": "Specialty clinical departmental tariffs and outpatient service charges",
        "badge": "Tariff PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Drug Stores Stock Details",
        "url": "http://192.168.101.75:3000/files/Drug Stores Stock Details.pdf",
        "category": "Pharmacy & Stock",
        "description": "Central pharmacy drug inventory and active stock counts (139 items)",
        "badge": "Stock PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "IP Pharmacy Stock Details",
        "url": "http://192.168.101.75:3000/files/IP Pharmacy Stock Details.pdf",
        "category": "Pharmacy & Stock",
        "description": "Inpatient ward pharmacy current stock balance (77 items)",
        "badge": "Stock PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Insurance Pharmacy Stock Details",
        "url": "http://192.168.101.75:3000/files/Insurance Pharmacy Stock Details.pdf",
        "category": "Pharmacy & Stock",
        "description": "TPA / Insurance pharmacy inventory and approved formulary stock (515 items)",
        "badge": "Stock PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "OP Pharmacy Stock Details",
        "url": "http://192.168.101.75:3000/files/Op Pharmacy Stock  Details.pdf",
        "category": "Pharmacy & Stock",
        "description": "Outpatient dispensing pharmacy stock details (90 items)",
        "badge": "Stock PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Hospital Formulary - 2025",
        "url": "http://192.168.101.75:3000/files/Hospital Formulary - 2025.pdf",
        "category": "Pharmacy & Stock",
        "description": "Official APH hospital drug formulary, dosage recommendations and generic catalog",
        "badge": "Formulary PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Free Drug List (NMC)",
        "url": "http://192.168.101.75:3000/files/Pharmacy_Updated_11.05.26.pdf",
        "category": "Pharmacy & Stock",
        "description": "National Medical Commission approved complimentary hospital medicines list",
        "badge": "Formulary PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Inventory Stock Details 2024",
        "url": "http://192.168.101.75:3000/files/Inventory Stock Details 2024.pdf",
        "category": "Pharmacy & Stock",
        "description": "Biomedical and general store hospital equipment inventory status",
        "badge": "Stock PDF",
        "hub_page": "./index.html#tariff-stock"
    },
    {
        "title": "Blood Bank Stock Details",
        "url": "http://192.168.101.75:3000/files/Blood Bank Stock Details.pdf",
        "category": "Clinical Governance",
        "description": "Real-time blood components, PRBC, FFP, platelets units stock register",
        "badge": "Stock PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "24-Hour Doctor On-Duty Roster",
        "url": "http://192.168.101.75:3000/files/24hr%27s%20Duty%20Details.pdf",
        "category": "Clinical Governance",
        "description": "Casualty, ICU, surgical and specialist medical officers on-call schedule",
        "badge": "Roster",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "MLC & Police Station Hotlines",
        "url": "http://192.168.101.75:3000/files/police.pdf",
        "category": "Clinical Governance",
        "description": "Local jurisdiction police stations and Medico-Legal Case reporting emergency hotlines",
        "badge": "Contact PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "Clinical Protocols & Standing Orders",
        "url": "http://192.168.101.75:3000/files/clinical.pdf",
        "category": "Clinical Governance",
        "description": "Inpatient clinical treatment protocols and medical management directives",
        "badge": "Protocol PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "User Billing Manual",
        "url": "http://192.168.101.75:3000/files/billingmanual.pdf",
        "category": "Operational Manuals",
        "description": "Hospital billing desk, IP discharge billing and cashier SOP handbook",
        "badge": "Manual PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "Nursing Operations Manual",
        "url": "http://192.168.101.75:3000/files/nursingmanual.pdf",
        "category": "Operational Manuals",
        "description": "Standard operating procedures and nursing protocols for general and intensive care wards",
        "badge": "Manual PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "Official Staff Email Directory",
        "url": "http://192.168.101.75:3000/files/email.pdf",
        "category": "Staff Directory",
        "description": "Official institutional faculty and departmental email directory",
        "badge": "Directory PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "Medical Abbreviations Register",
        "url": "http://192.168.101.75:3000/files/Abrrevation.pdf",
        "category": "Clinical Governance",
        "description": "NABH standard approved clinical abbreviations register and 'Do Not Use' list",
        "badge": "Register PDF",
        "hub_page": "./index.html#resources"
    },
    {
        "title": "Campus Intercom & Extension Directory PDF",
        "url": "http://192.168.101.75:3000/files/Intercom Directory.pdf",
        "category": "Staff Directory",
        "description": "Official campus telephone extension directory PDF with internal department lines",
        "badge": "Directory PDF",
        "hub_page": "./intercom.html"
    },
    {
        "title": "Campus Intercom & Extension Directory (Searchable List)",
        "url": "./intercom.html",
        "category": "Staff Directory",
        "description": "Searchable internal departmental telephone extensions and casualty hotlines",
        "badge": "Directory",
        "hub_page": "./intercom.html"
    },
    {
        "title": "Emergency & Casualty Intercom Extensions (2001 / 2002 / 2800)",
        "url": "./intercom.html",
        "category": "Emergency Telephony",
        "description": "24/7 Casualty triage, emergency reception, priority room, HOD, and main gate extensions",
        "badge": "Hotline",
        "hub_page": "./intercom.html"
    },
    {
        "title": "Blood Bank 24/7 Intercom Extensions (2131 / 2132)",
        "url": "./intercom.html",
        "category": "Emergency Telephony",
        "description": "24/7 Blood bank issue counter, cross-matching and donor collection extensions",
        "badge": "Hotline",
        "hub_page": "./intercom.html"
    },
    {
        "title": "ICU & Critical Care Intercom Extensions (2156 / 2163 / 2160)",
        "url": "./intercom.html",
        "category": "Emergency Telephony",
        "description": "Intensive Care Unit HOD, Trauma ICU, and PACU direct internal lines",
        "badge": "Hotline",
        "hub_page": "./intercom.html"
    },
    {
        "title": "IT & HIS Help Desk Intercom Extensions (2226 / 2228)",
        "url": "./intercom.html",
        "category": "Staff Directory",
        "description": "Hospital Information System support, hardware, and network telephony desk",
        "badge": "Support",
        "hub_page": "./intercom.html"
    },
    {
        "title": "PruWorks HRMS (Staff Attendance, Leave & Payroll)",
        "url": "https://mapims-hrms.tecvinesolutions.com",
        "category": "HR Forms",
        "description": "Official PruWorks HRMS portal for staff biometric attendance, leave applications & balance, shift duty, and monthly payslips",
        "badge": "HRMS",
        "hub_page": "./hrforms.html"
    },
    {
        "title": "HRMS Staff Self-Service Login",
        "url": "http://www.mapims.online/staff",
        "category": "HR Forms",
        "description": "Employee self-service login for attendance regularisation, profile, and HR circulars",
        "badge": "Staff Portal",
        "hub_page": "./hrforms.html"
    },
    {
        "title": "HRMS Admin Management Portal",
        "url": "http://www.mapims.online/",
        "category": "HR Forms",
        "description": "Institutional Human Resources administration and staff records management",
        "badge": "Admin Portal",
        "hub_page": "./hrforms.html"
    },
    {
        "title": "APH HR Forms Hub",
        "url": "./index.html#forms",
        "category": "HR Forms",
        "description": "Central repository on the main portal for teaching faculty recruitment, non-teaching jobs, appraisals, PMS policy and leave schedule",
        "badge": "Forms Hub",
        "hub_page": "./index.html#forms"
    },
    {
        "title": "HVAC PM Schedule (Facility Management)",
        "url": "http://192.168.101.75:3000/files/PMSheduleHVACsystem2021.xlsx",
        "category": "Facility Management",
        "description": "Facility management preventative maintenance plan for OT & ICU HVAC",
        "badge": "Excel Spreadsheet",
        "hub_page": "./commonforms.html"
    }
]
for d in portal_docs:
    add_entry(d["title"], d["url"], d["category"], d["description"], d["badge"], d["hub_page"])

# 10. Scan HTML files for any remaining documents/cards
html_sources = [
    ('consent.html', 'Consent Forms', './consent.html'),
    ('commonforms.html', 'Common Forms', './commonforms.html'),
    ('hrforms.html', 'HR Forms', './hrforms.html'),
    ('itforms.html', 'IT Forms', './itforms.html'),
    ('manuals.html', 'Manuals & SOPs', './manuals.html'),
    ('comitee.html', 'Committees & MOM', './comitee.html'),
    ('recent circular.html', 'Circulars', './recent circular.html'),
    ('index.html', 'Portal Resources', './index.html')
]

for fname, default_cat, hub_page in html_sources:
    file_path = os.path.join(BASE_DIR, fname)
    if not os.path.exists(file_path):
        continue
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Regex to match card containers with h3/h4/h2 followed by an <a> tag
        card_matches = re.findall(r'<h[234][^>]*>(.*?)</h[234]>.*?<a[^>]*href=[\"\']([^\"\']+)[\"\']', html, re.DOTALL | re.IGNORECASE)
        for title, url in card_matches:
            if 'files/' in url or url.endswith('.pdf') or url.endswith('.xlsx'):
                add_entry(title, url, default_cat, f"{title} ({default_cat})", "Document", hub_page)
        
        # Regex for all <a> tags with text and href
        a_matches = re.findall(r'<a\s+[^>]*href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
        for url, text in a_matches:
            if 'files/' in url or url.endswith('.pdf') or url.endswith('.xlsx'):
                clean_text = ' '.join(re.sub(r'<[^>]+>', ' ', text).split())
                if clean_text and not clean_text.lower().startswith(('open pdf', 'view pdf', 'view', 'download', 'read')):
                    add_entry(clean_text, url, default_cat, f"{clean_text} ({default_cat})", "Document", hub_page)
    except Exception as e:
        print(f"Error scanning {fname}: {e}")

output_path = os.path.join(DATA_DIR, 'portal_catalog.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(catalog, f, indent=2, ensure_ascii=False)

print(f"✅ Successfully compiled {len(catalog)} verified resources into {output_path}")
