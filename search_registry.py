#!/usr/bin/env python3
"""
APH Portal AI Search Engine: Central Resource Registry & Intent Engine
Provides:
1. Canonical Resource Registry with stable IDs, verified URLs, categories, and bilingual labels.
2. Explicit Intent Classification (OPEN_APPLICATION, OPEN_FORM, FIND_DOCUMENT, ANSWER_FROM_MANUAL,
   FIND_COMMITTEE, FIND_DIRECTORY, NAVIGATE_SECTION, UNKNOWN).
3. Multilingual Normalization (English, Tamil Script, Tanglish phonetics, spelling variants).
4. Deterministic Priority Ranking (Intent > Resource Alias > Exact Title > Token Match > Stopword Suppression).
"""

import re
import urllib.parse
from enum import Enum

class SearchIntent(Enum):
    OPEN_APPLICATION = "OPEN_APPLICATION"
    OPEN_FORM = "OPEN_FORM"
    FIND_DOCUMENT = "FIND_DOCUMENT"
    ANSWER_FROM_MANUAL = "ANSWER_FROM_MANUAL"
    FIND_COMMITTEE = "FIND_COMMITTEE"
    FIND_DIRECTORY = "FIND_DIRECTORY"
    NAVIGATE_SECTION = "NAVIGATE_SECTION"
    UNKNOWN = "UNKNOWN"

# =========================================================================
# 1. CANONICAL RESOURCE REGISTRY
# =========================================================================
RESOURCE_REGISTRY = {
    # Core Clinical & Administrative Applications
    "APP_HIS": {
        "id": "APP_HIS",
        "title": "Hospital Information System (HIS Backbone Login)",
        "url": "http://192.168.103.37/BB15SE/Backbone/admin/login.aspx",
        "category": "Core Systems",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "AOSTA HIS clinical workstation for patient registration, doctor consultations, IP/OP billing, and ward management.",
        "description_ta": "மருத்துவமனை தகவல் அமைப்பு (HIS - Backbone / AOSTA) முதன்மை உள்நுழைவு தளம்.",
        "aliases": [
            "his", "aosta", "backbone", "his login", "his portal", "his software", "open his", "his open",
            "his system", "his workstation", "access his", "backbone login", "aosta his", "clinical workstation",
            "ஹெச்ஐஎஸ்", "ஹெச்ஐஎஸ் திற", "ஹெச் ஐ எஸ்", "ஹிஸ்", "ஹிஸ் லாகின்", "ஹிஸ் சாப்ட்வேர்"
        ],
        "negative_aliases": [
            "his form", "his forms", "user creation", "doctor id", "item creation", "id creation",
            "user create", "account create", "padivam", "படிவம்", "creation form"
        ]
    },
    "APP_HRMS": {
        "id": "APP_HRMS",
        "title": "PruWorks HRMS Portal",
        "url": "https://mapims-hrms.tecvinesolutions.com",
        "category": "HR & Payroll",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Official employee self-service portal to apply for leave, view biometric attendance, and download monthly salary pay slips.",
        "description_ta": "பணியாளர் வருகை பதிவு, சம்பள ரசீதுகள், மற்றும் விடுமுறை விண்ணப்பிக்க PruWorks HRMS போர்ட்டல்.",
        "aliases": [
            "hrms", "pruworks", "hrms portal", "hrms login", "open hrms", "pruworks hrms", "hrms staff",
            "apply leave", "leave apply", "leave balance", "payslip", "pay slip", "salary slip",
            "biometric punch", "attendance portal", "leavu", "vidumurai", "viduppu", "sambalam",
            "விடுமுறை", "விடுப்பு", "சம்பளம்", "சம்பள ரசீது", "வருகை"
        ],
        "negative_aliases": ["holiday calendar", "list of holidays", "holidays 2026"]
    },
    "APP_PACS": {
        "id": "APP_PACS",
        "title": "M - PACS (Medsynapse Radiology Viewer)",
        "url": "http://192.168.101.224/User_Login.asp",
        "category": "Core Systems",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Diagnostic radiology imaging workstation to view Digital X-Ray, CT Scan, MRI, and Ultrasound scans.",
        "description_ta": "கதிரியக்க பரிசோதனை படங்கள் (X-Ray, CT, MRI, Ultrasound) பார்க்க M - PACS (Medsynapse) தளம்.",
        "aliases": [
            "pacs", "medsynapse", "open pacs", "pacs login", "pacs viewer", "xray viewer", "scan viewer",
            "xray scan", "x-ray", "ct scan", "mri scan", "ultrasound viewer", "radiology viewer",
            "xray scan paakanum", "பாக்ஸ்", "எக்ஸ்ரே", "ஸ்கேன் பார்க்க"
        ],
        "negative_aliases": []
    },
    "APP_MRD": {
        "id": "APP_MRD",
        "title": "MRD Medical Records Portal",
        "url": "http://www.mapimsmrd.com/mapimsmrd/",
        "category": "Core Systems",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Hospital medical records department portal for digitized discharge summaries and historical clinical archives.",
        "description_ta": "மருத்துவ ஆவணக் காப்பகம் (MRD) மற்றும் டிஸ்சார்ஜ் சம்மரி போர்ட்டல்.",
        "aliases": [
            "mrd", "open mrd", "mrd portal", "mrd login", "medical records", "discharge summary",
            "discharge summary archive", "case sheet archive", "மருத்துவ ஆவண காப்பகம்"
        ],
        "negative_aliases": []
    },
    "APP_MHC": {
        "id": "APP_MHC",
        "title": "MAPIMS AI Health Assessment (Master Health Checkup / MHC)",
        "url": "https://mh.mapims.edu.in/",
        "category": "In-House Developed",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Master Health Checkup clinical assessment, risk stratification, and patient wellness portal.",
        "description_ta": "மாஸ்டர் ஹெல்த் செக்கப் (MHC) மற்றும் AI சுகாதார மதிப்பீட்டுத் தளம்.",
        "aliases": [
            "mhc", "open mhc", "master health", "master health checkup", "health checkup", "ai health",
            "ai health assessment", "healthcheck app", "மாஸ்டர் ஹெல்த் செக்கப்", "ஹெல்த் செக்கப்"
        ],
        "negative_aliases": []
    },
    "APP_LINELOOM": {
        "id": "APP_LINELOOM",
        "title": "LineLoom OPD Token Display System",
        "url": "http://192.168.103.158:8086",
        "category": "Core Systems",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Outpatient department live queue visualization and patient calling token screen.",
        "description_ta": "புறநோயாளி பிரிவு நேரலை டோக்கன் மற்றும் வரிசை காட்சி அமைப்பு (LineLoom).",
        "aliases": [
            "lineloom", "token display", "opd token", "token machine", "opd queue", "queue display",
            "token screen", "வரிசை டோக்கன்", "டோக்கன் டிஸ்பிளே"
        ],
        "negative_aliases": ["food token", "unavu token"]
    },
    "APP_TICKETING": {
        "id": "APP_TICKETING",
        "title": "Campus Ticketing & Maintenance Desk (Job Orders)",
        "url": "http://www.mapimshis.com/mapims/",
        "category": "Core Systems",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Institutional ticketing system to lodge IT, HIS, biomedical, civil, and electrical breakdown job orders.",
        "description_ta": "கணினி, இணையம், மற்றும் மருத்துவமனை பழுது புகார்களைப் பதிவு செய்ய Ticketing Desk.",
        "aliases": [
            "ticketing", "ticket", "ticketing desk", "lodge ticket", "it ticket", "maintenance desk",
            "job order", "job orders", "breakdown", "hardware repair", "complaint", "fault", "bug", "பழுது"
        ],
        "negative_aliases": [
            "resignation", "resign", "rajinama", "relieving", "notice period", "job application",
            "job form", "employment form", "faculty application"
        ]
    },
    "APP_BARCODE": {
        "id": "APP_BARCODE",
        "title": "Pathology Barcode Generator",
        "url": "http://192.168.103.158:8081",
        "category": "Diagnostic Tools",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Laboratory specimen barcode label generation system for diagnostic blood and pathology tubes.",
        "description_ta": "பரிசோதனை குழாய்களுக்கான பார்கோடு லேபிள் உருவாக்கும் தளம்.",
        "aliases": ["barcode", "barcode generator", "pathology barcode", "lab barcode", "sample barcode"],
        "negative_aliases": []
    },

    # Verified Forms (IT, HR, Clinical, Consent)
    "FORM_HIS_USER": {
        "id": "FORM_HIS_USER",
        "title": "New HIS User Request Form",
        "url": "http://192.168.101.75:3000/files/His%20User%20Creation.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Official requisition form to create a new HIS user profile and assign role-based hospital module access permissions.",
        "description_ta": "HIS புதிய பயனர் கணக்கு உருவாக்குவதற்கான அதிகாரப்பூர்வ விண்ணப்பப் படிவம்.",
        "aliases": [
            "his form", "his user form", "his user creation", "new his user", "his access form",
            "his credential", "his login form", "his account creation", "enaku his access venum",
            "his access venum", "his user request", "open his form", "his padivam",
            "ஹெச்ஐஎஸ் படிவம்", "ஹிஸ் பயனர் படிவம்", "ஹிஸ் புதிய பயனர்"
        ],
        "negative_aliases": ["open his", "his login", "his open", "login his", "his portal", "his software"]
    },
    "FORM_DOCTOR_ID": {
        "id": "FORM_DOCTOR_ID",
        "title": "New Doctor Name and ID Creation in HIS",
        "url": "http://192.168.101.75:3000/files/Doctor%20Name%20and%20ID%20Creation.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Form to register new doctor names, specialty designations, and clinical practitioner IDs in the HIS master database.",
        "description_ta": "HIS அமைப்பில் புதிய மருத்துவர் பெயர் மற்றும் பயனர் அடையாள எண் (Doctor ID) உருவாக்கும் படிவம்.",
        "aliases": [
            "doctor id", "doctor id creation", "doctor name creation", "doctor creation in his",
            "doctor id form", "maruthuvar id", "மருத்துவர் ஐடி", "மருத்துவர் பெயர்"
        ],
        "negative_aliases": []
    },
    "FORM_WIFI": {
        "id": "FORM_WIFI",
        "title": "Employee WIFI Request Form",
        "url": "http://192.168.101.75:3000/files/EMPLOYEE%20WIFI%20REQUEST%20FORM.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Application form to register authorized employee laptops and mobile devices for hospital Wi-Fi and network access.",
        "description_ta": "மருத்துவமனை வளாக வைஃபை (Wi-Fi) மற்றும் இணைய அனுமதி கோரும் படிவம்.",
        "aliases": [
            "wifi form", "wifi request", "employee wifi", "wifi request form", "wi-fi form",
            "internet request", "internet connection request", "wifi access", "wifi venum",
            "wireless request", "வைஃபை படிவம்", "இணைய கோரிக்கை"
        ],
        "negative_aliases": []
    },
    "FORM_SYSTEM": {
        "id": "FORM_SYSTEM",
        "title": "System Request Form",
        "url": "http://192.168.101.75:3000/files/SYSTEM%20REQUEST%20FORM.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Official requisition for new desktop computers, monitors, accessories, or software installations.",
        "description_ta": "புதிய கணினி, மவுஸ், கீபோர்டு, அல்லது மென்பொருள் கோரிக்கை படிவம்.",
        "aliases": [
            "system request", "system request form", "computer request", "desktop request", "kanini request",
            "கணினி கோரிக்கை", "கணினி படிவம்", "புதிய கணினி படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_PRINTER": {
        "id": "FORM_PRINTER",
        "title": "Printer Request Form",
        "url": "http://192.168.101.75:3000/files/PRINTER%20REQUEST%20FORM.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Form to request departmental printing hardware, barcode label printers, or toner replacements.",
        "description_ta": "துறை பயன்பாட்டிற்கான புதிய பிரிண்டர் அல்லது டோனர் கோரிக்கை படிவம்.",
        "aliases": [
            "printer request", "printer form", "printer request form", "toner request",
            "acchaagam padivam", "பிரிண்டர் படிவம்", "அச்சக படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_EMAIL_ID": {
        "id": "FORM_EMAIL_ID",
        "title": "Official Email ID Request Form",
        "url": "http://192.168.101.75:3000/files/OFFICIAL%20EMAIL%20ID%20REQUEST%20FORM.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Form to request an official institutional @mapims.edu.in email account.",
        "description_ta": "அதிகாரப்பூர்வ நிறுவன மின்னஞ்சல் முகவரி (Email ID) கோரும் படிவம்.",
        "aliases": ["email form", "email id request", "official email form", "mail id form", "மின்னஞ்சல் படிவம்"],
        "negative_aliases": []
    },
    "FORM_SIM_CUG": {
        "id": "FORM_SIM_CUG",
        "title": "SIM CUG Request Form",
        "url": "http://192.168.101.75:3000/files/SIM%20CUG%20REQUEST%20FORM.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Requisition for hospital closed user group (CUG) SIM cards and authorized mobile connections.",
        "description_ta": "மருத்துவமனை சிம் கார்டு (CUG SIM) கோரிக்கை படிவம்.",
        "aliases": ["cug form", "sim form", "sim cug", "cug sim request", "சிம் படிவம்"],
        "negative_aliases": []
    },
    "FORM_RESIGNATION_HRM": {
        "id": "FORM_RESIGNATION_HRM",
        "title": "Human Resources Manual (HRM - 2025)",
        "url": "http://192.168.101.75:3000/files/HRM%202025.pdf",
        "category": "HR Forms",
        "badge": "HR Manual",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Employee resignation procedure, notice period guidelines, departmental handovers, exit clearance, and relieving order protocols.",
        "description_ta": "பணியாளர் பணி விலகல் நடைமுறைகள் (Resignation), நோட்டீஸ் காலம், மற்றும் என்ஓசி (No Dues) விதிமுறைகள் கையேடு.",
        "aliases": [
            "resignation procedure", "resignation", "resign", "relieving", "relieving procedure",
            "exit clearance", "notice period", "no dues", "nodues", "resignation letter",
            "rajinama", "rajinama form", "raajinaama", "பணி விலகல்", "பணி விலகல் படிவம்",
            "ராஜினாமா", "ராஜினாமா படிவம்", "procedure resignation job form"
        ],
        "negative_aliases": ["ticketing", "maintenance desk", "job order", "antibiotics"]
    },
    "FORM_NON_TEACHING": {
        "id": "FORM_NON_TEACHING",
        "title": "Non-Teaching Staff Application Form",
        "url": "http://192.168.101.75:3000/files/Non%20Teaching.pdf",
        "category": "HR Forms",
        "badge": "HR Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Official employment application form for administrative, technical, nursing, and support staff vacancies.",
        "description_ta": "ஆசிரியரல்லாத பணியாளர் வேலை விண்ணப்பப் படிவம்.",
        "aliases": [
            "non teaching", "non-teaching form", "staff application", "job form", "job application",
            "velai vinnappam", "வேலை விண்ணப்பம்", "பணியாளர் வேலை விண்ணப்பம்"
        ],
        "negative_aliases": ["ticketing", "job orders"]
    },
    "FORM_TEACHING": {
        "id": "FORM_TEACHING",
        "title": "Teaching Faculty Application & Appraisal Form",
        "url": "http://192.168.101.75:3000/files/Teaching.pdf",
        "category": "HR Forms",
        "badge": "HR Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Application, promotion, and appraisal form for medical college teaching faculty and clinical professors.",
        "description_ta": "மருத்துவக் கல்லூரி ஆசிரியர் மற்றும் பேராசிரியர் பணிக்கான விண்ணப்பப் படிவம்.",
        "aliases": [
            "teaching faculty", "teaching application", "faculty application", "professor application",
            "teaching job", "பேராசிரியர் விண்ணப்பம்"
        ],
        "negative_aliases": ["ticketing", "job orders"]
    },

    # Verified Clinical Governance & Committee Directory
    "DIR_COMMITTEES": {
        "id": "DIR_COMMITTEES",
        "title": "APH Hospital Committees & MOM Directory",
        "url": "./comitee.html",
        "category": "Committees & MOM",
        "badge": "Governance Hub",
        "intent_type": SearchIntent.FIND_COMMITTEE,
        "description": "Central registry of hospital governance charters, quality committees, HICC, safety committees, and Minutes of Meeting (MOM).",
        "description_ta": "மருத்துவமனை நிர்வாக குழுக்கள், தரக் கட்டுப்பாடு குழு (Quality Committee), மற்றும் கூட்ட அறிக்கைகள் (MOM) தளம்.",
        "aliases": [
            "committee", "committees", "committee list", "hospital committees", "quality committee",
            "quality committee members", "committee members", "committee charter", "committee charters",
            "mom", "minutes of meeting", "hicc committee", "safety committee", "மருத்துவமனை குழுக்கள்", "குழு"
        ],
        "negative_aliases": []
    },
    "DOC_HICC_CHARTER": {
        "id": "DOC_HICC_CHARTER",
        "title": "Hospital Infection Control Committee (NABH 5th Edition)",
        "url": "http://192.168.101.75:3000/files/Qc/HOSPITAL%20INFECTION%20CONTROL%20COMMITTEE.pdf",
        "category": "Committees & MOM",
        "badge": "Committee Charter",
        "intent_type": SearchIntent.FIND_COMMITTEE,
        "description": "Official constitution, TOR, and multidisciplinary charter of the Hospital Infection Control Committee (HICC).",
        "description_ta": "தொற்று கட்டுப்பாட்டுக் குழுவின் (HICC) அதிகாரப்பூர்வ சாசனம் மற்றும் விதிமுறைகள்.",
        "aliases": [
            "infection control committee", "hicc charter", "hicc committee", "infection committee",
            "தொற்று கட்டுப்பாட்டு குழு"
        ],
        "negative_aliases": []
    },
    "DOC_ICU_INFECTION_MANUAL": {
        "id": "DOC_ICU_INFECTION_MANUAL",
        "title": "Guideline for Infection Control Practices ICU",
        "url": "http://192.168.101.75:3000/files/Guideline%20for%20Infection%20Control%20Practices%20ICU.pdf",
        "category": "Manuals & SOPs",
        "badge": "Clinical Manual",
        "intent_type": SearchIntent.ANSWER_FROM_MANUAL,
        "description": "ICU infection surveillance protocols, ventilator bundle guidelines, catheter-associated UTI prevention, and hand hygiene standards.",
        "description_ta": "தீவிர சிகிச்சை பிரிவு (ICU) தொற்று தடுப்பு வழிகாட்டுதல் கையேடு.",
        "aliases": [
            "infection control manual", "icu infection control", "infection control guideline",
            "infection practices", "தொற்று கட்டுப்பாட்டு கையேடு"
        ],
        "negative_aliases": []
    },

    # Telephony Directories
    "DIR_INTERCOM_OFFICIAL": {
        "id": "DIR_INTERCOM_OFFICIAL",
        "title": "Official Campus Intercom & Extension Directory",
        "url": "http://192.168.101.75/assets/sub%20files/intercom.html",
        "category": "Staff Directory",
        "badge": "Full Directory",
        "intent_type": SearchIntent.FIND_DIRECTORY,
        "description": "Full official printable campus telephone directory across all hospital, medical college, and administrative departments.",
        "description_ta": "மருத்துவமனை வளாக முழுமையான தொலைபேசி மற்றும் இன்டர்காம் இணைப்பு பட்டியல்.",
        "aliases": [
            "intercom", "inercom", "telephone", "phone directory", "campus directory", "extension directory",
            "tholaipesi", "தொலைபேசி", "இன்டர்காம்", "இணைப்பு பட்டியல்"
        ],
        "negative_aliases": []
    },
    "DIR_INTERCOM_SEARCH": {
        "id": "DIR_INTERCOM_SEARCH",
        "title": "Campus Intercom & Extension Directory (Searchable List)",
        "url": "./intercom.html",
        "category": "Staff Directory",
        "badge": "Directory",
        "intent_type": SearchIntent.FIND_DIRECTORY,
        "description": "Interactive searchable department intercom directory with one-click print and floor filter.",
        "description_ta": "துறைவாரியாக தேடக்கூடிய நேரலை இன்டர்காம் இணைப்பு பட்டியல்.",
        "aliases": ["interactive intercom", "search intercom", "intercom list"],
        "negative_aliases": []
    }
}

# Generic Tokens that must never dominate scoring
GENERIC_STOP_WORDS = {
    'form', 'forms', 'from', 'padivam', 'படிவம்',
    'manual', 'manuals', 'sop', 'sops', 'guideline', 'guidelines',
    'procedure', 'procedures', 'policy', 'policies', 'protocol', 'protocols',
    'request', 'application', 'vinnappam', 'விண்ணப்பம்',
    'details', 'detail', 'portal', 'hub', 'sheet', 'file', 'files', 'list', 'lists',
    'document', 'documents', 'view', 'download', 'department', 'hospital', 'aph', 'mapims',
    'please', 'show', 'give', 'about', 'the', 'is', 'in', 'of', 'and', 'for', 'to', 'with',
    'what', 'which', 'where', 'when', 'who', 'how', 'why', 'available', 'availability',
    'are', 'can', 'get', 'need', 'want', 'tell', 'me', 'i', 'a', 'an', 'any', 'all', 'there',
    'have', 'has', 'do', 'does', 'find', 'some', 'know', 'open', 'enga', 'yenga', 'trla',
    'therila', 'theriyala', 'venum', 'vendum', 'iruku', 'eruku'
}

# Multilingual Synonym and Normalization Map
MULTILINGUAL_SYNONYMS = {
    # HIS Transliteration & Actions
    "ஹெச்ஐஎஸ்": "his aosta backbone",
    "ஹெச் ஐ எஸ்": "his aosta backbone",
    "ஹிஸ்": "his aosta backbone",
    "திற": "open launch login portal",
    "திறக்கவும்": "open launch login portal",
    "thira": "open launch login portal",
    "உள்நுழைவு": "login workstation portal",

    # Resignation & HR
    "rajinama": "resignation resign relieving exit clearance",
    "raajinaama": "resignation resign relieving exit clearance",
    "ராஜினாமா": "resignation resign relieving exit clearance",
    "பணி விலகல்": "resignation relieving notice period",
    "pathavi vilagal": "resignation relieving",
    "velai viduthal": "resignation relieving",
    "sambalam": "salary payslip payroll wages",
    "சம்பளம்": "salary payslip payroll wages",
    "vidumurai": "leave vacation permission",
    "viduppu": "leave vacation permission",
    "விடுமுறை": "leave vacation permission",
    "விடுப்பு": "leave vacation permission",

    # Network & Hardware
    "internet connection": "wifi employee wireless request form",
    "internet connection request": "wifi employee wireless request form",
    "wifi venum": "wifi employee wireless request form",
    "kanini": "system computer workstation desktop",
    "கணினி": "system computer workstation desktop",
    "கணினி கோரிக்கை": "system request form",
    "acchaagam": "printer toner printing",
    "அச்சகம்": "printer toner printing",

    # Committees & Governance
    "quality committee members": "quality committee members governance charters",
    "குழு": "committee charter mom governance",
    "charter": "committee charter mom governance",

    # Telephony
    "tholaipesi": "intercom telephone phone extension call",
    "தொலைபேசி": "intercom telephone phone extension call",
    "இன்டர்காம்": "intercom telephone phone extension call",
    "இணைப்பு": "extension intercom call phone"
}

# =========================================================================
# 2. INTENT CLASSIFIER & QUERY NORMALIZER
# =========================================================================
def clean_and_tokenize(text):
    if not text:
        return set()
    cleaned = re.sub(r'[^\w\s\u0B80-\u0BFF]', ' ', text.lower())
    return set(cleaned.split())

def expand_query_tokens(tokens, raw_text=""):
    expanded = set(tokens)
    raw_lower = raw_text.lower().strip() if raw_text else " ".join(tokens)

    # Multi-word phrase expansion
    for phrase, mapped in MULTILINGUAL_SYNONYMS.items():
        if " " in phrase and phrase in raw_lower:
            expanded.update(mapped.split())

    # Token-level expansion
    for t in tokens:
        if t in MULTILINGUAL_SYNONYMS:
            expanded.update(MULTILINGUAL_SYNONYMS[t].split())

    return expanded

def classify_search_intent(query):
    """
    Deterministically classifies query intent into explicit categories:
    OPEN_APPLICATION, OPEN_FORM, FIND_DOCUMENT, ANSWER_FROM_MANUAL,
    FIND_COMMITTEE, FIND_DIRECTORY, NAVIGATE_SECTION, UNKNOWN.
    """
    q_lower = query.lower().strip()
    tokens = clean_and_tokenize(q_lower)

    # 1. Committee Search
    if any(k in q_lower for k in [
        "committee", "committees", "charter", "charters", "mom", "minutes of meeting",
        "governance", "குழு", "கூட்ட அறிக்கை", "meeting minutes"
    ]):
        return SearchIntent.FIND_COMMITTEE

    # 2. Telephony / Intercom Directory
    if any(k in q_lower for k in [
        "intercom", "inercom", "extension", "ext", "exts", "phone", "telephone",
        "call", "calling", "dial", "hotline", "tholaipesi", "தொலைபேசி", "இன்டர்காம்",
        "எக்ஸ்டென்ஷன்", "இணைப்பு"
    ]):
        return SearchIntent.FIND_DIRECTORY

    # 3. Resignation / Relieving Intent
    if any(k in q_lower for k in [
        "resignation", "resign", "relieving", "notice period", "exit clearance",
        "no dues", "nodues", "rajinama", "raajinaama", "பணி விலகல்", "ராஜினாமா"
    ]):
        return SearchIntent.FIND_DOCUMENT

    # 4. Form Requisition Intent (Explicit request for PDF / form to fill)
    is_form_word = bool(tokens & {"form", "forms", "padivam", "படிவம்", "vinnappam", "விண்ணப்பம்", "requisition"})
    is_creation_intent = any(k in q_lower for k in [
        "user creation", "doctor id", "item creation", "id creation", "account creation",
        "access venum", "access vendum", "creation in his"
    ])
    if (is_form_word or is_creation_intent) and not any(k in q_lower for k in ["open pacs", "open mrd", "open hrms"]):
        # Check if user specifically requested an app vs form
        if q_lower in ["open his form", "his form", "wifi form", "printer request form", "system request form"] or is_creation_intent:
            return SearchIntent.OPEN_FORM

    # 5. Core Application Launch Intent
    # e.g., "open his", "his login enga", "ஹெச்ஐஎஸ் திற", "open hrms", "open pacs", "open mrd"
    is_app_keyword = any(k in q_lower for k in [
        "his", "aosta", "backbone", "hrms", "pruworks", "pacs", "medsynapse",
        "mrd", "mhc", "master health", "lineloom", "barcode", "counselling",
        "ஹெச்ஐஎஸ்", "ஹிஸ்"
    ])
    is_launch_action = any(k in q_lower for k in [
        "open", "launch", "login", "portal", "workstation", "viewer", "software",
        "app", "enga", "yenga", "thira", "திற", "திறக்கவும்", "உள்நுழைவு", "லாகின்",
        "paakanum", "பார்க்க"
    ]) or "apply leave" in q_lower or "leave apply" in q_lower

    if is_app_keyword and (is_launch_action or q_lower in ["his", "hrms", "pacs", "mrd", "mhc", "lineloom"]):
        if not is_form_word and not is_creation_intent:
            return SearchIntent.OPEN_APPLICATION

    # 6. Clinical Manual / SOP / Guideline Search
    if any(k in q_lower for k in [
        "manual", "sop", "sops", "guideline", "guidelines", "protocol", "policy", "policies",
        "infection control", "nabh", "hand hygiene", "sterilization", "sbar"
    ]):
        return SearchIntent.ANSWER_FROM_MANUAL

    return SearchIntent.UNKNOWN

# =========================================================================
# 3. RESOURCE RESOLVER & RANKING ENGINE
# =========================================================================
def resolve_exact_registered_resource(query, intent):
    """
    Resolves explicit, unambiguous registered hospital resources.
    Returns matched resource dict or None.
    """
    q_lower = query.lower().strip()
    tokens = clean_and_tokenize(q_lower)

    # 1. HIS Application vs HIS Form Disambiguation
    if (
        "his" in tokens or "aosta" in q_lower or "backbone" in q_lower or
        "ஹெச்ஐஎஸ்" in tokens or "ஹிஸ்" in tokens or "ஹெச்ஐஎஸ் திற" in q_lower
    ):
        # Explicit Form Requisition
        if any(k in q_lower for k in [
            "his form", "his forms", "user creation", "his user", "new his user",
            "access venum", "access vendum", "his account", "open his form",
            "padivam", "படிவம்", "creation form"
        ]) or (intent == SearchIntent.OPEN_FORM and "doctor" not in q_lower and "item" not in q_lower):
            return RESOURCE_REGISTRY["FORM_HIS_USER"]

        # Explicit Doctor ID Form
        if any(k in q_lower for k in ["doctor id", "doctor name", "maruthuvar id", "மருத்துவர்"]):
            return RESOURCE_REGISTRY["FORM_DOCTOR_ID"]

        # Explicit Application Launch
        if intent == SearchIntent.OPEN_APPLICATION or any(k in q_lower for k in [
            "open his", "his open", "login", "workstation", "portal", "software",
            "enga", "திற", "திறக்கவும்", "ஹெச்ஐஎஸ் திற"
        ]):
            return RESOURCE_REGISTRY["APP_HIS"]

    # 2. HRMS Portal vs Leave
    if "hrms" in tokens or "pruworks" in q_lower or any(k in q_lower for k in ["open hrms", "hrms portal", "hrms login"]):
        return RESOURCE_REGISTRY["APP_HRMS"]

    if any(k in q_lower for k in ["apply leave", "leave apply", "vidumurai", "viduppu", "leavu", "விடுமுறை"]) and not any(k in q_lower for k in ["calendar", "holiday"]):
        return RESOURCE_REGISTRY["APP_HRMS"]

    # 3. Resignation & Job Forms
    if any(k in q_lower for k in [
        "resignation", "resign", "relieving", "notice period", "exit clearance",
        "rajinama", "raajinaama", "பணி விலகல்", "ராஜினாமா", "procedure resignation job form"
    ]):
        return RESOURCE_REGISTRY["FORM_RESIGNATION_HRM"]

    # 4. Wi-Fi Form
    if any(k in q_lower for k in ["wifi form", "wi-fi form", "internet connection request", "wifi request", "wifi venum", "வைஃபை"]):
        return RESOURCE_REGISTRY["FORM_WIFI"]

    # 5. System & Printer Request Forms
    if any(k in q_lower for k in ["system request", "kanini", "கணினி கோரிக்கை", "கணினி படிவம்"]):
        return RESOURCE_REGISTRY["FORM_SYSTEM"]

    if any(k in q_lower for k in ["printer request", "printer form", "acchaagam", "அச்சக படிவம்"]):
        return RESOURCE_REGISTRY["FORM_PRINTER"]

    # 6. Core Clinical Apps
    if "pacs" in tokens or "medsynapse" in q_lower or "xray scan paakanum" in q_lower:
        return RESOURCE_REGISTRY["APP_PACS"]

    if "mrd" in tokens or "discharge summary archive" in q_lower:
        return RESOURCE_REGISTRY["APP_MRD"]

    if "mhc" in tokens or any(k in q_lower for k in ["master health", "மாஸ்டர் ஹெல்த் செக்கப்"]):
        return RESOURCE_REGISTRY["APP_MHC"]

    if "lineloom" in tokens or "opd token" in q_lower or "opd queue display" in q_lower:
        return RESOURCE_REGISTRY["APP_LINELOOM"]

    # 7. Committee Searches
    if intent == SearchIntent.FIND_COMMITTEE:
        if "infection control" in q_lower or "hicc" in q_lower:
            return RESOURCE_REGISTRY["DOC_HICC_CHARTER"]
        return RESOURCE_REGISTRY["DIR_COMMITTEES"]

    return None
