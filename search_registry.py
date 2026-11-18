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
import difflib
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
        "description": "AOSTA HIS clinical workstation exclusively for patient details, IP/OP/ER registration (new & review), billing, indents/stores, pharmacy dispensing, and hospital operations.",
        "description_ta": "மருத்துவமனை தகவல் அமைப்பு (HIS - Backbone / AOSTA) நோயாளி விவரங்கள், பதிவு (OP/IP/ER), பில்லிங், மருந்தகம் மற்றும் இண்டென்ட்ஸ் உள்நுழைவு தளம்.",
        "aliases": [
            "his", "aosta", "backbone", "his login", "his portal", "his software", "open his", "his open",
            "his system", "his workstation", "access his", "backbone login", "aosta his", "clinical workstation",
            "his app", "his application", "his website", "his tool", "aosta app",
            "patient details", "patient detail", "patient info", "patient record", "patient search",
            "reg io", "reg op", "reg ip", "reg er", "op registration", "ip registration", "er registration",
            "new registration", "new patient", "review patient", "patient review", "ip admission", "patient discharge",
            "billing", "billinh", "op billing", "ip billing", "discharge billing", "patient billing", "billing login",
            "indents stores", "indents", "stores", "ward indents", "store indent", "material issue", "drug indent",
            "pharmacy in his", "his pharmacy", "pharmacy dispensing", "pharmacy login", "pharmacy billing",
            "front office", "front desk", "front office his", "his front office", "open front office", "front office login",
            "his op", "his ip", "his ward", "his discharge", "his discharge summary", "discharge summary his",
            "ward his", "op his", "ip his", "ward login", "ward management", "inpatient ward", "ip ward", "op ward",
            "op login", "ip login", "opd login", "ipd login",
            "staff user creation",
            "ஹெச்ஐஎஸ்", "ஹெச்ஐஎஸ் திற", "ஹெச் ஐ எஸ்", "ஹிஸ்", "ஹிஸ் லாகின்", "ஹிஸ் சாப்ட்வேர்", "நோயாளி விவரம்"
        ],
        "negative_aliases": [
            "his form", "his forms", "doctor id", "item creation", "id creation",
            "padivam", "படிவம்", "creation form",
            "repair", "fixing", "maintenance", "electrical", "housekeeping", "laundry", "breakdown", "job order"
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
            "hrms app", "hrms application", "hrms software", "hrms website", "pruworks app", "pruworks application", "pruworks software",
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
            "pacs app", "pacs application", "pacs software", "pacs website", "medsynapse app", "medsynapse application", "medsynapse software",
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
            "mrd app", "mrd application", "mrd software", "mrd website",
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
            "mhc app", "mhc application", "mhc software", "mhc website", "master health app", "master health checkup app", "ai health app",
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
            "lineloom app", "lineloom application", "lineloom software", "token app", "opd token app",
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
        "description": "Institutional ticketing system to lodge repairs, fixing anything, maintenance, electrical, housekeeping, laundry, IT and facility job orders.",
        "description_ta": "கணினி, மின்சாரம், பராமரிப்பு, துப்புரவு (Housekeeping), சலவை (Laundry) மற்றும் மருத்துவமனை பழுது புகார்களைப் பதிவு செய்ய Ticketing Desk.",
        "aliases": [
            "ticketing", "ticket", "ticketing desk", "lodge ticket", "it ticket", "maintenance desk",
            "ticketing app", "ticketing application", "ticketing software", "ticket app", "maintenance app",
            "repair", "fixing anything", "fixing", "fix", "maintenance",
            "electrical", "electrical maintenance", "electrical repair", "electrical fault", "electrical complaint", "electrical work",
            "housekeeping", "housekeeping complaint", "housekeeping maintenance", "housekeeping request", "cleaning complaint",
            "laundry", "laundry complaint", "laundry maintenance", "laundry request", "laundry issue", "laundry service",
            "job order", "job orders", "breakdown", "hardware repair", "complaint", "fault", "bug", "பழுது"
        ],
        "negative_aliases": [
            "resignation", "resign", "rajinama", "relieving", "notice period", "job application",
            "job form", "employment form", "faculty application",
            "sop", "manual", "policy", "guideline", "protocol", "கையேடு", "விதிமுறை",
            "patient details", "patient registration", "op billing", "ip billing", "discharge billing", "indents", "stores"
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
        "aliases": [
            "barcode", "barcode generator", "pathology barcode", "lab barcode", "sample barcode",
            "barcode app", "barcode application", "barcode software", "barcode tool", "pathology barcode app"
        ],
        "negative_aliases": []
    },
    "APP_EYECAMP": {
        "id": "APP_EYECAMP",
        "title": "Community Health Eye Camp-25 Outreach",
        "url": "http://192.168.103.158:8082",
        "category": "Community Health",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Ophthalmology community outreach, camp registration and patient screening.",
        "description_ta": "கண் மருத்துவ முகாம் பதிவு மற்றும் நோயாளி பரிசோதனை தளம்.",
        "aliases": [
            "eye camp", "eye camp 25", "eyecamp", "ophthalmology camp", "community eye camp", "eye screening",
            "eye camp app", "eye camp application", "eye camp software", "eyecamp app", "கண் முகாம்"
        ],
        "negative_aliases": []
    },
    "APP_COUNSELLING": {
        "id": "APP_COUNSELLING",
        "title": "Clinical Care Counselling & ICU App",
        "url": "https://192.168.103.158:8083",
        "category": "Clinical Care",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Critical care counselling notes, psychological consults and encrypted ICU log storage.",
        "description_ta": "தீவிர சிகிச்சை ஆலோசனை மற்றும் உளவியல் ஆலோசனை குறிப்புகள் தளம்.",
        "aliases": [
            "counselling app", "counselling application", "counselling software", "icu app", "icu application",
            "icu software", "counselling & icu", "counselling and icu", "patient counselling", "icu counselling"
        ],
        "negative_aliases": []
    },
    "APP_CLINICAL_CHECKLIST": {
        "id": "APP_CLINICAL_CHECKLIST",
        "title": "Clinical Checklist App",
        "url": "https://checklist.mapims.edu.in/",
        "category": "Quality & NABH",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Daily nursing checklists, patient safety rounds, and paperless clinical audit workflows.",
        "description_ta": "தினசரி நர்சிங் சரிபார்ப்பு பட்டியல் மற்றும் நோயாளி பாதுகாப்பு தணிக்கை தளம்.",
        "aliases": [
            "clinical checklist", "clinical checklist app", "clinical checklist application", "clinical checklist software",
            "checklist app", "checklist application", "checklist software", "patient safety rounds", "surgery checklist",
            "clinical audit app", "audit app"
        ],
        "negative_aliases": ["non clinical", "gencl"]
    },
    "APP_NON_CLINICAL_CHECKLIST": {
        "id": "APP_NON_CLINICAL_CHECKLIST",
        "title": "Non-Clinical Checklist App",
        "url": "https://gencl.mapims.edu.in/",
        "category": "Quality & NABH",
        "badge": "System",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Hospital sanitation, housekeeping, engineering, and general facilities audit checklist.",
        "description_ta": "மருத்துவமனை சுகாதாரம் மற்றும் பராமரிப்பு வசதிகள் சரிபார்ப்பு பட்டியல் தளம்.",
        "aliases": [
            "non clinical checklist", "non clinical checklist app", "non clinical checklist application", "non clinical checklist software",
            "non-clinical checklist", "non-clinical checklist app", "gencl", "gencl app", "general checklist app", "facility checklist app"
        ],
        "negative_aliases": []
    },

    # Verified Forms (IT, HR, Clinical, Consent)
    "SECTION_IT_FORMS": {
        "id": "SECTION_IT_FORMS",
        "title": "IT Forms Hub",
        "url": "./itforms.html",
        "category": "Forms Vault",
        "badge": "Hardware & Access",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Central repository of hospital IT forms: New HIS User, Doctor ID Creation, Item Creation, WiFi, System Requisition, Printer, CUG, and Official Email.",
        "description_ta": "மருத்துவமனை தகவல் தொழில்நுட்ப (IT) படிவங்கள் தளம்: புதிய HIS பயனர், மருத்துவர் ஐடி உருவாக்கம், வைஃபை, கணினி கோரிக்கை, பிரிண்டர், CUG மற்றும் மின்னஞ்சல் படிவங்கள்.",
        "aliases": [
            "it forms", "it form", "information technology forms", "it forms hub", "it vault",
            "hardware and access forms", "ஐடி படிவங்கள்", "தகவல் தொழில்நுட்ப படிவங்கள்",
            "it padivangal", "it padivam", "all it forms", "list of it forms"
        ],
        "negative_aliases": []
    },
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
            "system request", "system request form", "system requisition", "system requisition form",
            "computer request", "desktop request", "kanini request",
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
            "printer request", "printer form", "printer request form", "printer repair", "printer repair request",
            "toner request", "acchaagam padivam", "பிரிண்டர் படிவம்", "அச்சக படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_VISITING_CONSULTANT": {
        "id": "FORM_VISITING_CONSULTANT",
        "title": "Visiting Consultant Requisition Form",
        "url": "http://192.168.101.75:3000/files/Visiting%20Consultant%20Requisition%20letter.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Specialist consultation requisition protocol and requisition letter.",
        "description_ta": "சிறப்பு மருத்துவர் ஆலோசனை மற்றும் வருகைக்கான கோரிக்கை கடிதம்.",
        "aliases": [
            "visiting consultant", "visiting consultant requisition", "visiting consultant form", "visiting consultant letter",
            "consultant requisition form", "visiting doctor form", "visiting doctor requisition",
            "visiting specialist requisition", "வெளி மருத்துவர் வருகை படிவம்", "சிறப்பு மருத்துவர் வருகை கடிதம்"
        ],
        "negative_aliases": []
    },
    "FORM_CONSENT_SURGERY_EN": {
        "id": "FORM_CONSENT_SURGERY_EN",
        "title": "Informed Consent Form For Surgery or Procedures -English",
        "url": "http://192.168.101.75:3000/files/INFORMED%20CONSENT%20FORM%20FOR%20SURGERY%20OR%20PROCEDURES%20-English.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Standard operative, invasive surgical, anaesthetic, and clinical procedure informed consent form (English).",
        "description_ta": "அறுவை சிகிச்சை மற்றும் மருத்துவ நடைமுறைகளுக்கான ஆங்கில தகவலறிந்த ஒப்புதல் படிவம்.",
        "aliases": [
            "informed consent form for surgery english", "surgery consent english", "surgical consent english",
            "surgery consent", "surgical consent", "operation consent", "operative consent", "procedure consent",
            "surgery consent form", "surgical consent form", "operation form", "anaesthesia consent", "ot consent",
            "informed consent for surgery", "consent for surgery", "consent for procedures", "consent for operation",
            "sergery consent", "sergery concent", "suregry consent", "surgry concent", "surgical concent",
            "operation concent", "ot concent", "concent for surgery", "concent for operation"
        ],
        "negative_aliases": ["tamil", "தமிழ்", "aruvai", "sikitsai"]
    },
    "FORM_CONSENT_SURGERY_TA": {
        "id": "FORM_CONSENT_SURGERY_TA",
        "title": "Informed Consent Form For Surgery or Procedures-Tamil",
        "url": "http://192.168.101.75:3000/files/INFORMED%20CONSENT%20FORM%20FOR%20SURGERY%20OR%20PROCEDURES-Tamil.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Standard operative, invasive surgical, and procedural informed consent form in Tamil script.",
        "description_ta": "அறுவை சிகிச்சை மற்றும் மருத்துவ நடைமுறைகளுக்கான அதிகாரப்பூர்வ தமிழ் தகவலறிந்த ஒப்புதல் படிவம்.",
        "aliases": [
            "surgery consent tamil", "tamil surgery consent", "surgical consent tamil", "operation consent tamil",
            "aruvai sigichai sammatha padivam", "aruvai sikitsai oputhal padivam", "aruvai sigichai sammatham",
            "aruvai sikitsai sammatham", "aruvai sigichai opputhal", "aruvai opputhal", "aruvai sammatham",
            "aruvai padivam", "aruvaisikitsai sammatham", "aruvaisigichai opputhal",
            "அறுவை சிகிச்சை ஒப்புதல் படிவம்", "அறுவை சிகிச்சை சம்மத படிவம்", "அறுவை சிகிச்சை படிவம்",
            "அறுவை ஒப்புதல் படிவம்", "அறுவை சம்மதம்", "தமிழ் ஒப்புதல் படிவம்"
        ],
        "negative_aliases": ["english"]
    },
    "FORM_CONSENT_PAEDIATRIC": {
        "id": "FORM_CONSENT_PAEDIATRIC",
        "title": "Paediatric Consent Form",
        "url": "http://192.168.101.75:3000/files/paedconsent.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Informed legal guardian authorization for neonatal, infant, and child medical and surgical care.",
        "description_ta": "குழந்தைகளுக்கான மருத்துவ மற்றும் அறுவை சிகிச்சைக்கான பெற்றோர்/பாதுகாவலர் ஒப்புதல் படிவம்.",
        "aliases": [
            "paediatric consent form", "pediatric consent form", "pediatric consent", "paediatric consent",
            "child consent form", "children consent", "infant consent", "newborn consent", "neonatal consent",
            "pediatric surgery consent", "paediatric surgery consent",
            "kuzhanthai consent form", "kuzhanthai consent", "kulandhai consent", "kulandhai sammatha padivam",
            "kuzhanthai sammatham", "pillai consent form", "chinna pasanga consent",
            "குழந்தை ஒப்புதல் படிவம்", "குழந்தைகள் ஒப்புதல் படிவம்", "குழந்தை சம்மத படிவம்", "குழந்தைகள் சம்மதம்",
            "pedatric concent", "pedatric consent", "paedatric consent", "paditric consent", "peadiatric concent"
        ],
        "negative_aliases": []
    },
    "FORM_CONSENT_BLOOD": {
        "id": "FORM_CONSENT_BLOOD",
        "title": "CONSENT FOR BLOOD COMPONENT TRANSFUSIONS",
        "url": "http://192.168.101.75:3000/files/Blood%20Transfusion%20Reaction%20Form%20version%202.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Informed authorization protocol and reaction tracking for whole blood, PRBC, FFP, and platelet component transfusions.",
        "description_ta": "ரத்தம் மற்றும் ரத்த கூறுகள் ஏற்றுவதற்கான நோயாளி ஒப்புதல் மற்றும் எதிர்வினை பதிவு படிவம்.",
        "aliases": [
            "consent for blood component transfusions", "blood transfusion consent", "blood component consent",
            "transfusion consent", "blood component transfusion consent", "prbc consent", "ffp consent",
            "platelet consent", "blood reaction form", "blood consent form",
            "ratha vangi consent", "iratha vangi consent", "ratham transfusion consent", "ratha vangi sammatham",
            "iratha vangi sammatham", "raththam selutha opputhal",
            "ரத்த தான ஒப்புதல்", "ரத்த மாற்று ஒப்புதல் படிவம்", "இரத்த மாற்று சம்மதம்", "இரத்த மாற்று ஒப்புதல்", "ரத்த வங்கி ஒப்புதல்",
            "transfution concent", "transfution consent", "blood transfution consent", "blod transfusion consent", "transfuson concent"
        ],
        "negative_aliases": ["stock", "stock details", "இருப்பு", "directory", "intercom", "phone"]
    },
    "FORM_CONSENT_DAMA": {
        "id": "FORM_CONSENT_DAMA",
        "title": "DAMA Consent Form",
        "url": "http://192.168.101.75:3000/files/Dama%20Consent%20Form.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Mandatory medicolegal declaration and risk undertaking for discharge against medical advice (DAMA / LAMA).",
        "description_ta": "மருத்துவ ஆலோசனைக்கு மாறாக நோயாளி தானாக வெளியேறுவதற்கான (DAMA / LAMA) பொறுப்பேற்பு படிவம்.",
        "aliases": [
            "dama consent form", "dama consent", "dama form", "lama consent form", "lama consent", "lama form",
            "discharge against medical advice", "dama undertaking", "dama declaration", "dama risk form",
            "hospital vittu poga consent", "veliye poga consent", "veetuku poga consent", "hospital la irunthu poga consent",
            "discharge aaga consent", "discharge against advice",
            "மருத்துவ ஆலோசனைக்கு மாறாக வெளியேறும் படிவம்", "டாமா படிவம்", "டாமா ஒப்புதல்",
            "damma consent", "damma form", "dama concent", "damma concent", "damaa consent"
        ],
        "negative_aliases": []
    },
    "FORM_CONSENT_NOT_WILLING": {
        "id": "FORM_CONSENT_NOT_WILLING",
        "title": "Not Willing Consent",
        "url": "http://192.168.101.75:3000/files/Not%20Willing%20Consent.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Formal clinical documentation of patient or surrogate refusal for proposed investigations, medications, or therapies (NOT WILLING FOR INVESTIGATION OR PROCEDURE CONSENT).",
        "description_ta": "பரிந்துரைக்கப்பட்ட பரிசோதனைகள் அல்லது மருத்துவ சிகிச்சையை நோயாளி மறுப்பதற்கான ஒப்புதல் படிவம் (சிகிச்சை மறுப்பு).",
        "aliases": [
            "not willing consent form", "not willing consent", "not willing form", "treatment refusal",
            "procedure refusal", "investigation refusal", "refusal consent",
            "not willing for investigation or procedure consent", "refusal of treatment form", "treatment refusal form",
            "maruppu form", "maruppu padivam", "chikitsai maruppu form", "treatment vendam consent",
            "treatment vendam form", "investigation thevailla consent", "viruppamillai consent", "viruppamilla padivam",
            "சிகிச்சை மறுப்பு படிவம்", "விருப்பமில்லா படிவம்", "மறுப்பு படிவம்", "மறுப்பு ஒப்புதல்",
            "not wiling consent", "not willin consent", "not willng concent", "not willing concent", "marupu form"
        ],
        "negative_aliases": []
    },
    "FORM_CONSENT_ADMISSION": {
        "id": "FORM_CONSENT_ADMISSION",
        "title": "General Patient Admission Consent",
        "url": "http://192.168.101.75:3000/files/consent.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "General hospital in-patient care, nursing rounds, and routine diagnostic tests authorization (General Consent for Admission).",
        "description_ta": "மருத்துவமனையில் உள்நோயாளியாக சேருதல், செவிலியர் பராமரிப்பு மற்றும் பொது சிகிச்சைக்கான ஒப்புதல் படிவம்.",
        "aliases": [
            "general consent for admission", "admission consent", "general admission consent",
            "inpatient admission consent", "ward admission consent", "general patient admission consent",
            "patient admission form", "inpatient consent form", "routine consent form", "hospital admission consent",
            "serkai sammatham", "serkai padivam", "serkkai opputhal", "admit aaga consent", "ward serkai consent",
            "admit sammatham", "ip admission consent",
            "சேர்க்கை ஒப்புதல் படிவம்", "நோயாளி சேர்க்கை சம்மதம்", "சேர்க்கை படிவம்",
            "admisison consent", "admissin consent", "admision concent", "admission concent", "admisn consent"
        ],
        "negative_aliases": []
    },
    "FORM_CONSENT_SURROGATE": {
        "id": "FORM_CONSENT_SURROGATE",
        "title": "Surrogate Consent",
        "url": "http://192.168.101.75:3000/files/SURROGATE%20CONSENT.pdf",
        "category": "Consent Forms",
        "badge": "Medicolegal",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Informed clinical consent protocol for patients incapable of independent medical decision-making (Surrogate / Next-of-Kin decision makers).",
        "description_ta": "சுயமாக முடிவெடுக்க இயலாத நோயாளிகளுக்கான மாற்று முடிவெடுப்பவர் / குடும்பத்தினர் ஒப்புதல் நெறிமுறை.",
        "aliases": [
            "surrogate consent", "substitute decision maker consent", "incapable patient consent",
            "surrogate consent form", "surrogate consent protocol", "surrogate decision maker",
            "surrugate consent", "surogate consent", "surrugate concent", "surogate concent"
        ],
        "negative_aliases": []
    },
    "SECTION_CONSENT_VAULT": {
        "id": "SECTION_CONSENT_VAULT",
        "title": "Clinical Consent Forms Vault",
        "url": "./consent.html",
        "category": "Forms Vault",
        "badge": "Medicolegal Hub",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Comprehensive hospital repository of bilingual operative, procedural, blood transfusion, and treatment refusal consent documents.",
        "description_ta": "அறுவை சிகிச்சை, ரத்த மாற்று, மற்றும் மருத்துவ மறுப்பு ஒப்புதல் படிவங்களின் முழுமையான ஆவணக் காப்பகம்.",
        "aliases": [
            "consent form", "consent forms", "consent vault", "consent hub", "all consent forms",
            "clinical consents", "medicolegal forms", "list of consent forms", "where is consent form",
            "open consent vault", "open consent form", "concent form", "concent forms", "consen form", "consnt form",
            "ஒப்புதல் படிவங்கள்", "ஒப்புதல் படிவம்", "சம்மத படிவங்கள்", "சம்மத படிவம்",
            "opputhal padivam", "oputhal padivam", "oppudhal padivam", "sammatha padivam", "sammatham padivam"
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
        "intent_type": SearchIntent.OPEN_FORM,
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
            "teaching job", "பேராசிரியர் விண்ணப்பம்", "ஆசிரியர் விண்ணப்பம்"
        ],
        "negative_aliases": ["ticketing", "job orders"]
    },
    "SECTION_HR_FORMS": {
        "id": "SECTION_HR_FORMS",
        "title": "HR Forms Hub",
        "url": "./hrforms.html",
        "category": "Forms Vault",
        "badge": "People & Culture",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Central repository of hospital human resource forms: faculty and non-teaching applications, staff promotion, performance management, training feedback, and clinical privileges.",
        "description_ta": "மருத்துவமனை மனிதவளப் படிவங்கள் தளம்: ஆசிரியர் மற்றும் பணியாளர் விண்ணப்பங்கள், பதவி உயர்வு, பயிற்சி பின்னூட்டம், மற்றும் மருத்துவர் பணி உரிமைகள் படிவங்கள்.",
        "aliases": [
            "hr forms", "hr form", "human resource forms", "human resources forms",
            "hr forms hub", "hr vault", "hr documents", "people and culture forms",
            "எச் ஆர் படிவங்கள்", "எச்.ஆர் படிவங்கள்", "பணியாளர் படிவங்கள்", "மனித வள படிவங்கள்",
            "hr padivangal", "hr padivam", "all hr forms", "list of hr forms"
        ],
        "negative_aliases": []
    },
    "FORM_HR_PROMOTION": {
        "id": "FORM_HR_PROMOTION",
        "title": "For Promotion - Non Teaching",
        "url": "http://192.168.101.75:3000/files/For%20promotion%20-%20Non%20Teaching.pdf",
        "category": "HR Forms",
        "badge": "HR Promotion",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Department head appraisal, service seniority verification, and career elevation recommendation form for non-teaching employees.",
        "description_ta": "ஆசிரியரல்லாத பணியாளர்களுக்கான பதவி உயர்வு மற்றும் பணி மூப்பு பரிந்துரை படிவம்.",
        "aliases": [
            "for promotion non teaching", "promotion non teaching", "promotion form",
            "staff promotion form", "for promotion", "career promotion form",
            "promotion recommendation", "பதவி உயர்வு", "பதவி உயர்வு படிவம்",
            "pathavi uyartvu", "pathavi uyartvu form"
        ],
        "negative_aliases": []
    },
    "FORM_HR_NON_PERFORMER": {
        "id": "FORM_HR_NON_PERFORMER",
        "title": "Non Performer - Non Teaching",
        "url": "http://192.168.101.75:3000/files/Non%20performer-%20Non%20Teaching.pdf",
        "category": "HR Forms",
        "badge": "Performance Review",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Departmental evaluation log for identifying performance gaps, structuring retraining modules, and mentoring non-performing staff.",
        "description_ta": "பணியாளர் குறைபாடு மதிப்பீடு, மறுபயிற்சி மற்றும் வழிகாட்டுதல் பதிவு படிவம்.",
        "aliases": [
            "non performer non teaching", "non performer form", "non performer",
            "non performing staff", "performance gap form", "staff mentoring log",
            "retraining form", "குறைபாடு மதிப்பீடு படிவம்", "பணியாளர் குறைபாடு படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_HR_TRAINING_FEEDBACK": {
        "id": "FORM_HR_TRAINING_FEEDBACK",
        "title": "Staff Training Feedback Form",
        "url": "http://192.168.101.75:3000/files/Training%20Feedback%20Form.pdf",
        "category": "HR Forms",
        "badge": "Training Feedback",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Post-training assessment and participant feedback form for hospital induction, fire safety drills, and clinical CME courses.",
        "description_ta": "மருத்துவமனை பயிற்சி மற்றும் பயிலரங்கப் பின்னூட்ட மதிப்பீட்டுப் படிவம்.",
        "aliases": [
            "staff training feedback form", "training feedback form", "training feedback",
            "staff feedback form", "training evaluation form", "induction feedback form",
            "cme feedback", "பயிற்சி படிவம்", "பயிற்சி பின்னூட்டம்", "பயிற்சி பின்னூட்ட படிவம்",
            "payirchi form", "payirchi feedback"
        ],
        "negative_aliases": []
    },
    "FORM_HR_PMS": {
        "id": "FORM_HR_PMS",
        "title": "Performance Management System (PMS) Policy",
        "url": "http://192.168.101.75:3000/files/PMS%20Policy.pdf",
        "category": "HR Forms",
        "badge": "HR Policy",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Institutional framework establishing key performance indicators (KPIs), 360-degree appraisal benchmarks, and merit increments.",
        "description_ta": "நிறுவன செயல்திறன் மேலாண்மை அமைப்பு (PMS), கேபிஐ (KPIs) மற்றும் மதிப்பீட்டுக் கொள்கை.",
        "aliases": [
            "performance management system", "pms policy", "pms form", "pms appraisal",
            "performance management policy", "staff kpi policy", "kpi policy",
            "செயல்திறன் மேலாண்மை கொள்கை", "செயல்திறன் கொள்கை"
        ],
        "negative_aliases": []
    },
    "FORM_HR_PRIVILEGES_MEDICINE": {
        "id": "FORM_HR_PRIVILEGES_MEDICINE",
        "title": "Clinical Privileges - General Medicine",
        "url": "http://192.168.101.75:3000/files/hrmedicine.pdf",
        "category": "HR Forms",
        "badge": "Privileging",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Formal clinical credentialing, procedural scope of practice, and inpatient admission privileges for General Medicine consultants.",
        "description_ta": "பொது மருத்துவ மருத்துவர்களுக்கான மருத்துவ உரிமைகள் மற்றும் அங்கீகாரப் படிவம்.",
        "aliases": [
            "clinical privileges general medicine", "medicine privileges",
            "general medicine privileges", "clinical privileges medicine",
            "physician privileges", "scope of practice medicine",
            "பொது மருத்துவம் அங்கீகார படிவம்", "பொது மருத்துவ உரிமை"
        ],
        "negative_aliases": []
    },
    "FORM_HR_PRIVILEGES_ENT": {
        "id": "FORM_HR_PRIVILEGES_ENT",
        "title": "Clinical Privileges - ENT",
        "url": "http://192.168.101.75:3000/files/hrent.pdf",
        "category": "HR Forms",
        "badge": "Privileging",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Surgical scope of clinical practice, outpatient procedures, and operating theatre credentialing for ENT surgeons.",
        "description_ta": "காது மூக்கு தொண்டை (ENT) மருத்துவர்களுக்கான அறுவைசிகிச்சை மற்றும் மருத்துவ உரிமைகள் படிவம்.",
        "aliases": [
            "clinical privileges ent", "ent privileges", "ent privileges form",
            "ear nose throat privileges", "ent surgical privileges",
            "otorhinolaryngology privileges", "காது மூக்கு தொண்டை உரிமை", "ent உரிமை படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_HR_PRIVILEGES_ANAESTHESIA": {
        "id": "FORM_HR_PRIVILEGES_ANAESTHESIA",
        "title": "Clinical Privileges - Anaesthesia",
        "url": "http://192.168.101.75:3000/files/hranaesthesia.pdf",
        "category": "HR Forms",
        "badge": "Privileging",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Privileging matrix for general, neuraxial, and regional blocks, difficult airway management, and critical care procedures.",
        "description_ta": "மயக்கவியல் (Anaesthesia) மருத்துவர்களுக்கான அங்கீகார மற்றும் சிகிச்சை உரிமைகள் படிவம்.",
        "aliases": [
            "clinical privileges anaesthesia", "anaesthesia privileges",
            "anesthesia privileges", "anaesthesiology privileges", "sedation privileges",
            "மயக்கவியல் உரிமை", "மயக்கவியல் மருத்துவ உரிமை", "மயக்கவியல் படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_HR_CMO_POLICY": {
        "id": "FORM_HR_CMO_POLICY",
        "title": "Chief Medical Officer (CMO) Policy",
        "url": "http://192.168.101.75:3000/files/CMO%20Policy.pdf",
        "category": "HR Forms",
        "badge": "Cadre Policy",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Institutional charter delineating casualty management protocols, emergency response leadership, and clinical shift handover duties.",
        "description_ta": "தலைமை மருத்துவ அலுவலர் (CMO) பணிக் கொள்கை மற்றும் அவசர சிகிச்சைப் பிரிவு நெறிமுறைகள்.",
        "aliases": [
            "chief medical officer policy", "cmo policy", "cmo duties policy",
            "casualty cmo policy", "cmo charter", "தலைமை மருத்துவ அலுவலர் கொள்கை", "cmo கொள்கை"
        ],
        "negative_aliases": []
    },
    "FORM_HR_JUNIOR_RESIDENT": {
        "id": "FORM_HR_JUNIOR_RESIDENT",
        "title": "Junior Resident Policy",
        "url": "http://192.168.101.75:3000/files/Junior%20resident%20Policy.pdf",
        "category": "HR Forms",
        "badge": "Cadre Policy",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Academic governance, patient care documentation standards, night duty schedules, and consultant supervisory guidelines for residents.",
        "description_ta": "இளநிலை உறைவிட மருத்துவர் (Junior Resident) பணிக் கொள்கை மற்றும் வழிகாட்டுதல்கள்.",
        "aliases": [
            "junior resident policy", "resident policy", "jr policy",
            "junior resident guidelines", "resident duty policy", "junior resident rules",
            "இளநிலை உறைவிட மருத்துவர் கொள்கை", "உறைவிட மருத்துவர் கொள்கை"
        ],
        "negative_aliases": []
    },
    "FORM_ITEM_CREATION": {
        "id": "FORM_ITEM_CREATION",
        "title": "Item Creation in HIS",
        "url": "http://192.168.101.75:3000/files/Item%20Creation.pdf",
        "category": "IT Forms",
        "badge": "IT Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Master catalogue addition form for pharmacy drugs, lab tests, and hospital billing tariffs in HIS.",
        "description_ta": "HIS அமைப்பில் புதிய மருந்துகள் மற்றும் பரிசோதனை கட்டண விவரங்களை சேர்க்கும் படிவம்.",
        "aliases": [
            "item creation", "item creation in his", "pharmacy item addition", "item creation form",
            "marunthu porul his addition", "பொருள் உருவாக்கம்", "மருந்து சேர்ப்பு படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_FOOD_TOKEN": {
        "id": "FORM_FOOD_TOKEN",
        "title": "Food Token Requisition Form",
        "url": "http://192.168.101.75:3000/files/FOOD%20TOKEN%20REQUISITION%20FORM.pdf",
        "category": "Common Forms",
        "badge": "Common Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Official requisition for hospital staff, duty doctors, and inpatient attender food tokens.",
        "description_ta": "பணியாளர்கள் மற்றும் மருத்துவர்களுக்கான உணவு டோக்கன் கோரிக்கை படிவம்.",
        "aliases": ["food token", "food token requisition form", "food token form", "diet token", "unavu token", "சாப்பாடு டோக்கன்", "உணவு டோக்கன்"],
        "negative_aliases": []
    },
    "FORM_SBAR": {
        "id": "FORM_SBAR",
        "title": "Handing Over SBAR Record",
        "url": "http://192.168.101.75:3000/files/HANDING%20OVER%20SBAR.pdf",
        "category": "Common Forms",
        "badge": "Clinical Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Structured Situation-Background-Assessment-Recommendation (SBAR) clinical handover protocol sheet.",
        "description_ta": "நர்சிங் மற்றும் மருத்துவ ஷிப்ட் மாற்றத்திற்கான SBAR நோயாளி ஒப்படைப்பு படிவம்.",
        "aliases": ["handing over sbar record", "sbar sheet", "sbar record", "handing over sbar", "sbar"],
        "negative_aliases": []
    },
    "FORM_WARD_SHIFTING": {
        "id": "FORM_WARD_SHIFTING",
        "title": "ICU Checklist - Ward Shifting",
        "url": "http://192.168.101.75:3000/files/ICU%20CHECKLIST%20-%20WARD%20SHIFTING.pdf",
        "category": "Common Forms",
        "badge": "Clinical Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Patient safety checklist for shifting patients between intensive care units and general wards.",
        "description_ta": "தீவிர சிகிச்சை பிரிவிலிருந்து வார்டுக்கு நோயாளியை மாற்றும் சரிபார்ப்பு பட்டியல்.",
        "aliases": ["icu checklist ward shifting", "ward shifting form", "ward shifting", "patient transfer ward", "வார்டு மாற்றம்"],
        "negative_aliases": []
    },
    "FORM_ICU_CASESHEET": {
        "id": "FORM_ICU_CASESHEET",
        "title": "ICU Casesheet Checklist",
        "url": "http://192.168.101.75:3000/files/ICU%20Casesheet%20Checklist.pdf",
        "category": "Common Forms",
        "badge": "Clinical Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Comprehensive clinical casesheet audit checklist for intensive care units and NABH compliance.",
        "description_ta": "தீவிர சிகிச்சை பிரிவு கேஸ் ஷீட் தணிக்கை சரிபார்ப்பு பட்டியல்.",
        "aliases": ["icu casesheet checklist", "icu casesheet", "icu audit checklist"],
        "negative_aliases": ["ward shifting"]
    },
    "FORM_MEWS": {
        "id": "FORM_MEWS",
        "title": "MEWS Score Sheet",
        "url": "http://192.168.101.75:3000/files/MEWS%20SCORE%20SHEET.pdf",
        "category": "Common Forms",
        "badge": "Clinical Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Modified Early Warning Score (MEWS) clinical monitoring chart for early detection of patient deterioration.",
        "description_ta": "நோயாளி உடல்நிலை கண்காணிப்பு MEWS மதிப்பீட்டு தாள்.",
        "aliases": ["mews score sheet", "mews score", "mews sheet", "mews"],
        "negative_aliases": []
    },
    "FORM_EMERGENCY_TRANSFER": {
        "id": "FORM_EMERGENCY_TRANSFER",
        "title": "Emergency Patient Transfer Record",
        "url": "http://192.168.101.75:3000/files/EMERGENCY%20PATIENT%20TRANSFER%20RECORD.pdf",
        "category": "Common Forms",
        "badge": "Clinical Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Documentation record for urgent clinical transfers, ambulance transport, and inter-facility referrals.",
        "description_ta": "அவசர நோயாளி இடமாற்ற ஆவணப் பதிவு படிவம்.",
        "aliases": ["emergency patient transfer record", "patient transfer record", "emergency transfer"],
        "negative_aliases": []
    },
    "SECTION_COMMON_FORMS": {
        "id": "SECTION_COMMON_FORMS",
        "title": "Common Forms Hub (Clinical Indents & ICU Checklists)",
        "url": "./commonforms.html",
        "category": "Forms Vault",
        "badge": "Clinical Vault",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Comprehensive hospital vault of 45 clinical indents, ICU casesheet checklists, SBAR handovers, emergency protocols, and antibiotic review forms.",
        "description_ta": "45 தீவிர சிகிச்சை பிரிவு சரிபார்ப்பு பட்டியல்கள், SBAR ஒப்படைப்பு, போதை மருந்து படிவம் மற்றும் அவசர சிகிச்சை நெறிமுறைகள் களஞ்சியம்.",
        "aliases": [
            "common forms", "common form", "clinical forms", "clinical form", "icu forms", "icu form",
            "common forms hub", "clinical forms hub", "common forms section", "icu checklists",
            "clinical indents", "hospital common forms", "பொது படிவங்கள்", "பொது படிவம்", "மருத்துவ படிவங்கள்"
        ],
        "negative_aliases": ["consent", "it forms", "hr forms", "ஒப்புதல்"]
    },
    "FORM_CODE_BLUE": {
        "id": "FORM_CODE_BLUE",
        "title": "Code Blue Protocol & Algorithm",
        "url": "http://192.168.101.75:3000/files/Code.pdf",
        "category": "Emergency Protocols",
        "badge": "Emergency Protocol",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Cardiac arrest emergency response algorithm, adult CPR sequence, and resuscitation protocol.",
        "description_ta": "இதய நிறுத்தம் அவசர கால மீட்பு நெறிமுறை மற்றும் மறுமலர்ச்சி வழிமுறை.",
        "aliases": ["code blue form", "code blue algorithm", "code blue algorithm sheet", "code blue resuscitation algorithm", "code blue pdf"],
        "negative_aliases": []
    },
    "FORM_CODE_BLUE_ANALYSIS": {
        "id": "FORM_CODE_BLUE_ANALYSIS",
        "title": "Code Blue Post Event Analysis Form",
        "url": "http://192.168.101.75:3000/files/Code%20Blue%20Post%20Event%20Analysis%20Form.pdf",
        "category": "Emergency Protocols",
        "badge": "Audit Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Post-resuscitation debriefing, response timing, team performance, and clinical outcome documentation.",
        "description_ta": "கோட் ப்ளூ அவசர கால நிகழ்வுக்குப் பிந்தைய பகுப்பாய்வு மற்றும் மறுமலர்ச்சி தணிக்கை படிவம்.",
        "aliases": ["code blue post event analysis form", "code blue post event analysis", "code blue analysis form", "code blue audit form"],
        "negative_aliases": []
    },
    "FORM_CODE_RRT": {
        "id": "FORM_CODE_RRT",
        "title": "Code RRT Activation Form",
        "url": "http://192.168.101.75:3000/files/Code%20RRT%20Activation%20Form.pdf",
        "category": "Emergency Protocols",
        "badge": "Rapid Response",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Rapid Response Team (RRT) activation criteria, vital sign triggers, and immediate bedside intervention log.",
        "description_ta": "விரைவு பதில் குழு (RRT) செயல்முறை மற்றும் நோயாளி தீவிர கண்காணிப்பு படிவம்.",
        "aliases": ["code rrt activation form", "code rrt", "rrt activation form", "rapid response team form", "rrt form"],
        "negative_aliases": []
    },
    "FORM_NARCOTIC": {
        "id": "FORM_NARCOTIC",
        "title": "NARCOTIC DRUGS FORM & Register",
        "url": "http://192.168.101.75:3000/files/NARCOTIC%20DRUGS%20FORM.pdf",
        "category": "Pharmacy & Clinical",
        "badge": "Controlled Drug",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Controlled schedule substance indent, ampoule administration tracking, wastage verification, and double-witness register.",
        "description_ta": "போதை மருந்துகள் (Narcotics) மற்றும் கட்டுப்பாட்டு மருந்துகள் கோரிக்கை மற்றும் பயன்பாட்டு பதிவு படிவம்.",
        "aliases": [
            "narcotic drugs form", "narcotic drugs", "narcotic drug form", "narcotics form", "narcotic register",
            "narcotic indent", "narcotik form", "narcotic form", "narcotic", "narcotics",
            "போதை மருந்து படிவம்", "போதை மருந்து", "மயக்க மருந்து படிவம்"
        ],
        "negative_aliases": []
    },
    "FORM_DRUG_FOOD_INTERACTION": {
        "id": "FORM_DRUG_FOOD_INTERACTION",
        "title": "DRUG - FOOD INTERACTION LIST",
        "url": "http://192.168.101.75:3000/files/DRUG%20-%20FOOD%20INTERACTION%20LIST.pdf",
        "category": "Pharmacy & Clinical",
        "badge": "Clinical Reference",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Hospital reference guide on clinically significant drug-nutrient and meal timing interactions.",
        "description_ta": "மருந்து மற்றும் உணவு இடைவினை பட்டியல் மற்றும் உணவு நேர எச்சரிக்கைகள்.",
        "aliases": ["drug food interaction list", "drug food interaction", "food drug interaction list", "food drug interaction", "drug nutrient interaction"],
        "negative_aliases": []
    },
    "FORM_DRUG_DRUG_INTERACTION": {
        "id": "FORM_DRUG_DRUG_INTERACTION",
        "title": "DRUG - DRUG INTERACTION LIST",
        "url": "http://192.168.101.75:3000/files/DRUG%20-%20DRUG%20INTERACTION%20LIST.pdf",
        "category": "Pharmacy & Clinical",
        "badge": "Clinical Reference",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Clinical reference chart detailing major adverse pharmacokinetic and pharmacodynamic drug-drug combinations.",
        "description_ta": "மருந்துகளுக்கு இடையேயான தீவிர முரண்பாடுகள் மற்றும் இடைவினை பட்டியல்.",
        "aliases": ["drug drug interaction list", "drug drug interaction", "drug interaction list", "drug interactions list"],
        "negative_aliases": []
    },
    "FORM_APPROVED_ABBREVIATIONS": {
        "id": "FORM_APPROVED_ABBREVIATIONS",
        "title": "Approved Medical Abbreviations List 2025-2026",
        "url": "http://192.168.101.75:3000/files/Approved%20abbreviation%20July%202025%20-2026.pdf",
        "category": "Clinical Governance",
        "badge": "NABH Standard",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "NABH approved standardized clinical abbreviations and 'Do Not Use' dangerous abbreviation guidelines.",
        "description_ta": "மருத்துவமனையால் அங்கீகரிக்கப்பட்ட மருத்துவ சுருக்கங்கள் மற்றும் பயன்படுத்தக் கூடாத சுருக்கங்கள் பட்டியல்.",
        "aliases": ["approved abbreviation july 2025 -2026", "approved abbreviations", "approved medical abbreviations", "medical abbreviations", "hospital abbreviations", "do not use abbreviations"],
        "negative_aliases": []
    },
    "FORM_EMERGENCY_MEDS": {
        "id": "FORM_EMERGENCY_MEDS",
        "title": "EMERGENCY MEDICATION LIST - JAN 2026",
        "url": "http://192.168.101.75:3000/files/EMERGENCY%20MEDICATION%20LIST%20-%20JAN%202026.pdf",
        "category": "Emergency Protocols",
        "badge": "Crash Cart List",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Standardized resuscitation trolley and emergency room essential emergency medicines stocking list.",
        "description_ta": "அவசர சிகிச்சை பிரிவு மற்றும் க்ராஷ் கார்ட் (Crash Cart) அத்தியாவசிய மருந்துகள் பட்டியல் - ஜனவரி 2026.",
        "aliases": ["emergency medication list - jan 2026", "emergency medication list", "emergency drug list", "crash cart medication list", "crash cart drugs list"],
        "negative_aliases": []
    },
    "FORM_HIGH_ALERT_MEDS": {
        "id": "FORM_HIGH_ALERT_MEDS",
        "title": "HIGH ALERT MEDICATIONS",
        "url": "http://192.168.101.75:3000/files/HIGH%20ALERT%20MEDICATIONS.pdf",
        "category": "Pharmacy & Clinical",
        "badge": "Patient Safety",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Safe handling, independent double-check, storage segregation, and dosing protocols for high-alert drugs.",
        "description_ta": "அதிக கவனம் தேவைப்படும் உயர் எச்சரிக்கை மருந்துகள் (High Alert Medications) மற்றும் பாதுகாப்பு நெறிமுறைகள்.",
        "aliases": ["high alert medications", "high alert drugs", "high alert medication list", "high alert meds list", "high alert meds", "high alert form", "உயர் எச்சரிக்கை மருந்துகள்"],
        "negative_aliases": []
    },
    "FORM_ANTIBIOTIC_REVIEW": {
        "id": "FORM_ANTIBIOTIC_REVIEW",
        "title": "48 Hour Antibiotics Review Form",
        "url": "http://192.168.101.75:3000/files/48%20Hour%20Antibiotics%20Review%20From.pdf",
        "category": "Infection Control",
        "badge": "Antimicrobial Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Antimicrobial stewardship 48-hour time-out evaluation form for de-escalation or cessation of empiric therapy.",
        "description_ta": "நுண்ணுயிர் எதிர்ப்பி மருந்துகளின் (Antibiotics) 48 மணி நேர மறுஆய்வு மற்றும் பாதுகாப்பு படிவம்.",
        "aliases": [
            "48 hour antibiotics review form", "48 hour antibiotics review", "antibiotic review form",
            "antibiotics review form", "48 hour antibiotic review", "48 hr antibiotic review",
            "antibiotic time out", "antibiotic review", "antibiotics review"
        ],
        "negative_aliases": []
    },
    "FORM_DAYCARE_ASSESSMENT": {
        "id": "FORM_DAYCARE_ASSESSMENT",
        "title": "Day Care Assessment Form",
        "url": "http://192.168.101.75:3000/files/Day%20Care%20Assessment%20Form.pdf",
        "category": "Clinical Assessment",
        "badge": "Day Care Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Pre-procedure clinical evaluation, anesthesia clearance, and nursing admission sheet for day-care patients.",
        "description_ta": "பகல்நேர சிகிச்சை (Day Care) நோயாளி ஆரம்ப மருத்துவ மதிப்பீட்டு படிவம்.",
        "aliases": ["day care assessment form", "day care assessment", "daycare assessment form", "daycare assessment"],
        "negative_aliases": []
    },
    "FORM_DAYCARE_DISCHARGE": {
        "id": "FORM_DAYCARE_DISCHARGE",
        "title": "Day Care Discharge Summary",
        "url": "http://192.168.101.75:3000/files/Day%20Care%20-%20Discharge%20Summary.pdf",
        "category": "Clinical Assessment",
        "badge": "Day Care Form",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Standardized post-procedure discharge note, follow-up instructions, and home-care guidance for day care patients.",
        "description_ta": "பகல்நேர சிகிச்சை (Day Care) நோயாளி வெளியேற்ற சுருக்கம் (Discharge Summary).",
        "aliases": ["day care discharge summary", "day care - discharge summary", "daycare discharge summary", "daycare discharge form"],
        "negative_aliases": []
    },
    "FORM_ER_DISCHARGE": {
        "id": "FORM_ER_DISCHARGE",
        "title": "ER Discharge Summary Form",
        "url": "http://192.168.101.75:3000/files/ER%20-%20DISCHARGE%20SUMMARY%20FORM.pdf",
        "category": "Emergency Protocols",
        "badge": "ER Record",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Emergency Room clinical summary, emergency care rendered, and outpatient referral discharge slip.",
        "description_ta": "அவசர சிகிச்சை பிரிவு (ER) வெளியேற்ற சுருக்கம் படிவம்.",
        "aliases": ["er discharge summary form", "er discharge summary", "er - discharge summary form", "emergency room discharge summary"],
        "negative_aliases": []
    },
    "FORM_ER_DOCTOR_ASSESSMENT": {
        "id": "FORM_ER_DOCTOR_ASSESSMENT",
        "title": "ER Doctors Initial Assessment Form",
        "url": "http://192.168.101.75:3000/files/DOCTORS%20INITIAL%20ASSESSMENT%20FOR%20EMERGENCY%20ROOM.pdf",
        "category": "Emergency Protocols",
        "badge": "ER Assessment",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Emergency room doctor's initial triage, primary survey, physical findings, and preliminary diagnosis form.",
        "description_ta": "அவசர சிகிச்சை பிரிவு (ER) மருத்துவரின் ஆரம்ப மதிப்பீட்டு படிவம்.",
        "aliases": ["er doctors initial assessment form", "doctors initial assessment for emergency room", "er doctor initial assessment", "er initial assessment doctor", "er doctor assessment"],
        "negative_aliases": []
    },
    "FORM_ER_NURSE_ASSESSMENT": {
        "id": "FORM_ER_NURSE_ASSESSMENT",
        "title": "ER Nurses Initial Assessment Form",
        "url": "http://192.168.101.75:3000/files/Nurses%20Initial%20Assessment%20for%20Emergency%20Room.pdf",
        "category": "Emergency Protocols",
        "badge": "ER Assessment",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Emergency room nurse triage, baseline vital signs, pain score, and nursing admission documentation.",
        "description_ta": "அவசர சிகிச்சை பிரிவு (ER) செவிலியர் ஆரம்ப மதிப்பீட்டு படிவம்.",
        "aliases": ["er nurses initial assessment form", "nurses initial assessment for emergency room", "er nurse initial assessment", "er initial assessment nurse", "er nurse assessment"],
        "negative_aliases": []
    },
    "FORM_ADR": {
        "id": "FORM_ADR",
        "title": "ADR-Form (Adverse Drug Reaction)",
        "url": "http://192.168.101.75:3000/files/ADR-Form.pdf",
        "category": "Patient Safety",
        "badge": "Pharmacovigilance",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Adverse drug reaction incident reporting form for suspected drug allergies and pharmacovigilance logging.",
        "description_ta": "மருந்து ஒவ்வாமை மற்றும் பாதகமான எதிர்வினை பதிவு படிவம் (ADR Form).",
        "aliases": ["adr-form", "adr form", "adverse drug reaction form", "adr report", "pharmacovigilance form", "மருந்து ஒவ்வாமை படிவம்"],
        "negative_aliases": []
    },
    "FORM_INCIDENT_REPORT": {
        "id": "FORM_INCIDENT_REPORT",
        "title": "Incident Report Form",
        "url": "http://192.168.101.75:3000/files/Incident.pdf",
        "category": "Patient Safety",
        "badge": "Safety Incident",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Hospital incident and sentinel event reporting form for falls, equipment failure, and near-miss occurrences.",
        "description_ta": "மருத்துவமனை அசம்பாவித நிகழ்வு மற்றும் விபத்து அறிக்கை படிவம் (Incident Report).",
        "aliases": ["incident report", "incident report form", "incident form", "sentinel event form", "near miss form", "நிகழ்வு அறிக்கை படிவம்", "விபத்து அறிக்கை"],
        "negative_aliases": []
    },
    "FORM_TRANSFUSION_PROTOCOL": {
        "id": "FORM_TRANSFUSION_PROTOCOL",
        "title": "Transfusion Technique Protocol",
        "url": "http://192.168.101.75:3000/files/transfusionprotocol.pdf",
        "category": "Blood Bank",
        "badge": "Clinical Protocol",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Standardized bedside blood and blood component administration checklist, filter use, and reaction monitoring.",
        "description_ta": "ரத்த மாற்று செயல்முறை மற்றும் நிர்வாக நெறிமுறை வழிகாட்டுதல்.",
        "aliases": ["transfusion technique protocol", "transfusion protocol form", "blood transfusion protocol sheet"],
        "negative_aliases": []
    },
    "FORM_ANTIBIOGRAM": {
        "id": "FORM_ANTIBIOGRAM",
        "title": "Antibiogram",
        "url": "http://192.168.101.75:3000/files/ANTIBIOGRAM.pdf",
        "category": "Infection Control",
        "badge": "Microbiology",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Institutional microbial susceptibility profile and antibiotic resistance cumulative surveillance report.",
        "description_ta": "மருத்துவமனை நுண்ணுயிர் எதிர்ப்பு உணர்திறன் அறிக்கை (Antibiogram).",
        "aliases": ["antibiogram", "antibiogram form", "antibiogram report", "hospital antibiogram"],
        "negative_aliases": []
    },
    "FORM_RESTRICTED_ANTIBIOTIC": {
        "id": "FORM_RESTRICTED_ANTIBIOTIC",
        "title": "Restricted Anti-biotic Form (HIC)",
        "url": "http://192.168.101.75:3000/files/HIC.pdf",
        "category": "Infection Control",
        "badge": "Antimicrobial Stewardship",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Hospital Infection Control prior-authorization request form for prescribing reserve and restricted antibiotics.",
        "description_ta": "கட்டுப்படுத்தப்பட்ட நுண்ணுயிர் எதிர்ப்பி மருந்துகள் கோரிக்கை படிவம் (Restricted Antibiotic Form).",
        "aliases": ["restricted anti-biotic form", "restricted antibiotic form", "reserve antibiotic form", "hic antibiotic form", "கட்டுப்படுத்தப்பட்ட ஆன்டிபயாடிக் படிவம்"],
        "negative_aliases": []
    },
    "FORM_RESTRICTED_ANTIBIOTIC_LIST": {
        "id": "FORM_RESTRICTED_ANTIBIOTIC_LIST",
        "title": "Restricted Anti-biotic Drug List",
        "url": "http://192.168.101.75:3000/files/antibiotic.pdf",
        "category": "Infection Control",
        "badge": "Drug Formulary",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Institutional listing of reserve, restricted, and watch-group antimicrobial agents requiring ID / HIC authorization.",
        "description_ta": "அங்கீகரிக்கப்பட்ட கட்டுப்படுத்தப்பட்ட நுண்ணுயிர் எதிர்ப்பி மருந்துகளின் பட்டியல்.",
        "aliases": ["restricted anti-biotic drug list", "restricted antibiotic drug list", "restricted antibiotic list", "restricted antibiotics list"],
        "negative_aliases": []
    },
    "FORM_COUNSELLING": {
        "id": "FORM_COUNSELLING",
        "title": "Counselling Documentation Form",
        "url": "http://192.168.101.75:3000/files/Counselling%20Documentation%20Form.pdf",
        "category": "Clinical Assessment",
        "badge": "Clinical Counselling",
        "intent_type": SearchIntent.OPEN_FORM,
        "description": "Clinical care counselling, family discussion, poor prognosis, and treatment options documentation sheet.",
        "description_ta": "நோயாளி மற்றும் உறவினர்களுக்கான மருத்துவ ஆலோசனை மற்றும் வழிகாட்டுதல் பதிவு படிவம்.",
        "aliases": ["counselling documentation", "counselling documentation form", "counselling form", "counseling form", "patient counselling form", "நோயாளி ஆலோசனை படிவம்"],
        "negative_aliases": []
    },
    "DOC_HOLIDAYS_2026": {
        "id": "DOC_HOLIDAYS_2026",
        "title": "List of Holidays for the Year 2026",
        "url": "http://192.168.101.75:3000/files/LIST%20OF%20HOLIDAYS%20FOR%20THE%20YEAR%202026.pdf",
        "category": "HR Circulars",
        "badge": "Circular",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Official institutional approved holiday calendar for the academic and hospital calendar year 2026.",
        "description_ta": "2026 ஆம் ஆண்டிற்கான அதிகாரப்பூர்வ மருத்துவமனை மற்றும் கல்லூரி விடுமுறை நாட்கள் பட்டியல்.",
        "aliases": ["list of holidays 2026", "holidays 2026", "holiday calendar 2026", "hospital holidays 2026", "விடுமுறை பட்டியல் 2026"],
        "negative_aliases": []
    },
    "DIR_CIRCULARS": {
        "id": "DIR_CIRCULARS",
        "title": "APH Recent Circulars Hub",
        "url": "./recent circular.html",
        "category": "Circulars & Bulletins",
        "badge": "Circulars Hub",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Management memorandums, safety meeting circulars, SWOT analysis, in-house applications launch, and executive circulars.",
        "description_ta": "மருத்துவமனை நிர்வாகத்தின் சமீபத்திய சுற்றறிக்கைகள், பாதுகாப்பு அறிவிப்புகள் மற்றும் அதிகாரப்பூர்வ அலுவலக உத்தரவுகள்.",
        "aliases": [
            "digital e circulars", "digital e-circulars", "digital e circular", "digital e circulars & protocols",
            "digital e circulars and protocols", "e circulars", "e-circulars", "e circular", "e-circular",
            "recent circulars", "recent circular", "circulars", "circular", "hospital circulars", "hospital circular",
            "management circulars", "management circular", "office orders", "office circulars", "latest circulars",
            "circulars and protocols", "protocols and circulars", "circulars directory", "circulars hub",
            "circulars list", "list of circulars", "all circulars", "open circulars",
            "சுற்றறிக்கை", "சுற்றறிக்கைகள்", "மின் சுற்றறிக்கை", "அலுவலக சுற்றறிக்கை"
        ],
        "negative_aliases": []
    },
    "SECTION_E_CIRCULARS": {
        "id": "SECTION_E_CIRCULARS",
        "title": "Digital E – Circulars & Protocols (Bulletin Board)",
        "url": "./index.html#e-circulars",
        "category": "Portal Section",
        "badge": "Section 7",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Real-time bulletin board featuring live 24-hr duty roster, blood bank stock, police directory, clinical cases, PMS policy, and recent circulars.",
        "description_ta": "மருத்துவமனை முதன்மை பக்கத்தில் உள்ள நேரடி பணி பட்டியல், ரத்த வங்கி இருப்பு, காவல் நிலைய எண்கள் மற்றும் சுற்றறிக்கைகள் பகுதி.",
        "aliases": [
            "digital e circulars section", "e circulars section", "where is circulars section", "circulars on homepage",
            "digital e bulletin", "digital bulletin board", "bulletin board", "digital board",
            "சுற்றறிக்கை பகுதி", "அறிவிப்பு பலகை"
        ],
        "negative_aliases": []
    },
    "DOC_DUTY_ROSTER": {
        "id": "DOC_DUTY_ROSTER",
        "title": "24-Hour Doctor On-Duty Roster",
        "url": "http://192.168.101.75:3000/files/24hr's Duty Details.pdf",
        "category": "Digital E-Circulars",
        "badge": "Duty Roster",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Live roster for Casualty CMOs, Intensivists, and Nursing Supervisors on 24-hour hospital rotation.",
        "description_ta": "அவசர சிகிச்சை மருத்துவர்கள், தீவிர சிகிச்சைப் பிரிவு மருத்துவர்கள் மற்றும் நர்சிங் கண்காணிப்பாளர்களுக்கான 24 மணி நேர நேரடி பணிப் பட்டியல்.",
        "aliases": [
            "24hr duty roster", "24 hours duty roster", "duty roster", "doctor duty roster", "cmo duty roster", "cmo duty",
            "intensivist duty", "nursing supervisor roster", "on duty roster", "duty details", "who is on duty",
            "casualty duty doctor", "casualty cmo", "duty doctor list", "today duty doctor", "24hr duty details",
            "24hrs duty details", "duty list", "doctor roster", "24hr duty", "duty doctor",
            "டூட்டி ரோஸ்டர்", "பணி அட்டவணை", "டூட்டி டாக்டர்", "இன்றைய டூட்டி டாக்டர்"
        ],
        "negative_aliases": []
    },
    "DOC_BLOOD_BANK_STOCK": {
        "id": "DOC_BLOOD_BANK_STOCK",
        "title": "Blood Bank Stock Details",
        "url": "http://192.168.101.75:3000/files/Blood Bank Stock Details.pdf",
        "category": "Digital E-Circulars",
        "badge": "Live Inventory",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Real-time hospital inventory of PRBC, FFP, Platelets, cryoprecipitate, and rare blood units.",
        "description_ta": "ரத்த வங்கியின் நேரடி இருப்பு விவரம் (PRBC, FFP, பிளேட்லெட்டுகள் மற்றும் அரிய வகை ரத்தப் பிரிவுகள்).",
        "aliases": [
            "blood bank stock", "blood stock", "blood bank stock details", "blood availability", "blood units available",
            "prbc stock", "ffp stock", "platelet stock", "platelets stock", "cryo stock", "rare blood units",
            "blood bank inventory", "blood stock list", "ratha vangi stock", "iratha vangi",
            "இரத்த வங்கி இருப்பு விவரம்", "இரத்த வங்கி இருப்பு", "ரத்த வங்கி ஸ்டாக்", "ரத்த இருப்பு"
        ],
        "negative_aliases": ["consent", "form", "padivam", "ஒப்புதல்"]
    },
    "DOC_POLICE_STATION_NUMBERS": {
        "id": "DOC_POLICE_STATION_NUMBERS",
        "title": "Police Station Contact Numbers & Liaison Directory",
        "url": "http://192.168.101.75:3000/files/police.pdf",
        "category": "Digital E-Circulars",
        "badge": "Emergency Hotline",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Nearest local police station contacts, police inspector direct lines, police outpost, and MLC hospital liaison directory.",
        "description_ta": "அருகிலுள்ள காவல் நிலைய தொலைபேசி எண்கள், காவல் ஆய்வாளர் நேரடி இணைப்புகள் மற்றும் மருத்துவ-சட்ட (MLC) தொடர்பு வழிகாட்டி.",
        "aliases": [
            "police station number", "police station numbers", "police station phone number", "police directory",
            "nearest police station", "police contact", "police contacts", "police station contact", "police station phone",
            "mlc police", "police outpost", "police liaison", "police station hotline", "police numbers",
            "local police station", "police number", "police phone",
            "காவல் நிலைய எண்", "காவல் நிலைய எண்கள்", "காவல்துறை தொடர்பு", "போலீஸ் எண்", "போலீஸ் போன் எண்"
        ],
        "negative_aliases": []
    },
    "DOC_CLINICAL_CASE_PATIENTS": {
        "id": "DOC_CLINICAL_CASE_PATIENTS",
        "title": "Clinical Case Patients Documentation & Protocols",
        "url": "http://192.168.101.75:3000/files/clinical.pdf",
        "category": "Digital E-Circulars",
        "badge": "Clinical Protocol",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Clinical case patient documentation, medical protocols, guidelines, and hospital clinical case reporting standards.",
        "description_ta": "மருத்துவ வழக்கு நோயாளிகள் ஆவணப்படுத்தல், மருத்துவ நெறிமுறைகள் மற்றும் வழிகாட்டுதல்கள்.",
        "aliases": [
            "clinical case patients", "clinical cases", "clinical case patient", "clinical case documentation",
            "clinical case protocol", "clinical protocols and standing orders", "clinical casesheet protocol",
            "clinical guidelines circular", "clinical pdf",
            "மருத்துவ வழக்கு நோயாளிகள்", "மருத்துவ வழக்கு வழிகாட்டுதல்", "மருத்துவ நெறிமுறை"
        ],
        "negative_aliases": []
    },
    "DOC_PMS_POLICY": {
        "id": "DOC_PMS_POLICY",
        "title": "Performance Management System (PMS) Policy & KPI Framework",
        "url": "http://192.168.101.75:3000/files/PMS Policy.pdf",
        "category": "Digital E-Circulars",
        "badge": "HR Policy",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Performance Management System (PMS) policy, key performance indicators (KPIs), staff appraisal framework, and hospital evaluation guidelines.",
        "description_ta": "பணியாளர் செயல்திறன் மேலாண்மை அமைப்பு (PMS) கொள்கை, முக்கிய செயல்திறன் குறிகாட்டிகள் (KPI) மற்றும் மதிப்பீட்டு நெறிமுறை.",
        "aliases": [
            "pms policy", "performance management system", "performance management system policy", "pms",
            "hospital pms", "kpi policy", "staff appraisal policy", "pms kpis", "performance appraisal framework",
            "performance evaluation policy", "annual appraisal policy", "pms policy pdf",
            "செயல்திறன் மேலாண்மை கொள்கை", "பணியாளர் மதிப்பீடு கொள்கை"
        ],
        "negative_aliases": []
    },
    "CIRCULAR_SAFETY_2026": {
        "id": "CIRCULAR_SAFETY_2026",
        "title": "Safety Meeting Circular- 2026",
        "url": "http://192.168.101.75:3000/files/Safety meeting Circular- 2026.pdf",
        "category": "Circulars",
        "badge": "New Circular",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Official institutional safety committee directives, emergency drill guidelines, and hospital safety protocols (18.02.2026).",
        "description_ta": "மருத்துவமனை பாதுகாப்பு குழு கூட்டம் மற்றும் வழிகாட்டுதல்கள் பற்றிய அதிகாரப்பூர்வ சுற்றறிக்கை.",
        "aliases": ["safety meeting circular", "safety circular 2026", "safety meeting circular 2026", "safety circular", "பாதுகாப்பு கூட்ட சுற்றறிக்கை"],
        "negative_aliases": []
    },
    "CIRCULAR_SWOT_2026": {
        "id": "CIRCULAR_SWOT_2026",
        "title": "SWOT Analysis Circular Jan 2026",
        "url": "http://192.168.101.75:3000/files/SWOT ANALYSIS CIRCULAR jan 2026.pdf",
        "category": "Circulars",
        "badge": "Circular",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Hospital SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats) strategic governance circular (02.02.2026).",
        "description_ta": "மருத்துவமனை SWOT பகுப்பாய்வு மற்றும் நிர்வாக முன்னேற்ற வழிகாட்டுதல் சுற்றறிக்கை.",
        "aliases": ["swot analysis circular", "swot analysis", "swot circular jan 2026", "swot circular", "swot analysis circular 2026"],
        "negative_aliases": []
    },
    "CIRCULAR_AMS_2026": {
        "id": "CIRCULAR_AMS_2026",
        "title": "AMSOUR DEVELOPED INHOUSE APPLICATIONS - 2026",
        "url": "http://192.168.101.75:3000/files/AMS.pdf",
        "category": "Circulars",
        "badge": "Circular",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Official release circular for hospital in-house developed applications: Pathology Barcode, Eye Camp Outreach, Clinical Care & LineLoom.",
        "description_ta": "மருத்துவமனை உள் கட்டமைக்கப்பட்ட மென்பொருள்கள் பயன்பாட்டு வெளியீட்டு சுற்றறிக்கை.",
        "aliases": ["ams inhouse applications", "ams applications circular", "our developed inhouse applications", "inhouse applications circular", "ams circular"],
        "negative_aliases": []
    },
    "CIRCULAR_REFUGEE_2026": {
        "id": "CIRCULAR_REFUGEE_2026",
        "title": "Refugee - 2026 Circular",
        "url": "http://192.168.101.75:3000/files/Refugee.pdf",
        "category": "Circulars",
        "badge": "Circular",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Hospital protocol and admission guidelines circular for refugee patient care (04.02.2026).",
        "description_ta": "அகதிகள் சிகிச்சை நெறிமுறை மற்றும் சேர்க்கை வழிகாட்டுதல் சுற்றறிக்கை.",
        "aliases": ["refugee circular", "refugee 2026", "refugee policy circular", "refugee circular 2026"],
        "negative_aliases": []
    },
    "CIRCULAR_CODE_VIOLET": {
        "id": "CIRCULAR_CODE_VIOLET",
        "title": "Code Violet Protocol & Circular",
        "url": "http://192.168.101.75:3000/files/Code Violet.pdf",
        "category": "Circulars",
        "badge": "Emergency Code",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Hospital emergency Code Violet protocol: Combative person, workplace violence, physical assault response and security containment.",
        "description_ta": "மருத்துவமனை அவசர குறியீடு கோட் வயலெட் (Code Violet) - வன்முறை தடுப்பு மற்றும் ஊழியர் பாதுகாப்பு நெறிமுறை.",
        "aliases": ["code violet", "code violet circular", "code violet policy", "code violet protocol", "கோட் வயலெட்"],
        "negative_aliases": []
    },
    "CIRCULAR_PATIENT_VALUABLE": {
        "id": "CIRCULAR_PATIENT_VALUABLE",
        "title": "Patient Valuable Policy Circular",
        "url": "http://192.168.101.75:3000/files/Patient Valuable Policy.pdf",
        "category": "Circulars",
        "badge": "Hospital Policy",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Hospital policy on safeguarding and documenting patient valuable articles, cash, jewelry, and custody protocols.",
        "description_ta": "நோயாளிகளின் மதிப்புமிக்க பொருட்கள், நகை மற்றும் பணம் பாதுகாப்பு கொள்கை சுற்றறிக்கை.",
        "aliases": ["patient valuable policy", "patient valuable circular", "patient valuables policy", "patient valuables circular"],
        "negative_aliases": []
    },
    "CIRCULAR_EMERGENCY_RESCUE_TEAM": {
        "id": "CIRCULAR_EMERGENCY_RESCUE_TEAM",
        "title": "Emergency Rescue Team (ERT) Circular",
        "url": "http://192.168.101.75:3000/files/Emergency Rescue Team.pdf",
        "category": "Circulars",
        "badge": "Safety Circular",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Hospital Emergency Rescue Team (ERT) composition, roles, disaster mobilization, and casualty triage response duties.",
        "description_ta": "மருத்துவமனை அவசர மீட்புக் குழு (ERT) அமைப்பு மற்றும் பேரிடர் மீட்பு பணி வழிகாட்டுதல் சுற்றறிக்கை.",
        "aliases": ["emergency rescue team", "rescue team circular", "ert circular", "emergency rescue team circular", "அவசர மீட்புக் குழு"],
        "negative_aliases": []
    },
    "DIR_FORMS_HUB": {
        "id": "DIR_FORMS_HUB",
        "title": "Hospital Forms Vault",
        "url": "./commonforms.html",
        "category": "Forms Vault",
        "badge": "Portal Hub",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Complete digital repository of all departmental, clinical, and administrative forms.",
        "description_ta": "மருத்துவமனை அனைத்து படிவங்களின் மையக் களஞ்சியம்.",
        "aliases": ["where is the forms section", "forms hub", "hospital forms vault", "forms vault", "forms section", "all forms"],
        "negative_aliases": []
    },

    # =========================================================================
    # 8. TARIFF & LIVE STOCK (FINANCIAL & SUPPLY DASHBOARD)
    # =========================================================================
    "SECTION_TARIFF_STOCK": {
        "id": "SECTION_TARIFF_STOCK",
        "title": "Tariff & Live Stock Dashboard",
        "url": "./index.html#tariff-stock",
        "category": "Portal Section",
        "badge": "Section 8",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Financial & Supply dashboard featuring Hospital Tariffs (7 schedules), Pharmacy Live Stock (139 drugs, IP, OP, Insurance, Formulary), and General Store Inventory.",
        "description_ta": "மருத்துவமனை கட்டண விவரங்கள் (7 அட்டவணைகள்), மருந்தக நேரடி இருப்பு (139 மருந்துகள், உள்/வெளிநோயாளி/காப்பீடு) மற்றும் பொது சேமிப்பு கிடங்கு இருப்பு பிரிவு.",
        "aliases": [
            "tariff & live stock", "tariff and live stock", "tariff live stock", "tariff stock", "live stock",
            "tariffs and stock", "tariffs & stock", "hospital tariffs and stock", "tariff and stock section",
            "where is tariff section", "tariff section", "live stock section", "billing schedules and live supply counters",
            "கட்டணம் மற்றும் இருப்பு", "கட்டண விவரம்", "மருந்து இருப்பு", "சேமிப்பு கிடங்கு இருப்பு", "கட்டண அட்டவணை",
            "tariff விவரம்", "hospital kattanam", "vilai vivaram", "selavu vivaram"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "number", "login", "consent", "படிவம்", "ஒப்புதல்"]
    },
    "CARD_HOSPITAL_TARIFFS": {
        "id": "CARD_HOSPITAL_TARIFFS",
        "title": "MAPIMS Hospital Tariffs (Schedule of Charges)",
        "url": "./index.html#tariff-stock",
        "category": "Tariff & Packages",
        "badge": "Tariff Schedule",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Official MAPIMS schedule of charges across 7 specialized departments: Admission/Packages, Lab, Radiology, Physiotherapy, OT/Surgery, ICU & Special Ward, and Other Departments.",
        "description_ta": "அட்மிஷன் பேக்கேஜ், ஆய்வகம், கதிரியக்கவியல், பிசியோதெரபி, அறுவை சிகிச்சை தியேட்டர், ஐசியூ மற்றும் சிறப்பு வார்டு உள்ளிட்ட 7 துறைகளுக்கான மருத்துவமனை கட்டண அட்டவணை.",
        "aliases": [
            "hospital tariffs", "hospital tariff", "tariffs", "tariff", "schedule of charges",
            "hospital charges", "billing rates", "rate list", "treatment cost", "hospital fees",
            "service charges", "all tariffs", "list of tariffs", "hospital billing rates",
            "மருத்துவமனை கட்டணம்", "கட்டண பட்டியல்", "கட்டண விபரம்", "மருத்துவ கட்டணம்", "hospital kattanam",
            "billing charges"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "number", "login", "consent", "படிவம்", "ஒப்புதல்"]
    },
    "DOC_TARIFF_PACKAGES": {
        "id": "DOC_TARIFF_PACKAGES",
        "title": "Special Treatment & Health Packages (04.05.2026)",
        "url": "http://192.168.101.75:3000/files/Adhiparasakthi Hospitals Special Packages (04.05.2026).pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Official hospital outpatient & inpatient special treatment packages, surgical packages, Panchayat discount (15%), and master health checkup rates.",
        "description_ta": "வெளிநோயாளி மற்றும் உள்நோயாளி சிறப்பு சிகிச்சை பேக்கேஜ்கள், அறுவை சிகிச்சை கட்டண சலுகைகள் மற்றும் பஞ்சாயத்து 15% தள்ளுபடி விவரங்கள்.",
        "aliases": [
            "special packages", "admission packages", "health packages", "deluxe packages", "hospital packages",
            "treatment packages", "master packages", "package tariff", "panchayat discount", "hospital special packages",
            "inpatient packages", "outpatient discount package",
            "சிகிச்சை தொகுப்பு", "ஹெல்த் பேக்கேஜ்", "பேக்கேஜ் கட்டணம்", "பஞ்சாயத்து தள்ளுபடி"
        ],
        "negative_aliases": ["intercom", "phone", "extension"]
    },
    "DOC_TARIFF_LAB": {
        "id": "DOC_TARIFF_LAB",
        "title": "Laboratory Investigation Tariff",
        "url": "http://192.168.101.75:3000/files/Lab Tariff.pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Comprehensive pathology, clinical biochemistry, microbiology, and haematology laboratory diagnostic test charges and OP/IP ward rates.",
        "description_ta": "பத்தாலஜி, பயோகெமிஸ்ட்ரி, மைக்ரோபயாலஜி மற்றும் ரத்த பரிசோதனைகளுக்கான அதிகாரப்பூர்வ லேப் கட்டண விவரங்கள்.",
        "aliases": [
            "lab tariff", "lab charges", "laboratory tariff", "lab investigation tariff", "laboratory test charges",
            "blood test charges", "pathology charges", "biochemistry tariff", "microbiology tariff", "lab test rates",
            "investigation charges", "lab rates", "laboratory charges",
            "லேப் கட்டணம்", "இரத்த பரிசோதனை கட்டணம்", "ஆய்வக கட்டணம்"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "requisition", "request form", "பரிசோதனை படிவம்"]
    },
    "DOC_TARIFF_RADIOLOGY": {
        "id": "DOC_TARIFF_RADIOLOGY",
        "title": "Radiology Imaging Tariff",
        "url": "http://192.168.101.75:3000/files/Radiology Tariff.pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Schedule of charges for Digital X-Ray, CT Scan, MRI, Ultrasound (USG), Doppler, and special radiologic procedures.",
        "description_ta": "டிஜிட்டல் எக்ஸ்ரே, சிடி ஸ்கேன், எம்ஆர்ஐ, அல்ட்ராசவுண்ட் (USG) மற்றும் சிறப்பு கதிரியக்க பரிசோதனை கட்டண விவரங்கள்.",
        "aliases": [
            "radiology tariff", "radiology charges", "xray tariff", "x-ray charges", "ct scan tariff", "ct scan charges",
            "mri charges", "mri tariff", "ultrasound tariff", "usg charges", "imaging charges", "xray charges", "scan charges",
            "ரேடியாலஜி கட்டணம்", "ஸ்கேன் கட்டணம்", "எக்ஸ்ரே கட்டணம்", "கதிரியக்கவியல் கட்டணம்"
        ],
        "negative_aliases": ["pacs", "pacs login", "viewer", "intercom", "phone", "extension"]
    },
    "DOC_TARIFF_PHYSIOTHERAPY": {
        "id": "DOC_TARIFF_PHYSIOTHERAPY",
        "title": "Physiotherapy Department Tariff",
        "url": "http://192.168.101.75:3000/files/Physiotherapy Tariff.pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Rehabilitation, electrotherapy, exercise therapy, traction, ultrasound therapy, and outpatient/inpatient physiotherapy session charges.",
        "description_ta": "மறுவாழ்வு சிகிச்சை, எலக்ட்ரோதெரபி, உடற்பயிற்சி சிகிச்சை மற்றும் பிசியோதெரபி அமர்வு கட்டண விவரங்கள்.",
        "aliases": [
            "physiotherapy tariff", "physiotherapy charges", "physio tariff", "physio charges", "physical therapy charges",
            "physiotherapy rates", "rehabilitation charges",
            "பிசியோதெரபி கட்டணம்", "உடற்பயிற்சி சிகிச்சை கட்டணம்"
        ],
        "negative_aliases": ["intercom", "phone", "extension"]
    },
    "DOC_TARIFF_OT_SURGERY": {
        "id": "DOC_TARIFF_OT_SURGERY",
        "title": "General Ward Surgery OT Tariff",
        "url": "http://192.168.101.75:3000/files/General Ward Surgery OT Tariff.pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Operation Theatre charges, surgeon fees, anaesthesia charges, and General Ward surgical package schedules (e.g. Local Package Rs.2000/-).",
        "description_ta": "அறுவை சிகிச்சை அரங்கு கட்டணம் (OT), மயக்க மருந்து கட்டணம் மற்றும் பொது வார்டு அறுவை சிகிச்சை தொகுப்பு கட்டணங்கள்.",
        "aliases": [
            "ot tariff", "surgery tariff", "operation theatre tariff", "ot charges", "surgery charges",
            "operation charges", "general ward surgery ot tariff", "surgical procedure charges", "theatre charges",
            "operation theatre charges", "surgical tariff",
            "அறுவை சிகிச்சை கட்டணம்", "ஆபரேஷன் தியேட்டர் கட்டணம்", "ஆபரேஷன் கட்டணம்"
        ],
        "negative_aliases": ["consent", "sammatham", "opputhal", "படிவம்", "ஒப்புதல்", "intercom", "phone", "extension"]
    },
    "DOC_TARIFF_ICU_ROOM": {
        "id": "DOC_TARIFF_ICU_ROOM",
        "title": "ICU and Special Ward Room Tariff",
        "url": "http://192.168.101.75:3000/files/ICU and Special Ward Room Tariff.pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Bed charges, nursing care rates, room rent per day for ICU, ICCU, NICU, PICU, Deluxe Rooms, AC Single Rooms, and Special Sharing Wards.",
        "description_ta": "தீவிர சிகிச்சைப் பிரிவு (ICU) படுக்கை கட்டணம், டீலக்ஸ் அறை, ஏசி தனி அறை மற்றும் சிறப்பு வார்டு அறை வாடகை கட்டண விவரங்கள்.",
        "aliases": [
            "room rent", "room tariff", "bed charges", "ward charges", "icu tariff", "icu charges",
            "special ward room tariff", "deluxe room rent", "single room rent", "sharing room charges",
            "icu bed charges", "room rates", "hospital room rent", "inpatient bed charges",
            "அறை வாடகை", "ஐசியூ கட்டணம்", "படுக்கை கட்டணம்", "வார்டு கட்டணம்", "ரூம் வாடகை"
        ],
        "negative_aliases": ["counselling", "checklist", "intercom", "phone", "extension"]
    },
    "DOC_TARIFF_OTHER_DEPTS": {
        "id": "DOC_TARIFF_OTHER_DEPTS",
        "title": "Other Departments Tariff",
        "url": "http://192.168.101.75:3000/files/Other Department Tariff.pdf",
        "category": "Tariff & Packages",
        "badge": "Tariff PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Dental, ENT, Ophthalmology, Dermatology, Casualty/Emergency, and miscellaneous clinical department consultation and procedural tariffs.",
        "description_ta": "பல் மருத்துவம், இஎன்டி, கண், தோல் மற்றும் அவசர சிகிச்சை உள்ளிட்ட இதர மருத்துவ துறைகளுக்கான கட்டண அட்டவணை.",
        "aliases": [
            "other department tariff", "other departments tariff", "other tariffs", "miscellaneous hospital tariffs",
            "dental tariff", "ent charges", "casualty charges tariff", "other dept tariff",
            "இதர கட்டணங்கள்", "பிற துறை கட்டணங்கள்"
        ],
        "negative_aliases": ["intercom", "phone", "extension"]
    },
    "CARD_PHARMACY_STOCK": {
        "id": "CARD_PHARMACY_STOCK",
        "title": "Pharmacy Live Stock Counters & Dispensary",
        "url": "./index.html#tariff-stock",
        "category": "Pharmacy & Stock",
        "badge": "Dispensary Live",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Live dispensing & reserve counters for Pharmacy: Drugs (139 items), In-Patient (77 items), Insurance (515 items), OP (90 items), Formulary 2025, and Free Drug List (NMC).",
        "description_ta": "மருந்தகத்தின் நேரடி விநியோகம் மற்றும் இருப்பு கவுண்டர்கள்: 139 முக்கிய மருந்துகள், உள்நோயாளி (77), காப்பீடு (515), வெளிநோயாளி (90) மற்றும் கையேடு 2025.",
        "aliases": [
            "pharmacy stock", "pharmacy live stock", "live pharmacy stock", "drug counters", "pharmacy stock counters",
            "dispensing counters", "pharmacy counters", "drug stock", "medicines stock", "drugs stock",
            "மருந்தக இருப்பு", "மருந்து இருப்பு விபரம்", "marunthu stock", "marunthagam stock"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "number", "login", "aosta", "blood", "ரத்தம்", "இரத்தம்", "consent", "படிவம்", "ஒப்புதல்"]
    },
    "DOC_DRUG_STORES_STOCK": {
        "id": "DOC_DRUG_STORES_STOCK",
        "title": "Drug Stores Stock Details",
        "url": "http://192.168.101.75:3000/files/Drug Stores Stock Details.pdf",
        "category": "Pharmacy & Stock",
        "badge": "139 Drugs PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Official Central Drug Store active stock list and inventory counts across 139 essential hospital medications, injections, and suture products.",
        "description_ta": "மத்திய மருந்து சேமிப்பு கிடங்கின் நேரடி 139 அத்தியாவசிய மருந்துகள் மற்றும் தையல் பொருட்கள் இருப்பு பட்டியல்.",
        "aliases": [
            "drug stores stock", "drug store stock", "139 drugs", "139 drugs stock", "essential drugs stock",
            "drug stores stock details", "central pharmacy drug stock", "central drug store stock", "139 essential drugs",
            "139 மருந்து இருப்பு", "மருந்து இருப்பு பட்டியல்", "மத்திய மருந்து இருப்பு"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "number", "login", "aosta", "blood", "ரத்தம்", "இரத்தம்"]
    },
    "DOC_IP_PHARMACY_STOCK": {
        "id": "DOC_IP_PHARMACY_STOCK",
        "title": "IP Pharmacy Stock Details",
        "url": "http://192.168.101.75:3000/files/IP Pharmacy Stock Details.pdf",
        "category": "Pharmacy & Stock",
        "badge": "77 Items PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "In-Patient pharmacy dispensary stock details and availability counts covering 77 active hospital medications and IV fluids.",
        "description_ta": "உள்நோயாளி மருந்தகத்தின் நேரடி 77 மருந்துகள் மற்றும் திரவங்கள் இருப்பு பட்டியல்.",
        "aliases": [
            "ip pharmacy stock", "inpatient pharmacy stock", "in patient pharmacy stock", "ip drug stock",
            "77 items pharmacy stock", "ip pharmacy stock details",
            "உள்நோயாளி மருந்தக இருப்பு", "உள்நோயாளி மருந்து இருப்பு"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "number", "login"]
    },
    "DOC_INSURANCE_PHARMACY_STOCK": {
        "id": "DOC_INSURANCE_PHARMACY_STOCK",
        "title": "Insurance Pharmacy Stock Details",
        "url": "http://192.168.101.75:3000/files/Insurance Pharmacy Stock Details.pdf",
        "category": "Pharmacy & Stock",
        "badge": "515 Items PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Comprehensive stock inventory of 515 approved insurance, CMCHIS, and TPA medications available at the hospital insurance pharmacy counter.",
        "description_ta": "முதலமைச்சரின் விரிவான மருத்துவ காப்பீட்டு திட்டம் மற்றும் டிபிஏ மருந்துகளுக்கான 515 இருப்பு பட்டியல்.",
        "aliases": [
            "insurance pharmacy stock", "tpa pharmacy stock", "insurance drug stock", "515 items pharmacy stock",
            "cmchis pharmacy stock", "insurance pharmacy stock details",
            "காப்பீட்டு மருந்தக இருப்பு", "காப்பீடு மருந்து இருப்பு"
        ],
        "negative_aliases": ["intercom", "phone", "extension", "number", "login"]
    },
    "DOC_OP_PHARMACY_STOCK": {
        "id": "DOC_OP_PHARMACY_STOCK",
        "title": "OP Pharmacy Stock Details",
        "url": "http://192.168.101.75:3000/files/Op Pharmacy Stock  Details.pdf",
        "category": "Pharmacy & Stock",
        "badge": "90 Items PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Outpatient pharmacy dispensing inventory details covering 90 vital oral, topical, and prescription drugs for daily OPD clinics.",
        "description_ta": "வெளிநோயாளி மருந்தகத்தின் 90 நேரடி மருந்து மாத்திரைகள் மற்றும் மருந்து இருப்பு விவரம்.",
        "aliases": [
            "op pharmacy stock", "opd pharmacy stock", "outpatient pharmacy stock", "op drug stock",
            "90 items pharmacy stock", "op pharmacy stock details",
            "வெளிநோயாளி மருந்தக இருப்பு", "வெளிநோயாளி மருந்து இருப்பு"
        ],
        "negative_aliases": ["token", "lineloom", "intercom", "phone", "extension", "number", "login"]
    },
    "DOC_HOSPITAL_FORMULARY_2025": {
        "id": "DOC_HOSPITAL_FORMULARY_2025",
        "title": "Hospital Formulary - 2025",
        "url": "http://192.168.101.75:3000/files/Hospital Formulary - 2025.pdf",
        "category": "Pharmacy & Stock",
        "badge": "Formulary 2025",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Official MAPIMS Hospital Drug Formulary 2025 approved by the Pharmacy and Therapeutics Committee.",
        "description_ta": "மருந்தியல் மற்றும் சிகிச்சை குழுவால் அங்கீகரிக்கப்பட்ட அதிகாரப்பூர்வ மருத்துவமனை மருந்து கையேடு 2025.",
        "aliases": [
            "hospital formulary 2025", "hospital formulary", "formulary 2025", "drug formulary 2025", "aph formulary",
            "மருந்து கையேடு 2025", "மருந்தியல் கையேடு 2025"
        ],
        "negative_aliases": ["intercom", "phone", "extension"]
    },
    "DOC_FREE_DRUG_LIST_NMC": {
        "id": "DOC_FREE_DRUG_LIST_NMC",
        "title": "Free Drug List (NMC)",
        "url": "http://192.168.101.75:3000/files/Pharmacy_Updated_11.05.26.pdf",
        "category": "Pharmacy & Stock",
        "badge": "NMC Free Drugs",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "National Medical Commission (NMC) mandatory updated list of essential medicines dispensed free of cost to hospital patients (Updated 11.05.26).",
        "description_ta": "தேசிய மருத்துவ ஆணையத்தின் (NMC) வழிகாட்டுதலின்படி நோயாளிகளுக்கு இலவசமாக வழங்கப்படும் அத்தியாவசிய மருந்துகள் பட்டியல்.",
        "aliases": [
            "free drug list", "nmc free drug list", "nmc drug list", "free medicines list", "free drug list nmc",
            "pharmacy updated 11.05.26", "free drugs nmc",
            "இலவச மருந்து பட்டியல்", "என்எம்சி இலவச மருந்துகள்", "இலவச மருந்துகள்"
        ],
        "negative_aliases": ["intercom", "phone", "extension"]
    },
    "CARD_GENERAL_STORE": {
        "id": "CARD_GENERAL_STORE",
        "title": "General Store Inventory & Surgical Kits",
        "url": "./index.html#tariff-stock",
        "category": "General Store",
        "badge": "Store Counters",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Live inventory counters for hospital General Store: Active Inventory (738 items), Stationery items (160 items), and Surgical & CSSD Kits (93 items).",
        "description_ta": "மருத்துவமனை பொது சேமிப்பு கிடங்கு இருப்பு: 738 பொது பொருட்கள், 160 எழுதுபொருட்கள் மற்றும் 93 அறுவை சிகிச்சை கிட்கள்.",
        "aliases": [
            "general store", "hospital general store", "general store stock", "general store inventory",
            "store inventory", "stationery stock", "surgical kits stock", "cssd store", "store stock",
            "பொது சேமிப்பு கிடங்கு", "ஸ்டோர் இருப்பு", "பொது ஸ்டோர்", "ஸ்டோர் விவரம்"
        ],
        "negative_aliases": ["purchase process", "indent form", "intercom", "phone", "extension", "number"]
    },
    "DOC_INVENTORY_STOCK_2024": {
        "id": "DOC_INVENTORY_STOCK_2024",
        "title": "Inventory Stock Details 2024",
        "url": "http://192.168.101.75:3000/files/Inventory Stock Details 2024.pdf",
        "category": "General Store",
        "badge": "738 Items PDF",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Complete PDF inventory ledger of all 738 items in the hospital general store, including surgical instruments, forceps, and consumables.",
        "description_ta": "பொது சேமிப்பு கிடங்கில் உள்ள 738 அறுவை சிகிச்சை கருவிகள் மற்றும் மருத்துவ பொருட்களின் முழுமையான இருப்பு அறிக்கை.",
        "aliases": [
            "inventory stock details 2024", "inventory stock details", "inventory stock pdf", "general store inventory pdf",
            "store inventory pdf", "738 inventory items", "inventory stock",
            "ஸ்டோர் இருப்பு விவரம்", "ஸ்டோர் இருப்பு அறிக்கை"
        ],
        "negative_aliases": ["purchase process", "indent form", "intercom", "phone", "extension"]
    },

    # Verified Clinical Governance & Committee Directory
    "DIR_MANUALS": {
        "id": "DIR_MANUALS",
        "title": "Hospital Accreditation Manuals Hub (NABH 5th & 6th Edition)",
        "url": "./manuals.html",
        "category": "Manuals & SOPs",
        "badge": "Manuals Hub",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Comprehensive directory of 266 official NABH 5th & 6th Edition accreditation manuals, chapter standards (AAC, COP, MOM, PRE, PSQ, HIC, FMS, HRM, IMS, ROM), departmental SOPs, and clinical protocols.",
        "description_ta": "266 அதிகாரப்பூர்வ NABH கையேடுகள், துறை வாரியான SOP மற்றும் மருத்துவ நெறிமுறைகளின் முழுமையான தொகுப்பு.",
        "aliases": [
            "manuals", "manual", "open manuals", "open manual", "hospital manuals", "nabh manuals", "quality manuals",
            "manuals hub", "manuals directory", "manual directory", "hospital sops", "hospital sop", "departmental manuals",
            "clinical manuals", "accreditation manuals", "clinical protocols", "hospital manuals hub", "all manuals",
            "nabh documents", "sops", "sop", "nabh sop", "quality sop", "quality committee manuals",
            "மருத்துவமனை கையேடுகள்", "கையேடு", "கையேடுகள்", "விதிமுறைகள்", "kaiyedu", "kaiyedugal", "sops list", "list of manuals"
        ],
        "negative_aliases": ["teaching", "user creation", "doctor id", "item creation"]
    },
    "HUB_CORE_QUALITY": {
        "id": "HUB_CORE_QUALITY",
        "title": "Core Quality Committee Hub",
        "url": "./index.html#quality",
        "category": "Clinical Governance",
        "badge": "Quality Hub",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Central governance portal for NABH / JCI accreditation governance, hospital quality committee (QC), chapter standards, clinical manuals, and committee meeting minutes.",
        "description_ta": "மருத்துவமனை தரக் கட்டுப்பாடு குழு (Quality Committee), NABH நெறிமுறைகள், கையேடுகள் மற்றும் கூட்ட அறிக்கைகளுக்கான பிரதான தளம்.",
        "aliases": [
            "core quality committee hub", "core quality committee", "quality committee hub", "quality hub",
            "core quality", "quality committee", "quality governance", "nabh governance", "quality committee hub 2026",
            "தரக் கட்டுப்பாட்டு மையம்", "தரக்கட்டுப்பாடு"
        ],
        "negative_aliases": []
    },
    "DIR_COMMITTEES": {
        "id": "DIR_COMMITTEES",
        "title": "APH Hospital Committees & MOM Directory",
        "url": "./comitee.html",
        "category": "Committees & MOM",
        "badge": "Governance Hub",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Central registry of hospital governance charters, quality committees, HICC, safety committees, and Minutes of Meeting (MOM).",
        "description_ta": "மருத்துவமனை நிர்வாக குழுக்கள், தரக் கட்டுப்பாடு குழு (Quality Committee), மற்றும் கூட்ட அறிக்கைகள் (MOM) தளம்.",
        "aliases": [
            "committee", "committees", "comitee", "commitee", "open committee", "open comitee", "open committees",
            "list of commitee", "list of committee", "list of committees", "committee list", "committees list",
            "hospital committees", "hospital committee", "hospital committee list", "hospital committees list",
            "committee members", "committee charter", "committee charters", "governance committees",
            "committee directory", "committees directory", "committee hub", "committees hub",
            "mom", "moms", "minutes of meeting", "meeting minutes", "mom directory", "minutes of meeting directory",
            "committee calendar", "mock drill calendar", "committee scheduled calendar",
            "hicc committee", "safety committee", "quality committee", "cpr committee", "btc committee", "cac committee",
            "மருத்துவமனை குழுக்கள்", "குழு", "குழுக்கள்", "குழுக்கள் பட்டியல்", "கூட்ட அறிக்கை", "நிர்வாகக் குழு"
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
    },

    # 12. Quick Shortcuts Dock & Individual Shortcut Tools
    "SECTION_QUICK_SHORTCUTS": {
        "id": "SECTION_QUICK_SHORTCUTS",
        "title": "Quick Shortcuts Dock",
        "url": "./index.html#quick-shortcuts-dock",
        "category": "Quick Access Dock",
        "badge": "8 Live Shortcuts",
        "intent_type": SearchIntent.NAVIGATE_SECTION,
        "description": "Floating Quick-Action Shortcuts Dock featuring 8 essential hospital links: Intercom Hotline, 24h Duty Roster, Blood Bank Stock, Email Directory, Medical Abbreviations, Billing Manual, Nursing Manual, and Replace PDF Server.",
        "description_ta": "8 முக்கிய மருத்துவமனை இணைப்புகளைக் கொண்ட விரைவு குறுக்குவழிப் பலகை (இன்டர்காம், 24 மணி நேரப் பணி விவரம், ரத்த வங்கி இருப்பு, மின்னஞ்சல் பட்டியல், சுருக்கக் குறியீடுகள், கையேடுகள்).",
        "aliases": [
            "quick shortcuts", "quick shortcut", "quicks shortcut", "quicks shortcuts", "quick access shortcuts",
            "shortcuts dock", "shortcuts panel", "quick links", "shortcuts", "shortcut",
            "emergency and hospital links", "floating dock", "side shortcuts", "side dock",
            "quick action dock", "dock shortcuts", "hospital shortcuts",
            "விரைவு குறுக்குவழி", "குறுக்குவழிகள்", "விரைவு இணைப்புகள்", "குறுக்கு வழி",
            "kurukku vazhi", "viraivu kurukku vazhi", "shortcut panel", "quicks"
        ],
        "negative_aliases": []
    },
    "DOC_STAFF_EMAIL_DIR": {
        "id": "DOC_STAFF_EMAIL_DIR",
        "title": "Official Staff Email Directory",
        "url": "http://192.168.101.75:3000/files/email.pdf",
        "category": "Quick Shortcuts",
        "badge": "Staff Directory",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Comprehensive internal directory of official institutional @mapims.edu.in email addresses for hospital doctors, faculty, and administrative departments.",
        "description_ta": "மருத்துவர்கள், பேராசிரியர்கள் மற்றும் நிர்வாகத் துறைகளுக்கான அதிகாரப்பூர்வ மின்னஞ்சல் முகவரிகளின் பட்டியல்.",
        "aliases": [
            "staff email directory", "email list", "email directory", "hospital email list", "staff email list",
            "official email list", "email pdf", "hospital email directory", "doctors email list",
            "மின்னஞ்சல் பட்டியல்", "மின்னஞ்சல் முகவரி பட்டியல்", "மின்னஞ்சல் டைரக்டரி", "staff minnanjal"
        ],
        "negative_aliases": ["form", "request", "படிவம்", "creation"]
    },
    "DOC_ABBREVIATION_GUIDE": {
        "id": "DOC_ABBREVIATION_GUIDE",
        "title": "Approved Medical Abbreviations List",
        "url": "http://192.168.101.75:3000/files/Abrrevation.pdf",
        "category": "Quick Shortcuts",
        "badge": "Clinical Guide",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Hospital approved medical, clinical, pharmaceutical, and diagnostic abbreviations reference guide.",
        "description_ta": "மருத்துவமனையில் அனுமதிக்கப்பட்ட மருத்துவ, மருந்தியல் மற்றும் நோய் கண்டறிதல் சுருக்கக் குறியீடுகளின் அதிகாரப்பூர்வ கையேடு.",
        "aliases": [
            "medical abbreviations", "abbreviations", "abbreviation", "abbreviation guide", "medical abbreviation list",
            "clinical abbreviations", "approved abbreviations", "hospital abbreviations",
            "மருத்துவ சுருக்கங்கள்", "சுருக்கக் குறியீடுகள்", "abbreviation list"
        ],
        "negative_aliases": []
    },
    "DOC_BILLING_MANUAL": {
        "id": "DOC_BILLING_MANUAL",
        "title": "User Billing Manual",
        "url": "http://192.168.101.75:3000/files/billingmanual.pdf",
        "category": "Quick Shortcuts",
        "badge": "User Manual",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Standard operating user manual for hospital billing, cashier desks, inpatient settlements, and payment vouchers.",
        "description_ta": "மருத்துவமனை பில்லிங், காசாளர் கவுண்டர் மற்றும் கட்டணம் செலுத்துதல் வழிகாட்டி கையேடு.",
        "aliases": [
            "billing manual", "user billing manual", "billing guide", "hospital billing manual", "cashier manual",
            "பில்லிங் கையேடு", "பில்லிங் வழிகாட்டி", "billing user manual"
        ],
        "negative_aliases": ["tariff", "stock", "rate", "cost", "price"]
    },
    "DOC_NURSING_MANUAL": {
        "id": "DOC_NURSING_MANUAL",
        "title": "Nursing Operations Manual",
        "url": "http://192.168.101.75:3000/files/nursingmanual.pdf",
        "category": "Quick Shortcuts",
        "badge": "User Manual",
        "intent_type": SearchIntent.FIND_DOCUMENT,
        "description": "Comprehensive nursing procedural manual covering inpatient care, medication administration, and clinical bedside standards.",
        "description_ta": "நர்சிங் நடைமுறைகள், மருந்துகள் வழங்குதல் மற்றும் நோயாளி பராமரிப்பு வழிகாட்டி கையேடு.",
        "aliases": [
            "nursing manual", "nursing operations manual", "nursing user manual", "nursing guide",
            "நர்சிங் கையேடு", "செவிலியர் கையேடு", "nursing sop manual"
        ],
        "negative_aliases": []
    },
    "APP_REPLACE_PDF": {
        "id": "APP_REPLACE_PDF",
        "title": "Replace / Upload PDF Portal",
        "url": "http://192.168.101.75:8000/server",
        "category": "Quick Shortcuts",
        "badge": "Admin Server",
        "intent_type": SearchIntent.OPEN_APPLICATION,
        "description": "Administrative document upload and replacement portal for managing intranet PDF files.",
        "description_ta": "இன்ட்ராநெட் பிடிஎஃப் ஆவணங்களை மாற்றுவதற்கும் பதிவேற்றுவதற்குமான நிர்வாக போர்டல்.",
        "aliases": [
            "replace pdf", "replace pdf portal", "upload pdf server", "upload pdf portal", "admin replace pdf",
            "pdf replacement server", "பிடிஎஃப் மாற்று சர்வர்"
        ],
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
    # Shortcuts & Quick Access
    "quicks shortcut": "quick shortcuts dock",
    "quicks shortcuts": "quick shortcuts dock",
    "quick shortcut": "quick shortcuts dock",
    "shortcuts": "quick shortcuts dock",
    "shortcut": "quick shortcuts dock",
    "kurukku vazhi": "quick shortcuts dock",
    "kurukku vazhikal": "quick shortcuts dock",
    "விரைவு குறுக்குவழி": "quick shortcuts dock",
    "குறுக்குவழிகள்": "quick shortcuts dock",
    "குறுக்கு வழி": "quick shortcuts dock",

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

    # Medicolegal & Consent Forms
    "opputhal padivam": "consent form",
    "oputhal padivam": "consent form",
    "oppudhal padivam": "consent form",
    "sammatha padivam": "consent form",
    "sammatham padivam": "consent form",
    "samatham padivam": "consent form",
    "ஒப்புதல் படிவம்": "consent form",
    "சம்மத படிவம்": "consent form",
    "ஒப்புதல் படிவங்கள்": "consent forms",
    "aruvai sigichai sammatham": "surgery consent",
    "aruvai sikitsai sammatham": "surgery consent",
    "aruvai sigichai opputhal": "surgery consent",
    "aruvai sammatham": "surgery consent",
    "aruvai padivam": "surgery consent",
    "அறுவை சிகிச்சை ஒப்புதல்": "surgery consent",
    "அறுவை சிகிச்சை சம்மதம்": "surgery consent",
    "kuzhanthai consent": "pediatric consent",
    "kulandhai consent": "pediatric consent",
    "pillai consent": "pediatric consent",
    "குழந்தை ஒப்புதல்": "pediatric consent",
    "குழந்தை சம்மதம்": "pediatric consent",
    "ratha vangi consent": "blood transfusion consent",
    "iratha vangi consent": "blood transfusion consent",
    "ரத்த மாற்று ஒப்புதல்": "blood transfusion consent",
    "ரத்த தான ஒப்புதல்": "blood transfusion consent",
    "dama consent": "dama consent",
    "veliye poga consent": "dama consent",
    "hospital vittu poga consent": "dama consent",
    "maruppu form": "not willing consent",
    "maruppu padivam": "not willing consent",
    "chikitsai maruppu": "not willing consent",
    "treatment vendam consent": "not willing consent",
    "thevailla consent": "not willing consent",
    "viruppamillai consent": "not willing consent",
    "சிகிச்சை மறுப்பு": "not willing consent",
    "விருப்பமில்லா படிவம்": "not willing consent",
    "admission consent": "admission consent",
    "serkai sammatham": "admission consent",
    "serkai padivam": "admission consent",
    "admit aaga consent": "admission consent",
    "சேர்க்கை ஒப்புதல்": "admission consent",
    "visiting doctor form": "visiting consultant requisition",
    "surrogate consent": "surrogate consent",

    # Committees & Governance
    "quality committee members": "quality committee members governance charters",
    "குழு": "committee charter mom governance",
    "charter": "committee charter mom governance",

    # Telephony
    "tholaipesi": "intercom telephone phone extension call",
    "தொலைபேசி": "intercom telephone phone extension call",
    "இன்டர்காம்": "intercom telephone phone extension call",
    "இணைப்பு": "extension intercom call phone",

    # Clinical Procedures & Knowledge
    "needle stick": "needle stick injury protocol sharps ipc",
    "needle stick injury": "needle stick injury protocol sharps ipc",
    "oosi kuthu": "needle stick injury protocol sharps",
    "oosi": "needle injection stick",
    "kuthu": "puncture prick stick injury",
    "ஊசி குத்து": "needle stick injury protocol sharps",
    "ஊசி": "needle injection stick",
    "காயம்": "injury wound protocol",
    "sharps injury": "needle stick injury protocol",
    "hand hygiene": "hand hygiene moments wash rub nabh cop",
    "kai sugatharam": "hand hygiene moments wash rub",
    "கை சுகாதாரம்": "hand hygiene moments wash rub",
    "transfusion reaction": "blood transfusion reaction adverse cop",
    "ரத்த மாற்று எதிர்வினை": "blood transfusion reaction adverse",
    "ரத்த மாற்று": "blood transfusion component",
    "எதிர்வினை": "reaction adverse complication",
    "waste segregation": "biomedical waste segregation colour coding",
    "biomedical waste": "biomedical waste segregation colour coding",
    "கழிவு மேலாண்மை": "biomedical waste segregation colour coding",
    "நோட்டீஸ் காலம்": "resignation notice period relieving",
    "நோட்டீஸ் பீரியட்": "resignation notice period relieving",
    "ராஜினாமா நோட்டீஸ்": "resignation notice period relieving",

    # Common Forms & Clinical Indents
    "போதை மருந்து படிவம்": "narcotic drugs form register",
    "போதை மருந்து": "narcotic drugs form",
    "மயக்க மருந்து படிவம்": "narcotic drugs form",
    "உணவு டோக்கன்": "food token requisition form",
    "சாப்பாடு டோக்கன்": "food token requisition form",
    "unavu token": "food token requisition form",
    "theevira sigichai checklist": "icu casesheet checklist",
    "ward shifting padivam": "icu checklist ward shifting",
    "வார்டு மாற்றம்": "icu checklist ward shifting",
    "தீவிர சிகிச்சை சரிபார்ப்பு": "icu casesheet checklist",
    "மருந்து ஒவ்வாமை படிவம்": "adr form adverse drug reaction",
    "விபத்து அறிக்கை": "incident report form",
    "நிகழ்வு அறிக்கை": "incident report form",
    "கட்டுப்படுத்தப்பட்ட ஆன்டிபயாடிக்": "restricted antibiotic form",
    "பொது படிவங்கள்": "common forms hub clinical",
    "மருத்துவ படிவங்கள்": "common forms hub clinical",
    "உயர் எச்சரிக்கை மருந்துகள்": "high alert medications",
    "நோயாளி ஆலோசனை படிவம்": "counselling documentation form",
    # HR Forms & Cadre Policies
    "பதவி உயர்வு": "promotion form",
    "பதவி உயர்வு படிவம்": "promotion form",
    "pathavi uyartvu": "promotion form",
    "pathavi uyartvu padivam": "promotion form",
    "பயிற்சி படிவம்": "staff training feedback form",
    "பயிற்சி பின்னூட்டம்": "staff training feedback form",
    "payirchi form": "staff training feedback form",
    "payirchi feedback": "staff training feedback form",
    "செயல்திறன் கொள்கை": "pms policy",
    "செயல்திறன் மேலாண்மை": "pms policy",
    "எச்.ஆர் படிவங்கள்": "hr forms hub",
    "எச் ஆர் படிவங்கள்": "hr forms hub",
    "பணியாளர் படிவங்கள்": "hr forms hub",
    "மனித வள படிவங்கள்": "hr forms hub",
    "hr padivangal": "hr forms hub",
    "hr padivam": "hr forms hub",
    "ஜூனியர் ரெசிடென்ட்": "junior resident policy",
    "உறைவிட மருத்துவர் கொள்கை": "junior resident policy",
    "மருத்துவ அலுவலர் கொள்கை": "cmo chief medical officer policy",
    "மருத்துவ உரிமை": "clinical privileges general medicine",
    "மயக்கவியல் மருத்துவ உரிமை": "clinical privileges anaesthesia",
    "காது மூக்கு தொண்டை உரிமை": "clinical privileges ent",
    # IT Forms & Hardware Requisitions
    "ஐடி படிவங்கள்": "it forms hub",
    "தகவல் தொழில்நுட்ப படிவங்கள்": "it forms hub",
    "it padivangal": "it forms hub",
    "it padivam": "it forms hub",
    "கணினி படிவம்": "system request form",
    "கணினி கோரிக்கை படிவம்": "system request form",
    "பிரிண்டர் படிவம்": "printer request form",
    "அச்சக படிவம்": "printer request form",
    "அச்சுப்பொறி படிவம்": "printer request form",
    "மின்னஞ்சல் படிவம்": "official email id request form",
    "மின்னஞ்சல் கோரிக்கை": "official email id request form",
    "சிம் படிவம்": "sim cug request form",
    "சிம் கார்டு படிவம்": "sim cug request form",
    "சிம் கார்டு கோரிக்கை": "sim cug request form",
    "வைஃபை படிவம்": "employee wifi request form",
    "வைஃபை கோரிக்கை": "employee wifi request form",
    "மருத்துவர் ஐடி படிவம்": "doctor id creation form",
    "பொருள் உருவாக்கம்": "item creation in his"
}

# =========================================================================
# 2. INTENT CLASSIFIER & QUERY NORMALIZER
# =========================================================================
HOSPITAL_VOCABULARY = set([
    # Applications & Systems
    'his', 'backbone', 'aosta', 'hrms', 'pruworks', 'pacs', 'medsynapse',
    'mrd', 'mhc', 'lineloom', 'barcode', 'counselling', 'counseling', 'eyecamp', 'gencl',
    'ticketing', 'checklist',
    # App Descriptors & Actions
    'open', 'launch', 'login', 'portal', 'workstation', 'viewer', 'software',
    'application', 'webapplication', 'website', 'system', 'access',
    # Ticketing / Maintenance / Facility
    'repair', 'fixing', 'maintenance', 'electrical', 'housekeeping', 'laundry',
    'breakdown', 'complaint', 'ticket', 'cleaning', 'computer', 'hardware',
    # HIS & Clinical Workflows
    'patient', 'details', 'registration', 'admission', 'discharge', 'billing',
    'indents', 'stores', 'pharmacy', 'dispensing', 'doctor', 'consultation', 'consultant',
    'review', 'emergency', 'staff', 'creation',
    # HRMS & Employee
    'salary', 'payslip', 'leave', 'attendance', 'biometric', 'punch',
    'resignation', 'relieving', 'promotion', 'promotions', 'performer', 'performers',
    'performance', 'privilege', 'privileges', 'privileging', 'appraisal', 'appraisals',
    'resident', 'residents', 'faculty', 'training',
    # Radiology
    'xray', 'scan', 'dicom', 'radiology',
    # Clinical & Safety Protocols
    'code', 'blue', 'red', 'pink', 'cpr', 'needle', 'stick', 'injury', 'waste',
    'segregation', 'biomedical', 'resuscitation', 'protocol', 'policy', 'manual',
    'sop', 'sops', 'nabh', 'hicc', 'infection', 'control', 'blood', 'transfusion',
    'hand', 'hygiene', 'drill', 'audit', 'tariff', 'consent', 'surgery', 'pediatric',
    'paediatric', 'surrogate', 'dama', 'lama', 'refusal', 'willing', 'padivam',
    'opputhal', 'sammatham',
    'committee', 'committees', 'governance', 'charter',
    'interaction', 'interactions', 'incident', 'incidents', 'abbreviation', 'abbreviations',
    'narcotic', 'narcotics', 'antibiogram', 'antibiograms',
    # Telephony & Docs
    'intercom', 'extension', 'directory', 'telephone', 'phone', 'circular', 'circulars',
    'form', 'forms', 'requisition', 'holiday', 'stock', 'stocks', 'roster', 'rosters',
    'police', 'hotline', 'hotlines', 'bulletin', 'bulletins', 'violet',
    'printer', 'printers', 'toner', 'desktop', 'item', 'wifi', 'cug', 'sim',
    'shortcut', 'shortcuts', 'quick', 'dock'
])

TYPO_FIXES = {
    'opn': 'open',
    'hiss': 'his',
    'quicks': 'quick',
    'shorcut': 'shortcut',
    'shortcurt': 'shortcut',
    'shotcut': 'shortcut',
    'sortcut': 'shortcut',
    'shrotcut': 'shortcut',
    'foam': 'form',
    'foarm': 'form',
    'inercom': 'intercom',
    'leavu': 'leave',
    'vinnapam': 'vinnappam',
    'vidumura': 'vidumurai',
    'rajinamaa': 'rajinama',
    'billinh': 'billing',
    'billin': 'billing',
    'paitent': 'patient',
    'paitents': 'patients',
    'repar': 'repair',
    'fixin': 'fixing',
    'maintenence': 'maintenance',
    'maintenace': 'maintenance',
    'electircal': 'electrical',
    'husekeeping': 'housekeeping',
    'lundry': 'laundry',
    'salery': 'salary',
    'atendance': 'attendance',
    'checlist': 'checklist',
    'barcod': 'barcode',
    'linelom': 'lineloom',
    'eyecmp': 'eyecamp',
    'pharamcy': 'pharmacy',
    'medsynaps': 'medsynapse',
    'pruwork': 'pruworks',
    'backboen': 'backbone',
    'xrey': 'xray',
    'softwer': 'software',
    'aplication': 'application',
    'webaplication': 'webapplication',
    'commitee': 'committee',
    'comitee': 'committee',
    'comittee': 'committee',
    'commite': 'committee',
    'concent': 'consent',
    'consen': 'consent',
    'consnt': 'consent',
    'commset': 'consent',
    'conset': 'consent',
    'sergery': 'surgery',
    'suregry': 'surgery',
    'sugery': 'surgery',
    'surgry': 'surgery',
    'pedatric': 'pediatric',
    'paedatric': 'paediatric',
    'paditric': 'pediatric',
    'peadiatric': 'pediatric',
    'transfution': 'transfusion',
    'transfuson': 'transfusion',
    'trasfusion': 'transfusion',
    'damma': 'dama',
    'damaa': 'dama',
    'wiling': 'willing',
    'willin': 'willing',
    'admisison': 'admission',
    'admissin': 'admission',
    'admision': 'admission',
    'visitin': 'visiting',
    'consultent': 'consultant',
    'consaltant': 'consultant',
    'surrugate': 'surrogate',
    'surogate': 'surrogate',
    'oputhal': 'opputhal',
    'oppudhal': 'opputhal',
    'sammatha': 'sammatham',
    'samatham': 'sammatham',
    'narcotik': 'narcotic',
    'tokan': 'token',
    'tokn': 'token',
    'reviw': 'review',
    'reveiw': 'review',
    'antibiogramm': 'antibiogram',
    'antiboitic': 'antibiotic',
    'antiobiotic': 'antibiotic',
    'antibioitcs': 'antibiotics',
    'councelling': 'counselling',
    'counceling': 'counselling',
    'daycar': 'daycare',
    'casheet': 'casesheet',
    'caseshet': 'casesheet',
    'promtion': 'promotion',
    'promation': 'promotion',
    'performr': 'performer',
    'nonperformer': 'non performer',
    'apprasal': 'appraisal',
    'apraisal': 'appraisal',
    'privilage': 'privilege',
    'privilages': 'privileges',
    'priviledge': 'privilege',
    'priviledges': 'privileges',
    'feedbak': 'feedback',
    'fedback': 'feedback',
    'recrutment': 'recruitment',
    'recruitmnt': 'recruitment',
    'teching': 'teaching',
    'prnter': 'printer',
    'prntr': 'printer',
    'wirless': 'wireless',
    'wify': 'wifi',
    'kannini': 'kanini',
    'desktp': 'desktop',
    'computr': 'computer',
    'systm': 'system',
    'emial': 'email',
    'maill': 'mail',
    'cuug': 'cug'
}

def fuzzy_normalize_token(token: str) -> str:
    t = token.lower().strip()
    if not t:
        return token
    if t in TYPO_FIXES:
        return TYPO_FIXES[t]
    if t in HOSPITAL_VOCABULARY or len(t) <= 3:
        return t

    # Length filter: candidate must be within abs(len) <= 2
    candidates = [w for w in HOSPITAL_VOCABULARY if abs(len(w) - len(t)) <= 2]
    # First letter match or transposition of first two letters
    candidates = [w for w in candidates if w[0] == t[0] or (len(t) > 1 and len(w) > 1 and w[:2] == t[1] + t[0])]
    if not candidates:
        return t

    cutoff = 0.82 if len(t) <= 4 else (0.76 if len(t) <= 6 else 0.74)
    matches = difflib.get_close_matches(t, candidates, n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    return t

def fuzzy_normalize_query(text: str) -> str:
    if not text:
        return text
    words = re.findall(r'[\w\u0B80-\u0BFF]+|[^\w\s\u0B80-\u0BFF]+|\s+', text)
    result = []
    for w in words:
        if re.match(r'^[a-zA-Z]+$', w):
            result.append(fuzzy_normalize_token(w))
        else:
            result.append(w)
    return ''.join(result)

def clean_and_tokenize(text):
    if not text:
        return set()
    cleaned = re.sub(r'[^\w\s\u0B80-\u0BFF]', ' ', text.lower())
    raw_tokens = cleaned.split()
    return {fuzzy_normalize_token(t) for t in raw_tokens}

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

def is_telephony_query(text):
    t_lower = text.lower()
    return any(k in t_lower for k in [
        "intercom", "inercom", "extension", "ext", "exts", "phone", "telephone",
        "call", "calling", "dial", "hotline", "tholaipesi", "தொலைபேசி", "இன்டர்காம்",
        "எக்ஸ்டென்ஷன்", "இணைப்பு"
    ])

def classify_search_intent(query):
    """
    Deterministically classifies query intent into explicit categories:
    OPEN_APPLICATION, OPEN_FORM, FIND_DOCUMENT, ANSWER_FROM_MANUAL,
    FIND_COMMITTEE, FIND_DIRECTORY, NAVIGATE_SECTION, UNKNOWN.
    """
    q_lower = query.lower().strip()
    q_norm = fuzzy_normalize_query(q_lower.replace("-", " "))
    tokens = clean_and_tokenize(q_norm)

    # 1. Committee Search
    if any(k in q_norm for k in [
        "committee", "committees", "charter", "charters", "minutes of meeting",
        "governance", "குழு", "கூட்ட அறிக்கை", "meeting minutes"
    ]) or bool(tokens & {"mom", "moms"}):
        return SearchIntent.FIND_COMMITTEE

    # 2. Telephony / Intercom Directory
    if any(k in q_norm for k in [
        "intercom", "inercom", "extension", "ext", "exts", "phone", "telephone",
        "call", "calling", "dial", "hotline", "tholaipesi", "தொலைபேசி", "இன்டர்காம்",
        "எக்ஸ்டென்ஷன்", "இணைப்பு"
    ]):
        return SearchIntent.FIND_DIRECTORY

    # 3. Resignation / Relieving Intent
    if any(k in q_norm for k in [
        "resignation", "resign", "relieving", "notice period", "exit clearance",
        "no dues", "nodues", "rajinama", "raajinaama", "பணி விலகல்", "ராஜினாமா"
    ]):
        return SearchIntent.FIND_DOCUMENT

    # 4. Form Requisition Intent (Explicit request for PDF / form to fill)
    is_form_word = bool(tokens & {"form", "forms", "padivam", "padivangal", "படிவம்", "படிவங்கள்", "vinnappam", "விண்ணப்பம்", "requisition"})
    is_creation_intent = any(k in q_norm for k in [
        "user creation", "doctor id", "item creation", "id creation", "account creation",
        "access venum", "access vendum", "creation in his"
    ])
    if (is_form_word or is_creation_intent) and not any(k in q_norm for k in ["open pacs", "open mrd", "open hrms"]):
        return SearchIntent.OPEN_FORM

    # 5. Core Application Launch Intent
    is_app_keyword = any(k in q_norm for k in [
        "his", "aosta", "backbone", "hrms", "pruworks", "pacs", "medsynapse",
        "mrd", "mhc", "master health", "lineloom", "barcode", "counselling",
        "eye camp", "eyecamp", "checklist", "gencl", "ticketing",
        "front office", "front desk",
        "ஹெச்ஐஎஸ்", "ஹிஸ்"
    ]) or bool(tokens & {"his", "hrms", "pacs", "mrd", "mhc", "lineloom", "barcode", "eyecamp", "checklist", "gencl", "ticketing"})
    is_launch_action = any(k in q_norm for k in [
        "open", "launch", "login", "portal", "workstation", "viewer", "software",
        "app", "application", "webapplication", "web application", "website", "tool", "system",
        "enga", "yenga", "thira", "திற",
        "திறக்கவும்", "உள்நுழைவு", "லாகின்",
        "paakanum", "பார்க்க"
    ]) or "apply leave" in q_norm or "leave apply" in q_norm

    if is_app_keyword and (is_launch_action or q_norm in ["his", "hrms", "pacs", "mrd", "mhc", "lineloom"]):
        if not is_form_word and not is_creation_intent:
            return SearchIntent.OPEN_APPLICATION

    # 6. Clinical Manual / SOP / Guideline Search
    if any(k in q_norm for k in [
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
    q_norm = fuzzy_normalize_query(q_lower.replace("-", " "))
    tokens = clean_and_tokenize(q_norm)

    # 0a. Quick Shortcuts Dock Queries
    if any(k in q_norm for k in [
        "quick shortcut", "quick shortcuts", "quicks shortcut", "quicks shortcuts",
        "shortcuts dock", "shortcuts panel", "quick links", "emergency and hospital links",
        "side shortcuts", "floating dock", "side dock", "dock shortcuts", "hospital shortcuts",
        "விரைவு குறுக்குவழி", "குறுக்குவழிகள்", "விரைவு இணைப்புகள்", "குறுக்கு வழி",
        "kurukku vazhi", "viraivu kurukku vazhi", "shortcut panel"
    ]) or q_norm in ["shortcuts", "shortcut", "quick shortcuts dock", "quicks shortcut dock"]:
        return RESOURCE_REGISTRY["SECTION_QUICK_SHORTCUTS"]

    # 0b. Staff Email Directory PDF
    if any(k in q_norm for k in [
        "staff email directory", "email list", "email directory", "hospital email list", "staff email list",
        "official email list", "email pdf", "hospital email directory", "doctors email list",
        "மின்னஞ்சல் பட்டியல்", "மின்னஞ்சல் முகவரி பட்டியல்", "மின்னஞ்சல் டைரக்டரி", "staff minnanjal"
    ]) and not any(k in q_norm for k in ["form", "request", "படிவம்", "creation", "id venum", "id request"]):
        return RESOURCE_REGISTRY["DOC_STAFF_EMAIL_DIR"]

    # 0c. Medical Abbreviations Register
    if any(k in q_norm for k in [
        "medical abbreviations", "abbreviations", "abbreviation", "abbreviation guide", "medical abbreviation list",
        "clinical abbreviations", "approved abbreviations", "hospital abbreviations",
        "மருத்துவ சுருக்கங்கள்", "சுருக்கக் குறியீடுகள்", "abbreviation list"
    ]):
        return RESOURCE_REGISTRY["DOC_ABBREVIATION_GUIDE"]

    # 0d. User Billing Manual
    if any(k in q_norm for k in [
        "billing manual", "user billing manual", "billing guide", "hospital billing manual", "cashier manual",
        "பில்லிங் கையேடு", "பில்லிங் வழிகாட்டி", "billing user manual"
    ]) and not any(k in q_norm for k in ["tariff", "stock", "rate", "cost", "price", "charges"]):
        return RESOURCE_REGISTRY["DOC_BILLING_MANUAL"]

    # 0e. Nursing Operations Manual
    if any(k in q_norm for k in [
        "nursing manual", "nursing operations manual", "nursing user manual", "nursing guide",
        "நர்சிங் கையேடு", "செவிலியர் கையேடு", "nursing sop manual"
    ]) and not any(k in q_norm for k in ["nabh", "infection", "er manual"]):
        return RESOURCE_REGISTRY["DOC_NURSING_MANUAL"]

    # 0f. Replace PDF Server
    if any(k in q_norm for k in [
        "replace pdf", "replace pdf portal", "upload pdf server", "upload pdf portal", "admin replace pdf",
        "pdf replacement server", "பிடிஎஃப் மாற்று சர்வர்"
    ]):
        return RESOURCE_REGISTRY["APP_REPLACE_PDF"]

    # 0. General IT Forms Hub Queries
    if any(k in q_norm for k in [
        "it forms", "it form", "information technology forms", "it forms hub", "it vault",
        "hardware and access forms", "ஐடி படிவங்கள்", "தகவல் தொழில்நுட்ப படிவங்கள்",
        "it padivangal", "it padivam", "all it forms", "list of it forms"
    ]) and not any(k in q_norm for k in ["wifi", "system", "printer", "cug", "sim", "email", "mail", "user creation", "doctor id", "item creation", "toner", "computer", "desktop"]):
        return RESOURCE_REGISTRY["SECTION_IT_FORMS"]

    # 1. Wi-Fi Form & Network (Check BEFORE generic HIS access)
    if any(k in q_norm for k in ["wifi", "wi fi", "wireless", "வைஃபை", "internet connection", "laptop wifi"]):
        if any(k in q_norm for k in ["form", "foam", "request", "venum", "vendum", "permission", "application", "படிவம்", "கோரிக்கை", "employee wifi", "padivam", "vinnappam"]) or intent == SearchIntent.OPEN_FORM:
            return RESOURCE_REGISTRY["FORM_WIFI"]

    # 2. Item Creation in HIS (Check BEFORE generic HIS)
    if any(k in q_norm for k in ["item creation", "pharmacy item addition", "marunthu porul his", "மருந்து சேர்ப்பு", "பொருள் உருவாக்கம்", "item creation in his", "item creation form"]):
        return RESOURCE_REGISTRY["FORM_ITEM_CREATION"]

    # 3. Doctor ID Creation in HIS (Check BEFORE generic HIS)
    if any(k in q_norm for k in [
        "doctor id creation", "doctor id form", "doctor name creation", "maruthuvar id", "மருத்துவர் ஐடி",
        "doctor id creation in his", "doctor id", "new doctor name and id creation in his",
        "doctor name and id creation", "doctor name and id", "doctor name & id", "new doctor name",
        "doctor name id creation", "new doctor id", "maruthuvar peyar matrum id", "மருத்துவர் பெயர் மற்றும் ஐடி"
    ]):
        return RESOURCE_REGISTRY["FORM_DOCTOR_ID"]

    # 4. HIS Application vs HIS Form Disambiguation
    is_his_patient_scope = (
        not any(k in q_norm for k in ["stock", "stock details", "pdf", "sheet", "manual", "sop", "policy", "protocol", "guideline"]) and
        any(k in q_norm for k in [
            "patient details", "patient detail", "patient info", "patient record", "patient search",
            "reg io", "reg op", "reg ip", "reg er", "op registration", "ip registration", "er registration",
            "emergency registration", "new registration", "new patient", "review patient", "patient review",
            "ip admission", "patient admission", "patient discharge",
            "billing", "billinh", "op billing", "ip billing", "discharge billing", "patient billing", "billing login",
            "indents stores", "ward indents", "store indent", "material issue", "drug indent", "his indents", "his stores", "indents",
            "pharmacy in his", "his pharmacy", "pharmacy dispensing", "pharmacy billing",
            "front office", "front desk", "frontoffice", "front office login", "open front office",
            "his op", "his ip", "his ward", "his discharge", "his discharge summary", "discharge summary his", "discharge summary in his",
            "ward his", "op his", "ip his", "ward login", "ward management", "inpatient ward", "ip ward", "op ward",
            "op login", "ip login", "opd login", "ipd login"
        ])
    ) and not is_telephony_query(query)

    is_his_staff_user_intent = any(k in q_norm for k in [
        "staff user creation", "his staff user", "his staff creation", "user creation his"
    ])

    is_ticketing_word = any(k in q_norm for k in [
        "repair", "fixing", "maintenance", "electrical", "housekeeping", "laundry", "breakdown", "job order"
    ])

    if not is_ticketing_word and (
        is_his_patient_scope or is_his_staff_user_intent or
        "his" in tokens or "aosta" in q_norm or "backbone" in q_norm or
        "frontend login" in q_norm or "front end login" in q_norm or
        "front office" in q_norm or "front desk" in q_norm or "frontoffice" in q_norm or
        "his op" in q_norm or "his ip" in q_norm or "his ward" in q_norm or
        "doctor consultation workstation" in q_norm or "doctor consultation" in q_norm or
        "doctor workstation" in q_norm or "clinical workstation" in q_norm or
        "patient registration" in q_norm or
        "ஹெச்ஐஎஸ்" in tokens or "ஹிஸ்" in tokens or "ஹெச்ஐஎஸ் திற" in q_norm or
        q_norm.startswith("his ") or q_norm.endswith(" his") or q_norm == "his"
    ):
        # Explicit Form Requisition
        if any(k in q_norm for k in [
            "his form", "his forms", "user creation", "his user", "new his user",
            "access venum", "access vendum", "his account", "open his form",
            "padivam", "படிவம்", "creation form", "username form", "user request", "his id venum",
            "new his user request form", "his user creation form"
        ]) or (intent == SearchIntent.OPEN_FORM and "doctor" not in q_norm and "item" not in q_norm):
            return RESOURCE_REGISTRY["FORM_HIS_USER"]

        # Explicit Application Launch
        return RESOURCE_REGISTRY["APP_HIS"]

    # 5. HRMS Portal vs Leave, Attendance & Payslips
    if "hrms" in tokens or "pruworks" in q_norm or any(k in q_norm for k in ["open hrms", "hrms portal", "hrms login"]):
        return RESOURCE_REGISTRY["APP_HRMS"]

    if any(k in q_norm for k in [
        "salary", "pay slip", "payslip", "salary slip", "monthly pay", "check salary",
        "apply leave", "leave apply", "leave balance", "casual leave", "sick leave",
        "vidumurai", "viduppu", "leavu", "விடுமுறை",
        "sambalam", "சம்பள", "சம்பள ரசீது",
        "biometric punch", "attendance portal", "punch attendance", "attendance punch",
        "varugai", "வருகை"
    ]) and not any(k in q_norm for k in ["calendar", "holiday", "holidays 2026", "holiday list", "list of holidays"]):
        return RESOURCE_REGISTRY["APP_HRMS"]

    # 6. Resignation & Job Protocols (HRM Manual)
    if any(k in q_norm for k in [
        "resignation", "resign", "relieving", "notice period", "exit clearance",
        "rajinama", "raajinaama", "பணி விலகல்", "ராஜினாமா", "procedure resignation job form",
        "no dues", "nodues"
    ]):
        return RESOURCE_REGISTRY["FORM_RESIGNATION_HRM"]

    # 7. HR Forms Hub, Staff & Faculty Applications, Cadre Policies
    # 7a. General HR Forms Hub Queries
    if any(k in q_norm for k in [
        "hr forms", "hr form", "human resource forms", "human resources forms",
        "hr forms hub", "hr vault", "hr documents", "people and culture forms",
        "எச் ஆர் படிவங்கள்", "எச்.ஆர் படிவங்கள்", "பணியாளர் படிவங்கள்", "மனித வள படிவங்கள்",
        "hr padivangal", "hr padivam", "all hr forms", "list of hr forms"
    ]) and not any(k in q_norm for k in ["teaching", "non teaching", "promotion", "performer", "training", "privilege", "cmo", "resident", "resignation"]):
        return RESOURCE_REGISTRY["SECTION_HR_FORMS"]

    # 7b. Specific HR Recruitment, Promotion, Training & Privileging Forms
    if any(k in q_norm for k in [
        "promotion form", "for promotion", "promotion non teaching", "staff promotion",
        "career promotion", "promotion recommendation", "பதவி உயர்வு", "pathavi uyartvu"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_PROMOTION"]

    if any(k in q_norm for k in [
        "non performer", "non performer non teaching", "non-performer",
        "performance gap form", "staff mentoring log", "retraining form", "குறைபாடு மதிப்பீடு"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_NON_PERFORMER"]

    if any(k in q_norm for k in [
        "training feedback", "staff training feedback", "training evaluation form",
        "cme feedback", "induction feedback", "பயிற்சி பின்னூட்டம்", "பயிற்சி படிவம்", "payirchi feedback"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_TRAINING_FEEDBACK"]

    if any(k in q_norm for k in [
        "pms policy", "performance management system", "pms form", "pms appraisal",
        "kpi policy", "staff kpi", "செயல்திறன் மேலாண்மை", "செயல்திறன் கொள்கை"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_PMS"]

    if any(k in q_norm for k in [
        "clinical privileges general medicine", "clinical privileges medicine",
        "medicine privileges", "general medicine privileges", "physician privileges",
        "scope of practice medicine", "பொது மருத்துவம் அங்கீகார படிவம்", "பொது மருத்துவ உரிமை"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_PRIVILEGES_MEDICINE"]

    if any(k in q_norm for k in [
        "clinical privileges ent", "ent privileges", "ear nose throat privileges",
        "ent surgical privileges", "otorhinolaryngology privileges", "காது மூக்கு தொண்டை உரிமை"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_PRIVILEGES_ENT"]

    if any(k in q_norm for k in [
        "clinical privileges anaesthesia", "clinical privileges anesthesia",
        "anaesthesia privileges", "anesthesia privileges", "sedation privileges",
        "மயக்கவியல் உரிமை", "மயக்கவியல் மருத்துவ உரிமை"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_PRIVILEGES_ANAESTHESIA"]

    if any(k in q_norm for k in [
        "cmo policy", "chief medical officer policy", "casualty cmo policy",
        "cmo charter", "தலைமை மருத்துவ அலுவலர் கொள்கை"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_CMO_POLICY"]

    if any(k in q_norm for k in [
        "junior resident policy", "resident policy", "jr policy",
        "junior resident guidelines", "resident duty policy", "இளநிலை உறைவிட மருத்துவர்", "உறைவிட மருத்துவர் கொள்கை"
    ]):
        return RESOURCE_REGISTRY["FORM_HR_JUNIOR_RESIDENT"]

    if any(k in q_norm for k in [
        "non teaching", "non-teaching", "staff recruitment", "job application form for staff",
        "velai vinnappam", "வேலை விண்ணப்பம்", "பணியாளர் வேலை விண்ணப்பம்", "staff job application"
    ]):
        return RESOURCE_REGISTRY["FORM_NON_TEACHING"]

    if not any(k in q_norm for k in ["non teaching", "non-teaching", "non"]) and any(k in q_norm for k in [
        "teaching faculty", "teaching application", "faculty appraisal", "faculty recruitment",
        "professor application", "medical faculty application", "teaching form", "faculty form",
        "பேராசிரியர் விண்ணப்பம்", "ஆசிரியர் விண்ணப்பம்", "teching faculty"
    ]):
        return RESOURCE_REGISTRY["FORM_TEACHING"]

    # 8. IT Hardware & Telecom Forms
    if any(k in q_norm for k in [
        "system request", "system requisition", "new computer request", "kanini request",
        "கணினி கோரிக்கை", "கணினி படிவம்", "கணினி பழுது படிவம்", "kanini pazhuthu padivam", "kanini padivam",
        "computer repair form", "system repair form", "desktop system form",
        "system request form", "system form", "computer request form", "desktop request form", "workstation request form"
    ]):
        return RESOURCE_REGISTRY["FORM_SYSTEM"]

    if any(k in q_norm for k in [
        "printer request", "printer repair", "printer form", "toner replacement",
        "acchaagam padivam", "அச்சக படிவம்", "பிரிண்டர் படிவம்", "printer request form",
        "toner request", "barcode printer form", "label printer form"
    ]):
        return RESOURCE_REGISTRY["FORM_PRINTER"]

    # 8b. Medicolegal Clinical Consent Forms Disambiguation
    is_consent_word = any(k in q_norm for k in [
        "consent", "concent", "consen", "consnt", "conset", "commset",
        "opputhal", "oputhal", "oppudhal", "sammatham", "sammatha", "samatham",
        "ஒப்புதல்", "சம்மதம்", "paedconsent"
    ])

    # 1) Surrogate Consent
    if any(k in q_norm for k in ["surrogate", "surrugate", "surogate", "substitute decision maker", "incapable patient"]):
        return RESOURCE_REGISTRY["FORM_CONSENT_SURROGATE"]

    # 2) Paediatric Consent
    is_ped_word = any(k in q_norm for k in [
        "pediatric", "paediatric", "pedatric", "child", "children", "infant", "newborn",
        "neonatal", "kuzhanthai", "kulandhai", "pillai", "குழந்தை", "குழந்தைகள்", "pasanga"
    ])
    if is_ped_word and (is_consent_word or "form" in q_norm or "படிவம்" in q_norm or "surgery" in q_norm or "padivam" in q_norm):
        return RESOURCE_REGISTRY["FORM_CONSENT_PAEDIATRIC"]

    # 3) Blood Transfusion Consent
    is_clinical_reaction_question = any(k in q_norm for k in [
        "how to", "how do", "protocol", "management", "handle", "steps", "reaction protocol"
    ])
    is_blood_transfusion = not is_clinical_reaction_question and (
        any(k in q_norm for k in [
            "transfusion consent", "transfution", "blood consent", "blood component consent",
            "prbc consent", "ffp consent", "platelet consent", "ratha vangi consent",
            "iratha vangi consent", "ratham transfusion consent", "raththam selutha opputhal",
            "ரத்த மாற்று", "இரத்த மாற்று", "ரத்த தான ஒப்புதல்"
        ]) or (
            any(k in q_norm for k in ["blood", "transfusion", "ratha", "radha", "raththa", "ratham", "iratha"]) and
            (is_consent_word or any(k in q_norm for k in ["form", "foam", "padivam", "opputhal", "sammatham", "படிவம்"]))
        )
    )
    if is_blood_transfusion and not any(k in q_norm for k in ["stock", "stock details", "இருப்பு", "directory", "intercom", "phone"]):
        return RESOURCE_REGISTRY["FORM_CONSENT_BLOOD"]

    # 4) DAMA Consent Form (Discharge Against Medical Advice)
    is_dama_word = any(k in q_norm for k in [
        "dama", "lama", "damma", "damaa", "discharge against medical advice", "discharge against advice",
        "hospital vittu poga", "veliye poga consent", "veetuku poga consent", "hospital la irunthu poga",
        "discharge aaga consent", "மருத்துவ ஆலோசனைக்கு மாறாக"
    ])
    if is_dama_word:
        return RESOURCE_REGISTRY["FORM_CONSENT_DAMA"]

    # 5) Not Willing Consent (Treatment Refusal)
    is_not_willing = any(k in q_norm for k in [
        "not willing", "not wiling", "not willin", "treatment refusal", "procedure refusal",
        "investigation refusal", "refusal consent", "refusal of treatment",
        "maruppu form", "maruppu padivam", "chikitsai maruppu", "treatment vendam",
        "thevailla consent", "viruppamillai", "viruppamilla",
        "சிகிச்சை மறுப்பு", "விருப்பமில்லா படிவம்", "மறுப்பு படிவம்"
    ])
    if is_not_willing:
        return RESOURCE_REGISTRY["FORM_CONSENT_NOT_WILLING"]

    # 6) General Patient Admission Consent
    is_admission_consent = any(k in q_norm for k in [
        "admission consent", "general admission consent", "inpatient admission consent",
        "ward admission consent", "general patient admission", "general consent for admission",
        "patient admission form", "inpatient consent", "hospital admission consent",
        "serkai sammatham", "serkai padivam", "serkkai opputhal", "admit aaga consent",
        "ward serkai consent", "சேர்க்கை ஒப்புதல்", "நோயாளி சேர்க்கை சம்மதம்",
        "admisison consent", "admissin consent"
    ])
    if is_admission_consent:
        return RESOURCE_REGISTRY["FORM_CONSENT_ADMISSION"]

    # 7) Visiting Consultant Requisition
    if any(k in q_norm for k in [
        "visiting consultant", "visiting consultant requisition", "consultant requisition",
        "visiting doctor", "visiting specialist", "visitin consultant", "visiting consultent",
        "வெளி மருத்துவர் வருகை", "மருத்துவர் வருகை கடிதம்"
    ]):
        return RESOURCE_REGISTRY["FORM_VISITING_CONSULTANT"]

    # 8) Surgery / Surgical Consent (Tamil vs English)
    is_surgery_scope = any(k in q_norm for k in [
        "surgery", "surgical", "operation", "operative", "procedure", "ot consent",
        "sergery", "suregry", "surgry", "anaesthesia", "aruvai", "sikitsai", "sigichai", "அறுவை"
    ])
    if is_surgery_scope and (is_consent_word or "form" in q_norm or "படிவம்" in q_norm or "padivam" in q_norm):
        is_tamil_surgery = any(k in q_norm for k in ["tamil", "தமிழ்", "aruvai", "sikitsai", "sigichai", "அறுவை"])
        if is_tamil_surgery:
            return RESOURCE_REGISTRY["FORM_CONSENT_SURGERY_TA"]
        return RESOURCE_REGISTRY["FORM_CONSENT_SURGERY_EN"]

    # 9) Generic Consent Hub / Vault
    if is_consent_word and not is_ped_word:
        return RESOURCE_REGISTRY["SECTION_CONSENT_VAULT"]

    if any(k in q_norm for k in [
        "official email", "email form", "email id request", "மின்னஞ்சல் படிவம்", "minnanjal padivam",
        "official email request", "email request form", "mail request", "மின்னஞ்சல் கோரிக்கை",
        "minnanjal request", "minnanjal vinnappam", "mail id padivam", "email padivam"
    ]):
        return RESOURCE_REGISTRY["FORM_EMAIL_ID"]

    if any(k in q_norm for k in [
        "sim cug", "cug sim", "sim request", "cug form", "cug sim padivam", "cug padivam", "sim padivam",
        "cug request", "cug request form", "sim cug request form", "cug vinnappam",
        "சிம் படிவம்", "சிம் கார்டு கோரிக்கை", "சிம் கார்டு படிவம்"
    ]):
        return RESOURCE_REGISTRY["FORM_SIM_CUG"]

    # 9. Core Clinical & Operational Apps
    is_imaging_tariff = any(k in q_norm for k in ["tariff", "charges", "rate", "cost", "fee", "vilai", "selavu", "விலை", "செலவு", "கட்டணம்"])
    if not is_imaging_tariff and ("pacs" in tokens or "medsynapse" in q_norm or any(k in q_norm for k in [
        "xray scan", "scan paakanum", "ct scan", "mri scan", "ultrasound scan",
        "digital xray", "xray image", "radiology viewer", "xray viewer", "dicom",
        "view scan", "view xray", "எக்ஸ்ரே", "ஸ்கேன் பார்க்க"
    ])):
        return RESOURCE_REGISTRY["APP_PACS"]

    if ("mrd" in tokens or any(k in q_norm for k in [
        "discharge summary archive", "mrd records", "case sheet archive", "mrd portal",
        "old patient discharge summary", "old patient records", "historical patient file",
        "patient medical records portal"
    ])) and not any(k in q_norm for k in ["mom", "moms", "minutes", "committee", "commitee", "comitee"]):
        return RESOURCE_REGISTRY["APP_MRD"]

    if "mhc" in tokens or any(k in q_norm for k in ["master health", "மாஸ்டர் ஹெல்த் செக்கப்"]):
        return RESOURCE_REGISTRY["APP_MHC"]

    if "lineloom" in tokens or any(k in q_norm for k in ["opd token", "opd queue display", "opd token machine", "token machine"]):
        return RESOURCE_REGISTRY["APP_LINELOOM"]

    if any(k in q_norm for k in ["barcode", "pathology barcode", "lab barcode", "sample barcode"]):
        return RESOURCE_REGISTRY["APP_BARCODE"]

    if any(k in q_norm for k in ["eye camp", "eyecamp", "ophthalmology camp", "கண் முகாம்"]):
        return RESOURCE_REGISTRY["APP_EYECAMP"]

    if (any(k in q_norm for k in ["counselling", "counseling", "counselling & icu", "counselling and icu", "icu app", "icu software", "icu application", "icu log"]) and
        not any(k in q_norm for k in ["casesheet", "shifting", "checklist", "sbar", "form", "documentation", "padivam", "படிவம்"])):
        return RESOURCE_REGISTRY["APP_COUNSELLING"]

    # 9. Ticketing Desk (Repair, Fixing Anything, Maintenance, Electrical, Housekeeping, Laundry, IT Hardware)
    is_patient_scope = any(k in q_norm for k in [
        "patient details", "patient detail", "patient info", "patient record", "op billing", "ip billing",
        "discharge billing", "patient registration", "reg op", "reg ip", "reg er", "indents stores", "ward indents"
    ])

    is_ticketing_match = any(k in q_norm for k in [
        "ticketing", "maintenance desk", "it breakdown", "lodge ticket", "it ticket", "breakdown ticket",
        "report broken", "broken computer", "pc not working", "monitor not working", "display not working",
        "computer not working", "pc breakdown", "hardware repair", "hardware breakdown", "keyboard not working",
        "mouse not working", "his bug", "his not working",
        "repair", "fixing anything", "fixing", "fix", "maintenance",
        "electrical", "electrical maintenance", "electrical repair", "electrical fault", "electrical complaint", "electrical work",
        "housekeeping", "housekeeping complaint", "housekeeping maintenance", "housekeeping request", "cleaning complaint",
        "laundry", "laundry complaint", "laundry maintenance", "laundry request", "laundry issue", "laundry service"
    ]) or (any(k in q_norm for k in ["பழுது", "கணினி பழுது"]) and not any(k in q_norm for k in ["படிவம்", "padivam", "form"]))

    if is_ticketing_match and not is_patient_scope:
        if not is_telephony_query(query) and not any(k in q_norm for k in ["படிவம்", "padivam", "form", "printer request", "system request", "sop", "manual", "policy", "guideline", "protocol", "கையேடு", "விதிமுறை"]):
            return RESOURCE_REGISTRY["APP_TICKETING"]

    # Checklists (Apps vs Paper Forms)
    if any(k in q_norm for k in ["non clinical checklist", "non-clinical checklist", "gencl"]):
        return RESOURCE_REGISTRY["APP_NON_CLINICAL_CHECKLIST"]

    if any(k in q_norm for k in [
        "clinical checklist", "checklist app", "checklist application", "checklist software",
        "checklist webapplication", "checklist web application",
        "clinical audit app", "audit app"
    ]):
        return RESOURCE_REGISTRY["APP_CLINICAL_CHECKLIST"]

    # 10. Clinical Checklists & Common Forms
    if any(k in q_norm for k in [
        "common forms", "common form", "clinical forms", "clinical form", "icu forms", "icu form",
        "common forms hub", "clinical forms hub", "common forms section", "icu checklists",
        "clinical indents", "hospital common forms", "பொது படிவங்கள்", "பொது படிவம்", "மருத்துவ படிவங்கள்"
    ]):
        return RESOURCE_REGISTRY["SECTION_COMMON_FORMS"]

    if any(k in q_norm for k in ["code blue post event analysis", "code blue post event analysis form", "code blue analysis form", "code blue audit form"]):
        return RESOURCE_REGISTRY["FORM_CODE_BLUE_ANALYSIS"]

    if any(k in q_norm for k in ["code rrt activation form", "code rrt", "rrt activation form", "rapid response team form", "rrt form"]):
        return RESOURCE_REGISTRY["FORM_CODE_RRT"]

    if any(k in q_norm for k in ["code blue form", "code blue algorithm", "code blue pdf", "code blue sheet"]) or (q_norm in ["code blue form", "code blue algorithm"]):
        return RESOURCE_REGISTRY["FORM_CODE_BLUE"]

    if any(k in q_norm for k in [
        "narcotic drugs form", "narcotic drugs", "narcotic drug form", "narcotics form", "narcotic register",
        "narcotic indent", "narcotik form", "narcotic form", "narcotic", "narcotics",
        "போதை மருந்து படிவம்", "போதை மருந்து", "மயக்க மருந்து படிவம்"
    ]):
        return RESOURCE_REGISTRY["FORM_NARCOTIC"]

    if any(k in q_norm for k in ["drug food interaction", "food drug interaction", "drug nutrient interaction", "மருந்து மற்றும் உணவு"]):
        return RESOURCE_REGISTRY["FORM_DRUG_FOOD_INTERACTION"]

    if any(k in q_norm for k in ["drug drug interaction", "drug interaction list", "drug interactions list"]):
        return RESOURCE_REGISTRY["FORM_DRUG_DRUG_INTERACTION"]

    if any(k in q_norm for k in [
        "approved abbreviation", "approved abbreviations", "approved medical abbreviations",
        "medical abbreviations", "hospital abbreviations", "do not use abbreviations"
    ]):
        return RESOURCE_REGISTRY["FORM_APPROVED_ABBREVIATIONS"]

    if any(k in q_norm for k in ["emergency medication list", "emergency drug list", "crash cart medication list", "crash cart drugs list"]):
        return RESOURCE_REGISTRY["FORM_EMERGENCY_MEDS"]

    if any(k in q_norm for k in [
        "high alert medications", "high alert drugs", "high alert medication list",
        "high alert meds list", "high alert meds", "high alert form", "உயர் எச்சரிக்கை மருந்துகள்"
    ]):
        return RESOURCE_REGISTRY["FORM_HIGH_ALERT_MEDS"]

    if any(k in q_norm for k in [
        "48 hour antibiotics review form", "48 hour antibiotics review", "48 hour antibiotic review",
        "antibiotic review form", "antibiotics review form", "48 hr antibiotic review",
        "antibiotic time out", "antibiotic review", "antibiotics review"
    ]):
        return RESOURCE_REGISTRY["FORM_ANTIBIOTIC_REVIEW"]

    if any(k in q_norm for k in ["day care assessment form", "day care assessment", "daycare assessment form", "daycare assessment"]):
        return RESOURCE_REGISTRY["FORM_DAYCARE_ASSESSMENT"]

    if any(k in q_norm for k in ["day care discharge summary", "day care - discharge summary", "daycare discharge summary", "daycare discharge form", "day care discharge"]):
        return RESOURCE_REGISTRY["FORM_DAYCARE_DISCHARGE"]

    if any(k in q_norm for k in ["er discharge summary form", "er discharge summary", "er - discharge summary form", "emergency room discharge summary"]):
        return RESOURCE_REGISTRY["FORM_ER_DISCHARGE"]

    if any(k in q_norm for k in ["er doctors initial assessment form", "doctors initial assessment for emergency room", "er doctor initial assessment", "er initial assessment doctor", "er doctor assessment"]):
        return RESOURCE_REGISTRY["FORM_ER_DOCTOR_ASSESSMENT"]

    if any(k in q_norm for k in ["er nurses initial assessment form", "nurses initial assessment for emergency room", "er nurse initial assessment", "er initial assessment nurse", "er nurse assessment"]):
        return RESOURCE_REGISTRY["FORM_ER_NURSE_ASSESSMENT"]

    if any(k in q_norm for k in ["food token requisition form", "food token requisition", "food token form", "food token", "diet token", "unavu token", "சாப்பாடு டோக்கன்", "உணவு டோக்கன்"]):
        return RESOURCE_REGISTRY["FORM_FOOD_TOKEN"]

    if any(k in q_norm for k in ["adr form", "adr-form", "adverse drug reaction form", "adr report", "pharmacovigilance form", "மருந்து ஒவ்வாமை படிவம்"]) or (q_norm in ["adr", "adr form"]):
        return RESOURCE_REGISTRY["FORM_ADR"]

    if any(k in q_norm for k in ["incident report form", "incident form", "sentinel event form", "near miss form", "நிகழ்வு அறிக்கை படிவம்", "விபத்து அறிக்கை"]) or (q_norm in ["incident report", "incident"]):
        return RESOURCE_REGISTRY["FORM_INCIDENT_REPORT"]

    if any(k in q_norm for k in ["transfusion technique protocol", "transfusion protocol form", "blood transfusion protocol sheet"]):
        return RESOURCE_REGISTRY["FORM_TRANSFUSION_PROTOCOL"]

    if any(k in q_norm for k in ["antibiogram form", "antibiogram report", "hospital antibiogram"]) or (q_norm in ["antibiogram", "antibiograms"]):
        return RESOURCE_REGISTRY["FORM_ANTIBIOGRAM"]

    if any(k in q_norm for k in ["restricted antibiotic form", "restricted anti-biotic form", "reserve antibiotic form", "hic antibiotic form", "கட்டுப்படுத்தப்பட்ட ஆன்டிபயாடிக் படிவம்"]):
        return RESOURCE_REGISTRY["FORM_RESTRICTED_ANTIBIOTIC"]

    if any(k in q_norm for k in ["restricted antibiotic drug list", "restricted anti-biotic drug list", "restricted antibiotic list", "restricted antibiotics list", "restricted drug list"]):
        return RESOURCE_REGISTRY["FORM_RESTRICTED_ANTIBIOTIC_LIST"]

    if any(k in q_norm for k in ["counselling documentation", "counselling documentation form", "counselling form", "counseling form", "patient counselling form", "நோயாளி ஆலோசனை படிவம்"]):
        return RESOURCE_REGISTRY["FORM_COUNSELLING"]

    if any(k in q_norm for k in ["handing over sbar record", "handing over sbar", "sbar sheet", "sbar record", "sbar handover", "sbar form", "sbar"]) and not any(k in q_norm for k in ["protocol", "policy", "manual", "sop", "guideline"]):
        return RESOURCE_REGISTRY["FORM_SBAR"]

    if any(k in q_norm for k in ["icu checklist ward shifting", "ward shifting form", "icu to ward shifting", "ward shifting criteria checklist", "ward shifting checklist", "ward shifting", "ward shift", "ward shifting padivam", "வார்டு மாற்றம்"]):
        return RESOURCE_REGISTRY["FORM_WARD_SHIFTING"]

    if any(k in q_norm for k in ["icu casesheet checklist", "icu casesheet", "icu audit checklist", "icu checklist", "theevira sigichai checklist", "தீவிர சிகிச்சை செக்லிஸ்ட்"]):
        return RESOURCE_REGISTRY["FORM_ICU_CASESHEET"]

    if any(k in q_norm for k in ["mews score sheet", "mews score", "mews chart", "mews form", "mews sheet", "mews"]) and not any(k in q_norm for k in ["protocol", "policy", "manual", "sop", "guideline"]):
        return RESOURCE_REGISTRY["FORM_MEWS"]

    if any(k in q_norm for k in ["emergency patient transfer record", "patient transfer record", "emergency transfer record", "emergency transfer form", "emergency patient transfer", "emergency transfer"]):
        return RESOURCE_REGISTRY["FORM_EMERGENCY_TRANSFER"]

    # 11. Circulars & Real-Time Bulletins (Section 7)
    if any(k in q_norm for k in ["holidays 2026", "holiday calendar 2026", "list of holidays 2026", "விடுமுறை பட்டியல் 2026"]):
        return RESOURCE_REGISTRY["DOC_HOLIDAYS_2026"]

    if any(k in q_norm for k in [
        "24hr duty roster", "24 hours duty roster", "duty roster", "doctor duty roster", "cmo duty roster", "cmo duty",
        "intensivist duty", "nursing supervisor roster", "on duty roster", "duty details", "who is on duty",
        "casualty duty doctor", "casualty cmo", "duty doctor list", "today duty doctor", "24hr duty details",
        "24hrs duty details", "duty list", "doctor roster", "24hr duty", "duty doctor",
        "டூட்டி ரோஸ்டர்", "பணி அட்டவணை", "டூட்டி டாக்டர்", "இன்றைய டூட்டி டாக்டர்"
    ]):
        return RESOURCE_REGISTRY["DOC_DUTY_ROSTER"]

    if not any(k in q_norm for k in ["consent", "padivam", "படிவம்", "ஒப்புதல்"]) and any(k in q_norm for k in [
        "blood bank stock", "blood stock", "blood bank stock details", "blood availability", "blood units available",
        "prbc stock", "ffp stock", "platelet stock", "platelets stock", "cryo stock", "rare blood units",
        "blood bank inventory", "blood stock list", "ratha vangi stock", "iratha vangi",
        "இரத்த வங்கி இருப்பு விவரம்", "இரத்த வங்கி இருப்பு", "ரத்த வங்கி ஸ்டாக்", "ரத்த இருப்பு"
    ]):
        return RESOURCE_REGISTRY["DOC_BLOOD_BANK_STOCK"]

    if any(k in q_norm for k in [
        "police station number", "police station numbers", "police station phone number", "police directory",
        "nearest police station", "police contact", "police contacts", "police station contact", "police station phone",
        "mlc police", "police outpost", "police liaison", "police station hotline", "police numbers",
        "local police station", "police number", "police phone",
        "காவல் நிலைய எண்", "காவல் நிலைய எண்கள்", "காவல்துறை தொடர்பு", "போலீஸ் எண்", "போலீஸ் போன் எண்"
    ]):
        return RESOURCE_REGISTRY["DOC_POLICE_STATION_NUMBERS"]

    if any(k in q_norm for k in [
        "clinical case patients", "clinical cases", "clinical case patient", "clinical case documentation",
        "clinical case protocol", "clinical protocols and standing orders", "clinical casesheet protocol",
        "clinical guidelines circular", "clinical pdf",
        "மருத்துவ வழக்கு நோயாளிகள்", "மருத்துவ வழக்கு வழிகாட்டுதல்"
    ]):
        return RESOURCE_REGISTRY["DOC_CLINICAL_CASE_PATIENTS"]

    if any(k in q_norm for k in [
        "pms policy", "performance management system", "performance management system policy",
        "hospital pms", "kpi policy", "staff appraisal policy", "pms kpis", "performance appraisal framework",
        "performance evaluation policy", "annual appraisal policy", "pms policy pdf",
        "செயல்திறன் மேலாண்மை கொள்கை", "பணியாளர் மதிப்பீடு கொள்கை"
    ]):
        return RESOURCE_REGISTRY["DOC_PMS_POLICY"]

    if any(k in q_norm for k in ["safety meeting circular", "safety circular 2026", "safety meeting circular 2026", "safety circular", "பாதுகாப்பு கூட்ட சுற்றறிக்கை"]):
        return RESOURCE_REGISTRY["CIRCULAR_SAFETY_2026"]

    if any(k in q_norm for k in ["swot analysis circular", "swot analysis", "swot circular jan 2026", "swot circular", "swot analysis circular 2026"]):
        return RESOURCE_REGISTRY["CIRCULAR_SWOT_2026"]

    if any(k in q_norm for k in ["ams inhouse applications", "ams applications circular", "our developed inhouse applications", "inhouse applications circular", "ams circular"]):
        return RESOURCE_REGISTRY["CIRCULAR_AMS_2026"]

    if any(k in q_norm for k in ["refugee circular", "refugee 2026", "refugee policy circular", "refugee circular 2026"]):
        return RESOURCE_REGISTRY["CIRCULAR_REFUGEE_2026"]

    if any(k in q_norm for k in ["code violet", "code violet circular", "code violet policy", "code violet protocol", "கோட் வயலெட்"]):
        return RESOURCE_REGISTRY["CIRCULAR_CODE_VIOLET"]

    if any(k in q_norm for k in ["patient valuable policy", "patient valuable circular", "patient valuables policy", "patient valuables circular"]):
        return RESOURCE_REGISTRY["CIRCULAR_PATIENT_VALUABLE"]

    if any(k in q_norm for k in ["emergency rescue team", "rescue team circular", "ert circular", "emergency rescue team circular", "அவசர மீட்புக் குழு"]):
        return RESOURCE_REGISTRY["CIRCULAR_EMERGENCY_RESCUE_TEAM"]

    if any(k in q_norm for k in [
        "digital e circulars section", "e circulars section", "where is circulars section", "circulars on homepage",
        "digital e bulletin", "digital bulletin board", "bulletin board", "digital board",
        "சுற்றறிக்கை பகுதி", "அறிவிப்பு பலகை"
    ]):
        return RESOURCE_REGISTRY["SECTION_E_CIRCULARS"]

    if any(k in q_norm for k in [
        "digital e circulars", "digital e-circulars", "digital e circular", "digital e circulars & protocols",
        "digital e circulars and protocols", "e circulars", "e-circulars", "e circular", "e-circular",
        "recent circulars", "recent circular", "circulars", "circular", "hospital circulars", "hospital circular",
        "management circulars", "management circular", "office orders", "office circulars", "latest circulars",
        "circulars and protocols", "protocols and circulars", "circulars directory", "circulars hub",
        "circulars list", "list of circulars", "all circulars", "open circulars",
        "சுற்றறிக்கை", "சுற்றறிக்கைகள்", "மின் சுற்றறிக்கை", "அலுவலக சுற்றறிக்கை"
    ]) or (q_norm in ["circular", "circulars", "e-circular", "e circular"]):
        return RESOURCE_REGISTRY["DIR_CIRCULARS"]

    if any(k in q_norm for k in ["where is the forms section", "forms section", "forms vault", "forms hub"]):
        return RESOURCE_REGISTRY["DIR_FORMS_HUB"]

    # 11b. Section 8: Tariff & Live Stock Dashboard, Tariffs, Pharmacy Stock & General Store
    is_telecom_or_login_query = any(k in q_norm for k in [
        "intercom", "extension", "extensions", "ext", "phone", "telephone", "calling", "call",
        "tholaipesi", "tholaipasi", "inaippu", "koopidu", "pesa", "தொலைபேசி", "எண்", "இணைப்பு", "அழைப்பு", "போன்",
        "login", "aosta", "backbone", "user creation", "new doctor id", "wifi"
    ])
    is_consent_or_sop_query = any(k in q_norm for k in [
        "consent", "sammatham", "opputhal", "படிவம்", "ஒப்புதல்", "padivam", "vinnappam",
        "sop", "sops", "manual", "policy", "charter", "committee", "mom", "drill"
    ])

    if not is_telecom_or_login_query and not is_consent_or_sop_query:
        # Specific Tariffs
        if any(k in q_norm for k in [
            "special packages", "admission packages", "health packages", "deluxe packages", "hospital packages",
            "treatment packages", "master packages", "package tariff", "panchayat discount", "hospital special packages",
            "சிகிச்சை தொகுப்பு", "ஹெல்த் பேக்கேஜ்", "பேக்கேஜ் கட்டணம்", "பஞ்சாயத்து தள்ளுபடி"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_PACKAGES"]

        if any(k in q_norm for k in [
            "lab tariff", "lab charges", "laboratory tariff", "lab investigation tariff", "laboratory test charges",
            "blood test charges", "pathology charges", "biochemistry tariff", "microbiology tariff", "lab test rates",
            "investigation charges", "lab rates", "laboratory charges", "லேப் கட்டணம்", "இரத்த பரிசோதனை கட்டணம்", "ஆய்வக கட்டணம்"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_LAB"]

        if any(k in q_norm for k in [
            "radiology tariff", "radiology charges", "xray tariff", "x-ray charges", "ct scan tariff", "ct scan charges",
            "mri charges", "mri tariff", "ultrasound tariff", "usg charges", "imaging charges", "xray charges", "scan charges",
            "ரேடியாலஜி கட்டணம்", "ஸ்கேன் கட்டணம்", "எக்ஸ்ரே கட்டணம்"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_RADIOLOGY"]

        if any(k in q_norm for k in [
            "physiotherapy tariff", "physiotherapy charges", "physio tariff", "physio charges", "physical therapy charges",
            "physiotherapy rates", "rehabilitation charges", "பிசியோதெரபி கட்டணம்", "உடற்பயிற்சி சிகிச்சை கட்டணம்"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_PHYSIOTHERAPY"]

        if any(k in q_norm for k in [
            "ot tariff", "surgery tariff", "operation theatre tariff", "ot charges", "surgery charges",
            "operation charges", "general ward surgery ot tariff", "surgical procedure charges", "theatre charges",
            "operation theatre charges", "surgical tariff", "அறுவை சிகிச்சை கட்டணம்", "ஆபரேஷன் தியேட்டர் கட்டணம்", "ஆபரேஷன் கட்டணம்"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_OT_SURGERY"]

        if any(k in q_norm for k in [
            "room rent", "room tariff", "bed charges", "ward charges", "icu tariff", "icu charges",
            "special ward room tariff", "deluxe room rent", "single room rent", "sharing room charges",
            "icu bed charges", "room rates", "hospital room rent", "inpatient bed charges",
            "அறை வாடகை", "ஐசியூ கட்டணம்", "படுக்கை கட்டணம்", "வார்டு கட்டணம்", "ரூம் வாடகை"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_ICU_ROOM"]

        if any(k in q_norm for k in [
            "other department tariff", "other departments tariff", "other tariffs", "miscellaneous hospital tariffs",
            "dental tariff", "ent charges", "casualty charges tariff", "other dept tariff", "இதர கட்டணங்கள்"
        ]):
            return RESOURCE_REGISTRY["DOC_TARIFF_OTHER_DEPTS"]

        # Specific Stock & Pharmacy
        if any(k in q_norm for k in [
            "139 drugs", "139 drugs stock", "drug stores stock details", "drug stores stock", "drug store stock",
            "essential drugs stock", "central pharmacy drug stock", "central drug store stock", "139 essential drugs",
            "139 மருந்து இருப்பு", "மத்திய மருந்து இருப்பு"
        ]):
            return RESOURCE_REGISTRY["DOC_DRUG_STORES_STOCK"]

        if any(k in q_norm for k in [
            "ip pharmacy stock", "inpatient pharmacy stock", "in patient pharmacy stock", "ip drug stock",
            "77 items pharmacy stock", "ip pharmacy stock details", "உள்நோயாளி மருந்தக இருப்பு"
        ]):
            return RESOURCE_REGISTRY["DOC_IP_PHARMACY_STOCK"]

        if any(k in q_norm for k in [
            "insurance pharmacy stock", "tpa pharmacy stock", "insurance drug stock", "515 items pharmacy stock",
            "cmchis pharmacy stock", "insurance pharmacy stock details", "காப்பீட்டு மருந்தக இருப்பு"
        ]):
            return RESOURCE_REGISTRY["DOC_INSURANCE_PHARMACY_STOCK"]

        if any(k in q_norm for k in [
            "op pharmacy stock", "opd pharmacy stock", "outpatient pharmacy stock", "op drug stock",
            "90 items pharmacy stock", "op pharmacy stock details", "வெளிநோயாளி மருந்தக இருப்பு"
        ]):
            return RESOURCE_REGISTRY["DOC_OP_PHARMACY_STOCK"]

        if any(k in q_norm for k in [
            "hospital formulary 2025", "hospital formulary", "formulary 2025", "drug formulary 2025",
            "மருந்து கையேடு 2025", "மருந்தியல் கையேடு 2025"
        ]):
            return RESOURCE_REGISTRY["DOC_HOSPITAL_FORMULARY_2025"]

        if any(k in q_norm for k in [
            "free drug list", "nmc free drug list", "nmc drug list", "free medicines list", "free drug list nmc",
            "pharmacy updated 11.05.26", "free drugs nmc", "இலவச மருந்து பட்டியல்", "என்எம்சி இலவச மருந்துகள்", "இலவச மருந்துகள்"
        ]):
            return RESOURCE_REGISTRY["DOC_FREE_DRUG_LIST_NMC"]

        if any(k in q_norm for k in [
            "inventory stock details 2024", "inventory stock details", "inventory stock pdf", "general store inventory pdf",
            "store inventory pdf", "738 inventory items", "ஸ்டோர் இருப்பு விவரம்", "ஸ்டோர் இருப்பு அறிக்கை"
        ]):
            return RESOURCE_REGISTRY["DOC_INVENTORY_STOCK_2024"]

        if any(k in q_norm for k in [
            "general store", "hospital general store", "general store stock", "general store inventory",
            "store inventory", "stationery stock", "surgical kits stock", "cssd store", "store stock",
            "பொது சேமிப்பு கிடங்கு", "ஸ்டோர் இருப்பு", "பொது ஸ்டோர்", "ஸ்டோர் விவரம்"
        ]):
            return RESOURCE_REGISTRY["CARD_GENERAL_STORE"]

        if any(k in q_norm for k in [
            "pharmacy stock", "pharmacy live stock", "live pharmacy stock", "drug counters", "pharmacy stock counters",
            "dispensing counters", "pharmacy counters", "drug stock", "medicines stock", "drugs stock",
            "மருந்தக இருப்பு", "மருந்து இருப்பு விபரம்", "marunthu stock", "marunthagam stock"
        ]):
            return RESOURCE_REGISTRY["CARD_PHARMACY_STOCK"]

        if any(k in q_norm for k in [
            "tariff & live stock", "tariff and live stock", "tariff live stock", "tariff stock", "live stock",
            "tariffs and stock", "tariffs & stock", "hospital tariffs and stock", "tariff and stock section",
            "where is tariff section", "tariff section", "live stock section", "billing schedules and live supply counters",
            "கட்டணம் மற்றும் இருப்பு", "கட்டண விவரம்", "மருந்து இருப்பு", "சேமிப்பு கிடங்கு இருப்பு", "கட்டண அட்டவணை",
            "tariff விவரம்", "hospital kattanam", "vilai vivaram", "selavu vivaram"
        ]):
            return RESOURCE_REGISTRY["SECTION_TARIFF_STOCK"]

        if any(k in q_norm for k in [
            "hospital tariffs", "hospital tariff", "tariffs", "tariff", "schedule of charges",
            "hospital charges", "billing rates", "rate list", "treatment cost", "hospital fees",
            "service charges", "all tariffs", "list of tariffs", "hospital billing rates",
            "மருத்துவமனை கட்டணம்", "கட்டண பட்டியல்", "கட்டண விபரம்", "மருத்துவ கட்டணம்",
            "billing charges"
        ]) or (q_norm in ["tariff", "tariffs", "கட்டணம்", "கட்டணங்கள்"]):
            return RESOURCE_REGISTRY["CARD_HOSPITAL_TARIFFS"]

    # 12. Manuals Directory / Hub & Core Quality Committee Hub
    is_specific_manual_question = any(k in q_norm for k in [
        "protocol", "policy", "guideline", "guidelines", "sop", "sops", "criteria", "procedure",
        "needle", "stick", "transfusion", "waste", "hygiene", "cpr", "blue", "yellow", "red", "pink",
        "restraint", "vulnerable", "triage", "fall", "pain", "mews", "cauti", "clabsi", "vae"
    ])

    if not is_specific_manual_question:
        if any(k in q_norm for k in [
            "core quality committee hub", "core quality committee", "quality committee hub", "quality hub",
            "core quality", "quality governance", "nabh governance", "தரக் கட்டுப்பாட்டு மையம்", "தரக்கட்டுப்பாடு"
        ]):
            return RESOURCE_REGISTRY["HUB_CORE_QUALITY"]

        if any(k in q_norm or k in q_lower for k in [
            "open manuals", "open manual", "hospital manuals", "hospital manual", "nabh manuals", "nabh manual",
            "quality manuals", "quality manual", "manuals hub", "manual hub", "manuals directory", "manual directory",
            "hospital sops", "hospital sop", "hospital sops hub", "clinical manuals", "clinical manual",
            "accreditation manuals", "accreditation manual", "hospital manuals hub", "all manuals", "all manual",
            "nabh documents", "sops list", "list of manuals", "quality committee manuals", "quality committee manual",
            "மருத்துவமனை கையேடுகள்", "கையேடுகள்", "விதிமுறைகள்"
        ]) or (q_norm in ["manuals", "manual", "sops", "sop", "கையேடு", "kaiyedu"]):
            return RESOURCE_REGISTRY["DIR_MANUALS"]

    # 13. Committee Directory & Charter Searches
    # If the user is specifically querying for MOM of a specific month (e.g. oct MOM, MOM oct, nov MOM):
    # Delegate to specialized month MOM resolver in server.py
    is_month_mom = (
        any(k in q_norm for k in ["mom", "moms", "minutes", "meeting", "கூட்ட அறிக்கை"]) and
        any(m in q_norm for m in [
            "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
            "january", "february", "march", "april", "june", "july", "august", "september", "october", "november", "december"
        ])
    )
    if is_month_mom:
        return None

    if any(k in q_norm or k in q_lower for k in [
        "list of committee", "list of commitee", "list of committees", "committee list", "committees list",
        "open committee", "open comitee", "open committees", "hospital committees", "hospital committee",
        "hospital committee list", "hospital committees list", "committee directory", "committees directory",
        "committee hub", "committees hub", "governance committees", "all committees", "all committee",
        "committee calendar", "mock drill calendar", "committee scheduled calendar",
        "mom directory", "minutes of meeting directory", "quality committee members", "quality committee charter",
        "மருத்துவமனை குழுக்கள்", "குழுக்கள் பட்டியல்", "குழு பட்டியல்", "நிர்வாகக் குழு"
    ]) or (q_norm in ["committee", "committees", "comitee", "commitee", "mom", "moms", "குழு", "குழுக்கள்"]):
        return RESOURCE_REGISTRY["DIR_COMMITTEES"]

    if intent == SearchIntent.FIND_COMMITTEE:
        if "infection control" in q_norm or "hicc" in q_norm:
            return RESOURCE_REGISTRY["DOC_HICC_CHARTER"]
        return RESOURCE_REGISTRY["DIR_COMMITTEES"]

    return None

