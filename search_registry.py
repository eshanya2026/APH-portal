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
            "his app", "his application", "his website", "his tool", "aosta app",
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
        "description": "Institutional ticketing system to lodge IT, HIS, biomedical, civil, and electrical breakdown job orders.",
        "description_ta": "கணினி, இணையம், மற்றும் மருத்துவமனை பழுது புகார்களைப் பதிவு செய்ய Ticketing Desk.",
        "aliases": [
            "ticketing", "ticket", "ticketing desk", "lodge ticket", "it ticket", "maintenance desk",
            "ticketing app", "ticketing application", "ticketing software", "ticket app", "maintenance app",
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
            "visiting consultant", "visiting consultant requisition", "visiting consultant letter", "consultant requisition form"
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
        "title": "APH Recent Circulars & Office Orders",
        "url": "./recent circular.html",
        "category": "Circulars",
        "badge": "Notice Hub",
        "intent_type": SearchIntent.FIND_DIRECTORY,
        "description": "Latest institutional office orders, administration circulars, and official memos.",
        "description_ta": "மருத்துவமனை நிர்வாகத்தின் சமீபத்திய சுற்றறிக்கைகள் மற்றும் அறிவிப்புகள்.",
        "aliases": ["recent circulars", "recent circular", "circulars", "office orders", "latest notices", "சுற்றறிக்கை"],
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
    "ராஜினாமா நோட்டீஸ்": "resignation notice period relieving"
}

# =========================================================================
# 2. INTENT CLASSIFIER & QUERY NORMALIZER
# =========================================================================
TYPO_FIXES = {
    'opn': 'open',
    'hiss': 'his',
    'foam': 'form',
    'foarm': 'form',
    'inercom': 'intercom',
    'leavu': 'leave',
    'vinnapam': 'vinnappam',
    'vidumura': 'vidumurai',
    'rajinamaa': 'rajinama',
}

def clean_and_tokenize(text):
    if not text:
        return set()
    cleaned = re.sub(r'[^\w\s\u0B80-\u0BFF]', ' ', text.lower())
    raw_tokens = cleaned.split()
    return {TYPO_FIXES.get(t, t) for t in raw_tokens}

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
    q_norm = " ".join([TYPO_FIXES.get(w, w) for w in q_lower.replace("-", " ").split()])
    tokens = clean_and_tokenize(q_lower)

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
    is_form_word = bool(tokens & {"form", "forms", "padivam", "படிவம்", "vinnappam", "விண்ணப்பம்", "requisition"})
    is_creation_intent = any(k in q_norm for k in [
        "user creation", "doctor id", "item creation", "id creation", "account creation",
        "access venum", "access vendum", "creation in his"
    ])
    if (is_form_word or is_creation_intent) and not any(k in q_norm for k in ["open pacs", "open mrd", "open hrms"]):
        if q_norm in ["open his form", "his form", "wifi form", "printer request form", "system request form"] or is_creation_intent:
            return SearchIntent.OPEN_FORM

    # 5. Core Application Launch Intent
    is_app_keyword = any(k in q_norm for k in [
        "his", "aosta", "backbone", "hrms", "pruworks", "pacs", "medsynapse",
        "mrd", "mhc", "master health", "lineloom", "barcode", "counselling",
        "eye camp", "eyecamp", "checklist", "gencl", "ticketing",
        "ஹெச்ஐஎஸ்", "ஹிஸ்"
    ]) or bool(tokens & {"his", "hrms", "pacs", "mrd", "mhc", "lineloom", "barcode", "eyecamp", "checklist", "gencl", "ticketing"})
    is_launch_action = any(k in q_norm for k in [
        "open", "launch", "login", "portal", "workstation", "viewer", "software",
        "app", "application", "website", "tool", "enga", "yenga", "thira", "திற",
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
    q_norm = " ".join([TYPO_FIXES.get(w, w) for w in q_lower.replace("-", " ").split()])
    tokens = clean_and_tokenize(q_lower)

    # 1. Wi-Fi Form & Network (Check BEFORE generic HIS access)
    if any(k in q_norm for k in ["wifi", "wi fi", "wireless", "வைஃபை", "internet connection", "laptop wifi"]):
        if any(k in q_norm for k in ["form", "foam", "request", "venum", "vendum", "permission", "application", "படிவம்", "கோரிக்கை"]) or intent == SearchIntent.OPEN_FORM:
            return RESOURCE_REGISTRY["FORM_WIFI"]

    # 2. Item Creation in HIS (Check BEFORE generic HIS)
    if any(k in q_norm for k in ["item creation", "pharmacy item addition", "marunthu porul his", "மருந்து சேர்ப்பு", "பொருள் உருவாக்கம்"]):
        return RESOURCE_REGISTRY["FORM_ITEM_CREATION"]

    # 3. Doctor ID Creation in HIS (Check BEFORE generic HIS)
    if any(k in q_norm for k in ["doctor id", "doctor name", "maruthuvar id", "மருத்துவர் ஐடி", "மருத்துவர் பெயர்"]):
        return RESOURCE_REGISTRY["FORM_DOCTOR_ID"]

    # 4. HIS Application vs HIS Form Disambiguation
    if (
        "his" in tokens or "aosta" in q_norm or "backbone" in q_norm or
        "ஹெச்ஐஎஸ்" in tokens or "ஹிஸ்" in tokens or "ஹெச்ஐஎஸ் திற" in q_norm or
        q_norm.startswith("his ") or q_norm.endswith(" his") or q_norm == "his"
    ):
        # Explicit Form Requisition
        if any(k in q_norm for k in [
            "his form", "his forms", "user creation", "his user", "new his user",
            "access venum", "access vendum", "his account", "open his form",
            "padivam", "படிவம்", "creation form", "username form", "user request", "his id venum"
        ]) or (intent == SearchIntent.OPEN_FORM and "doctor" not in q_norm and "item" not in q_norm):
            return RESOURCE_REGISTRY["FORM_HIS_USER"]

        # Explicit Application Launch
        if intent == SearchIntent.OPEN_APPLICATION or any(k in q_norm for k in [
            "open his", "his open", "login", "workstation", "portal", "software",
            "enga", "திற", "திறக்கவும்", "ஹெச்ஐஎஸ் திற", "open panna", "where is his", "his login"
        ]) or q_norm in ["open his", "his", "his login", "his login enga", "opn his", "hiss login"]:
            return RESOURCE_REGISTRY["APP_HIS"]

    # 5. HRMS Portal vs Leave, Attendance & Payslips
    if "hrms" in tokens or "pruworks" in q_norm or any(k in q_norm for k in ["open hrms", "hrms portal", "hrms login"]):
        return RESOURCE_REGISTRY["APP_HRMS"]

    if any(k in q_norm for k in [
        "apply leave", "leave apply", "vidumurai", "viduppu", "leavu", "விடுமுறை",
        "payslip", "pay slip", "salary slip", "sambalam", "சம்பள", "சம்பள ரசீது",
        "biometric punch", "attendance portal", "varugai", "வருகை"
    ]) and not any(k in q_norm for k in ["calendar", "holiday", "holidays 2026"]):
        return RESOURCE_REGISTRY["APP_HRMS"]

    # 6. Resignation & Job Protocols (HRM Manual)
    if any(k in q_norm for k in [
        "resignation", "resign", "relieving", "notice period", "exit clearance",
        "rajinama", "raajinaama", "பணி விலகல்", "ராஜினாமா", "procedure resignation job form",
        "no dues", "nodues"
    ]):
        return RESOURCE_REGISTRY["FORM_RESIGNATION_HRM"]

    # 7. Staff & Faculty Applications
    if any(k in q_norm for k in ["non teaching", "non-teaching", "staff recruitment", "job application form for staff"]):
        return RESOURCE_REGISTRY["FORM_NON_TEACHING"]
    if any(k in q_norm for k in ["teaching faculty", "teaching application", "faculty appraisal"]):
        return RESOURCE_REGISTRY["FORM_TEACHING"]

    # 8. IT Hardware & Telecom Forms
    if any(k in q_norm for k in ["system request", "system requisition", "new computer request", "kanini request", "கணினி கோரிக்கை", "கணினி படிவம்", "desktop system form"]):
        return RESOURCE_REGISTRY["FORM_SYSTEM"]

    if any(k in q_norm for k in ["printer request", "printer repair", "printer form", "toner replacement", "acchaagam padivam", "அச்சக படிவம்", "பிரிண்டர் படிவம்"]):
        return RESOURCE_REGISTRY["FORM_PRINTER"]

    if any(k in q_norm for k in ["visiting consultant", "visiting consultant requisition", "consultant requisition"]):
        return RESOURCE_REGISTRY["FORM_VISITING_CONSULTANT"]

    if any(k in q_norm for k in ["official email", "email form", "email id request", "மின்னஞ்சல் படிவம்"]):
        return RESOURCE_REGISTRY["FORM_EMAIL_ID"]

    if any(k in q_norm for k in ["sim cug", "cug sim", "sim request", "cug form", "cug sim padivam"]):
        return RESOURCE_REGISTRY["FORM_SIM_CUG"]

    # 9. Core Clinical & Operational Apps
    if "pacs" in tokens or "medsynapse" in q_norm or any(k in q_norm for k in ["xray scan", "scan paakanum", "ct scan viewer"]):
        return RESOURCE_REGISTRY["APP_PACS"]

    if "mrd" in tokens or any(k in q_norm for k in ["discharge summary archive", "mrd records", "case sheet archive"]):
        return RESOURCE_REGISTRY["APP_MRD"]

    if "mhc" in tokens or any(k in q_norm for k in ["master health", "மாஸ்டர் ஹெல்த் செக்கப்"]):
        return RESOURCE_REGISTRY["APP_MHC"]

    if "lineloom" in tokens or any(k in q_norm for k in ["opd token", "opd queue display", "opd token machine", "token machine"]):
        return RESOURCE_REGISTRY["APP_LINELOOM"]

    if any(k in q_norm for k in ["barcode", "pathology barcode", "lab barcode", "sample barcode"]):
        return RESOURCE_REGISTRY["APP_BARCODE"]

    if any(k in q_norm for k in ["eye camp", "eyecamp", "ophthalmology camp", "கண் முகாம்"]):
        return RESOURCE_REGISTRY["APP_EYECAMP"]

    if any(k in q_norm for k in ["counselling app", "counselling application", "counselling software", "counselling & icu", "counselling and icu", "icu app"]):
        return RESOURCE_REGISTRY["APP_COUNSELLING"]

    if any(k in q_norm for k in ["ticketing", "maintenance desk", "it breakdown", "lodge ticket", "it ticket", "breakdown ticket"]):
        return RESOURCE_REGISTRY["APP_TICKETING"]

    # Checklists (Apps vs Paper Forms)
    if any(k in q_norm for k in ["non clinical checklist", "non-clinical checklist", "gencl"]):
        return RESOURCE_REGISTRY["APP_NON_CLINICAL_CHECKLIST"]

    if any(k in q_norm for k in [
        "clinical checklist", "checklist app", "checklist application", "checklist software",
        "clinical audit app", "audit app"
    ]):
        return RESOURCE_REGISTRY["APP_CLINICAL_CHECKLIST"]

    # 10. Clinical Checklists & Forms
    if any(k in q_norm for k in ["handing over sbar", "sbar sheet", "sbar record", "sbar"]) and not any(k in q_norm for k in ["protocol", "policy", "manual", "sop", "guideline"]):
        return RESOURCE_REGISTRY["FORM_SBAR"]

    if any(k in q_norm for k in ["ward shifting", "ward shift"]):
        return RESOURCE_REGISTRY["FORM_WARD_SHIFTING"]

    if any(k in q_norm for k in ["icu casesheet checklist", "icu checklist"]):
        return RESOURCE_REGISTRY["FORM_ICU_CASESHEET"]

    if any(k in q_norm for k in ["mews score", "mews"]) and not any(k in q_norm for k in ["protocol", "policy", "manual", "sop", "guideline"]):
        return RESOURCE_REGISTRY["FORM_MEWS"]

    if any(k in q_norm for k in ["emergency patient transfer", "patient transfer record"]):
        return RESOURCE_REGISTRY["FORM_EMERGENCY_TRANSFER"]

    if any(k in q_norm for k in ["food token", "unavu token", "சாப்பாடு டோக்கன்"]):
        return RESOURCE_REGISTRY["FORM_FOOD_TOKEN"]

    # 11. Circulars & Holidays
    if any(k in q_norm for k in ["holidays 2026", "holiday calendar 2026", "list of holidays 2026", "விடுமுறை பட்டியல் 2026"]):
        return RESOURCE_REGISTRY["DOC_HOLIDAYS_2026"]

    if any(k in q_norm for k in ["recent circulars", "recent circular", "circulars", "சுற்றறிக்கை"]):
        return RESOURCE_REGISTRY["DIR_CIRCULARS"]

    if any(k in q_norm for k in ["where is the forms section", "forms section", "forms vault", "forms hub"]):
        return RESOURCE_REGISTRY["DIR_FORMS_HUB"]

    # 12. Committee Searches
    if intent == SearchIntent.FIND_COMMITTEE:
        if "infection control" in q_norm or "hicc" in q_norm:
            return RESOURCE_REGISTRY["DOC_HICC_CHARTER"]
        return RESOURCE_REGISTRY["DIR_COMMITTEES"]

    return None

