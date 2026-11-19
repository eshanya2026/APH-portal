// ==============================================================================
// Adhiparasakthi Hospitals & Research Institute (APH) Search Engine
// High-Fidelity Pure Node.js Port of server.py & search_registry.py
// ==============================================================================

const path = require('node:path');
const fs = require('node:fs');

const DATA_DIR = path.join(__dirname, 'data');
const REGISTRY = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'resource_registry.json'), 'utf8'));
const CATALOG = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'portal_catalog.json'), 'utf8'));
const INTERCOM = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'intercom.json'), 'utf8'));
const VOCAB = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'search_vocabulary.json'), 'utf8'));
const CANONICAL_RESPONSES = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'canonical_responses.json'), 'utf8'));
const INTERCOM_ALIASES = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'intercom_aliases.json'), 'utf8'));

let COMMITTEES = [];
try {
  COMMITTEES = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'committees.json'), 'utf8'));
} catch (e) {
  COMMITTEES = [];
}

let CIRCULARS = [];
try {
  CIRCULARS = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'circulars.json'), 'utf8'));
} catch (e) {
  CIRCULARS = [];
}

const TYPOS = VOCAB.typo_fixes || {};
const SYNONYMS = VOCAB.multilingual_synonyms || {};
const STOP_WORDS = new Set(VOCAB.stop_words || []);

// ------------------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------------------
function isTamilQuery(query) {
  if (!query) return false;
  return /[\u0B80-\u0BFF]/.test(query);
}

function fuzzyNormalizeQuery(q) {
  if (!q) return '';
  return q.toLowerCase()
    .replace(/[^a-z0-9\u0B80-\u0BFF\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanAndTokenize(text) {
  if (!text) return [];
  const norm = fuzzyNormalizeQuery(text);
  const rawTokens = norm.split(' ').filter(Boolean);
  return rawTokens.map(t => TYPOS[t] || t);
}

function anyInText(words, text) {
  if (!text) return false;
  const t = text.toLowerCase();
  return words.some(w => {
    if (/[\u0B80-\u0BFF]/.test(w)) return t.includes(w);
    const pat = new RegExp('\\b' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
    return pat.test(t);
  });
}

// ------------------------------------------------------------------------------
// Month MOM Engine (Matches server.py Stage 0a)
// ------------------------------------------------------------------------------
const MONTH_MOM_LOOKUP = {
  jan: ['jan', 'January', 'ஜனவரி'],
  january: ['jan', 'January', 'ஜனவரி'],
  'ஜனவரி': ['jan', 'January', 'ஜனவரி'],
  feb: ['feb', 'February', 'பிப்ரவரி'],
  february: ['feb', 'February', 'பிப்ரவரி'],
  'பிப்ரவரி': ['feb', 'February', 'பிப்ரவரி'],
  mar: ['mar', 'March', 'மார்ச்'],
  march: ['mar', 'March', 'மார்ச்'],
  'மார்ச்': ['mar', 'March', 'மார்ச்'],
  apr: ['apr', 'April', 'ஏப்ரல்'],
  april: ['apr', 'April', 'ஏப்ரல்'],
  'ஏப்ரல்': ['apr', 'April', 'ஏப்ரல்'],
  may: ['may', 'May', 'மே'],
  'மே': ['may', 'May', 'மே'],
  jun: ['jun', 'June', 'ஜூன்'],
  june: ['jun', 'June', 'ஜூன்'],
  'ஜூன்': ['jun', 'June', 'ஜூன்'],
  jul: ['jul', 'July', 'ஜூலை'],
  july: ['jul', 'July', 'ஜூலை'],
  'ஜூலை': ['jul', 'July', 'ஜூலை'],
  aug: ['aug', 'August', 'ஆகஸ்ட்'],
  august: ['aug', 'August', 'ஆகஸ்ட்'],
  'ஆகஸ்ட்': ['aug', 'August', 'ஆகஸ்ட்'],
  sep: ['sep', 'September', 'செப்டம்பர்'],
  sept: ['sep', 'September', 'செப்டம்பர்'],
  september: ['sep', 'September', 'செப்டம்பர்'],
  'செப்டம்பர்': ['sep', 'September', 'செப்டம்பர்'],
  oct: ['oct', 'October', 'அக்டோபர்'],
  october: ['oct', 'October', 'அக்டோபர்'],
  'அக்டோபர்': ['oct', 'October', 'அக்டோபர்'],
  nov: ['nov', 'November', 'நவம்பர்'],
  november: ['nov', 'November', 'நவம்பர்'],
  'நவம்பர்': ['nov', 'November', 'நவம்பர்'],
  dec: ['dec', 'December', 'டிசம்பர்'],
  december: ['dec', 'December', 'டிசம்பர்'],
  'டிசம்பர்': ['dec', 'December', 'டிசம்பர்']
};

const MONTH_PATTERNS = {
  jan: /\bJAN(UARY)?\b/i,
  feb: /\bFEB(RUARY)?\b/i,
  mar: /\bMAR(CH)?\b/i,
  apr: /\bAPR(IL)?\b/i,
  may: /\bMAY\b/i,
  jun: /\bJUN(E)?\b/i,
  jul: /\bJUL(Y)?\b|\bJULY?[- ]/i,
  aug: /\bAUG(UST)?\b/i,
  sep: /\bSEP(T|TEMBER)?\b/i,
  oct: /\bOCT(OBER)?\b/i,
  nov: /\bNOV(EMBER)?\b/i,
  dec: /\bDEC(EMBER)?\b/i
};

const COMMITTEE_ACRONYM_NAMES = {
  BMW: ['Bio-Medical Waste Committee', 'பயோ-மெடிக்கல் கழிவு மேலாண்மைக் குழு'],
  CAC: ['Clinical Audit Committee', 'மருத்துவ தணிக்கைக் குழு'],
  QC: ['Quality Committee', 'தரக் கட்டுப்பாட்டுக் குழு'],
  BTC: ['Blood Transfusion Committee', 'இரத்த மாற்று சிகிச்சை குழு'],
  DTC: ['Drugs & Therapeutics Committee', 'மருந்துகள் & சிகிச்சைக் குழு'],
  FMS: ['Facility Management & Safety Committee', 'வசதி மேலாண்மை & பாதுகாப்பு குழு'],
  HR: ['Human Resources Committee', 'மனிதவளக் குழு'],
  CPC: ['Clinical Protocol Committee', 'மருத்துவ சிகிச்சை நெறிமுறைக் குழு'],
  CPR: ['Cardiopulmonary Resuscitation (Code Blue) Committee', 'அவசர சிகிச்சை மீட்புக் குழு (Code Blue)'],
  IPC: ['Infection Prevention & Control Committee', 'தொற்று தடுப்பு & கட்டுப்பாட்டுக் குழு'],
  HIC: ['Hospital Infection Control Committee', 'மருத்துவமனை தொற்று கட்டுப்பாட்டுக் குழு'],
  HICC: ['Hospital Infection Control Committee', 'மருத்துவமனை தொற்று கட்டுப்பாட்டுக் குழு'],
  MRD: ['Medical Records Department Committee', 'மருத்துவ பதிவேடுகள் துறை குழு'],
  AMS: ['Antimicrobial Stewardship Committee', 'ஆன்டிமைக்ரோபியல் பயன்பாட்டு கண்காணிப்புக் குழு'],
  PURCHASE: ['Purchase & Procurement Committee', 'கொள்முதல் & உபகரணக் குழு'],
  'M&M': ['Mortality & Morbidity Committee', 'இறப்பு மற்றும் நோய் விகித ஆய்வுக் குழு']
};

function resolveMonthMomQuery(query) {
  if (!COMMITTEES.length) return null;
  const qNorm = query.toLowerCase().trim();
  const words = qNorm.match(/[\w\u0B80-\u0BFF]+/g) || [];

  let matchedMonth = null;
  for (const w of words) {
    if (MONTH_MOM_LOOKUP[w]) {
      matchedMonth = MONTH_MOM_LOOKUP[w];
      break;
    }
  }
  if (!matchedMonth) return null;

  const [mKey, mEn, mTa] = matchedMonth;
  const hasMom = words.some(w => ['mom', 'moms', 'meeting', 'minutes'].includes(w)) ||
    qNorm.includes('கூட்ட அறிக்கை') || qNorm.includes('meeting minutes') || qNorm.includes('minutes of meeting');
  const isPureMonth = Object.keys(MONTH_MOM_LOOKUP).some(k => k.length > 3 && (qNorm === k || qNorm === `${k} month`));

  if (!hasMom && !isPureMonth) return null;

  const pat = MONTH_PATTERNS[mKey] || new RegExp('\\b' + mKey + '\\b', 'i');
  const matchedDocs = COMMITTEES.filter(d => pat.test(d.title || ''));
  if (!matchedDocs.length) return null;

  const isTamil = isTamilQuery(query);
  const docLines = [];
  const links = [
    {
      title: `Open Committees & MOM Hub (${mEn} Filter)`,
      url: `./comitee.html?q=${mKey}`,
      category: 'Governance Directory',
      badge: `${mEn} Directory`,
      access_level: 'PUBLIC'
    }
  ];

  matchedDocs.forEach((d, idx) => {
    const title = (d.title || '').trim();
    const docUrl = (d.url || '').trim();
    let commEn = 'Hospital Committee';
    let commTa = 'மருத்துவமனை குழு';

    for (const [acro, names] of Object.entries(COMMITTEE_ACRONYM_NAMES)) {
      if (new RegExp('\\b' + acro + '\\b', 'i').test(title)) {
        commEn = `${names[0]} (${acro})`;
        commTa = `${names[1]} (${acro})`;
        break;
      }
    }

    if (isTamil) {
      docLines.push(`${idx + 1}. **${commTa}**: [${title}](${docUrl})`);
    } else {
      docLines.push(`${idx + 1}. **${commEn}**: [${title}](${docUrl})`);
    }

    links.push({
      title: `${title} - ${commEn}`,
      url: docUrl,
      category: 'Hospital Committee Minutes (MOM)',
      badge: `${mEn} MOM`,
      access_level: 'STAFF'
    });
  });

  const docsListText = docLines.join('\n');
  let answer = '';
  if (isTamil) {
    answer = `📋 **${mTa} மாதத்திற்கான அதிகாரப்பூர்வ குழு கூட்ட அறிக்கைகள் (${matchedDocs.length} ஆவணங்கள் காணப்பட்டன)**:\n\n` +
      `மருத்துவமனை நிர்வாகம் மற்றும் தரக் கட்டுப்பாட்டுக் குழுக்களின் அதிகாரப்பூர்வ **${mTa} Minutes of Meeting (MOM)** ஆவணங்கள் கீழே பட்டியலிடப்பட்டுள்ளன:\n\n` +
      `${docsListText}\n\n` +
      `📁 அனைத்து குழு ஆவணங்களையும் தேடவும் ஆய்வு செய்யவும் **[Hospital Committees & MOM Directory](./comitee.html?q=${mKey})** திறக்கவும்.`;
  } else {
    answer = `📋 **${mEn} Minutes of Meeting (MOM) Records (${matchedDocs.length} Documents Found)**:\n\n` +
      `Here are the official verified **${mEn} Minutes of Meeting (MOM)** records for hospital governance and quality committees:\n\n` +
      `${docsListText}\n\n` +
      `📁 To view and search all committee documents with live keyword highlighting, open the **[Hospital Committees & MOM Directory](./comitee.html?q=${mKey})**.`;
  }

  const allMonths = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
  const curIdx = allMonths.indexOf(mKey);
  const prevM = MONTH_MOM_LOOKUP[allMonths[(curIdx - 1 + 12) % 12]][1];
  const nextM = MONTH_MOM_LOOKUP[allMonths[(curIdx + 1) % 12]][1];

  return {
    answer,
    links,
    suggestions: [
      `${nextM} MOM`,
      `${prevM} MOM`,
      'Committee Scheduled Calendar 2026',
      'List of Committees'
    ],
    auto_open_url: `./comitee.html?q=${mKey}`,
    auto_open_title: `APH Hospital Committees - ${mEn} MOM Directory`,
    access_status: 'AUTHORIZED',
    grounding_status: 'GROUNDED_CATALOG'
  };
}

// ------------------------------------------------------------------------------
// Year Circulars Engine (Matches server.py Stage 0b)
// ------------------------------------------------------------------------------
const YEAR_CIRCULAR_KEYWORDS = new Set(['circular', 'circulars', 'order', 'orders', 'memo', 'memos', 'bulletin', 'bulletins', 'சுற்றறிக்கை', 'சுற்றறிக்கைகள்']);

function resolveYearCircularQuery(query) {
  if (!CIRCULARS.length) return null;
  const qNorm = query.toLowerCase().trim();
  const yearMatch = qNorm.match(/\b(202[0-9])\b/);
  if (!yearMatch) return null;

  const year = yearMatch[1];
  const words = qNorm.match(/[\w\u0B80-\u0BFF]+/g) || [];
  const hasCirc = words.some(w => YEAR_CIRCULAR_KEYWORDS.has(w)) ||
    qNorm.includes('சுற்றறிக்கை') || qNorm.includes('office order') || qNorm.includes('circular');
  if (!hasCirc) return null;

  const matchedCircs = CIRCULARS.filter(c => (c.title || '').includes(year) || (c.date || '').includes(year));
  if (!matchedCircs.length) return null;

  const isTamil = isTamilQuery(query);
  const docLines = [];
  const links = [
    {
      title: `APH Recent Circulars Hub (${year} Filter)`,
      url: `./recent circular.html?q=${year}`,
      category: 'Circulars Hub',
      badge: `${year} Circulars`,
      access_level: 'PUBLIC'
    }
  ];

  matchedCircs.forEach((c, idx) => {
    const title = (c.title || '').trim();
    const circUrl = (c.url || '').trim();
    const dateStr = (c.date || '').trim();
    const dateInfo = dateStr ? ` (${isTamil ? 'தேதி' : 'Date'}: ${dateStr})` : '';
    docLines.push(`${idx + 1}. **[${title}](${circUrl})**${dateInfo}`);
    links.push({
      title: dateStr ? `${title} (${dateStr})` : title,
      url: circUrl,
      category: 'Hospital Circulars',
      badge: `${year} Circular`,
      access_level: 'STAFF'
    });
  });

  const docsListText = docLines.join('\n');
  let answer = '';
  if (isTamil) {
    answer = `📋 **${year} ஆம் ஆண்டிற்கான அதிகாரப்பூர்வ மருத்துவமனை சுற்றறிக்கைகள் (${matchedCircs.length} ஆவணங்கள்)**:\n\n` +
      `${year} ஆம் ஆண்டிற்கான மருத்துவமனை நிர்வாக மற்றும் பாதுகாப்பு சுற்றறிக்கைகள் கீழே பட்டியலிடப்பட்டுள்ளன:\n\n` +
      `${docsListText}\n\n` +
      `📁 அனைத்து சுற்றறிக்கைகளையும் பார்வையிட **[APH Recent Circulars Hub (${year})](./recent circular.html?q=${year})** திறக்கவும்.`;
  } else {
    answer = `📋 **Official ${year} Hospital Circulars & Management Orders (${matchedCircs.length} Documents Found)**:\n\n` +
      `Here are the official verified institutional circulars and management notifications issued for **${year}**:\n\n` +
      `${docsListText}\n\n` +
      `📁 To view and search all circulars with live keyword highlighting, open the **[APH Recent Circulars Hub (${year} Filter)](./recent circular.html?q=${year})**.`;
  }

  return {
    answer,
    links,
    suggestions: [
      'Safety Meeting Circular- 2026',
      'SWOT Analysis Circular Jan 2026',
      'List of Holidays 2026',
      'Digital E – Circulars & Protocols'
    ],
    auto_open_url: `./recent circular.html?q=${year}`,
    auto_open_title: `APH Recent Circulars - ${year}`,
    access_status: 'AUTHORIZED',
    grounding_status: 'GROUNDED_CATALOG'
  };
}

// ------------------------------------------------------------------------------
// Intercom Telephony Engine (Matches server.py Stage 1 & generate_catalog_fallback_result)
// ------------------------------------------------------------------------------
function isTelephonyQuery(query) {
  const q = query.toLowerCase();
  return /\b(intercom|extension|extensions|ext|exts|phone|phones|telephone|telephones|call|calling|calls|dial|dialing|number|numbers|contact)\b/i.test(q) ||
    /(தொலைபேசி|இணைப்பு|எண்|போன்|கால்|கூப்பிடு|பேசு|தொடர்பு|இன்டர்காம்)/.test(query);
}

function findIntercomDepartment(query) {
  if (!INTERCOM.length || !query) return null;
  const qClean = query.toLowerCase().trim();

  // 1. Match specific department aliases first (handles HR, IT, Billing, Casualty, Dietetics, Canteen, etc.)
  const aliasKeys = Object.keys(INTERCOM_ALIASES).sort((a, b) => b.length - a.length);
  for (const aliasKey of aliasKeys) {
    const aliasInfo = INTERCOM_ALIASES[aliasKey];
    let matched = false;
    if (/[\u0B80-\u0BFF]/.test(aliasKey)) {
      matched = qClean.includes(aliasKey);
    } else {
      const pat = new RegExp('\\b' + aliasKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
      matched = pat.test(qClean);
    }

    if (matched) {
      const targetDept = (aliasInfo.target_dept || '').toLowerCase();
      const matchedDepts = INTERCOM.filter(d => {
        const dName = (d.dept || '').toLowerCase();
        return dName === targetDept || dName.startsWith(targetDept + ' ') || targetDept.startsWith(dName + ' ');
      });

      if (matchedDepts.length) {
        const allExts = [];
        const floors = [];
        const primaryDeptName = matchedDepts[0].dept || '';

        for (const d of matchedDepts) {
          const dFloor = (d.floor || '').trim();
          if (dFloor && !floors.includes(dFloor)) floors.push(dFloor);

          for (const e of (d.extensions || [])) {
            const desc = (e.desc || '').trim();
            const extVal = String(e.ext || '').trim();
            if (aliasInfo.filter_descs && aliasInfo.filter_descs.length) {
              const matchedFilter = aliasInfo.filter_descs.some(fd => {
                const pat = new RegExp('\\b' + fd.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
                return pat.test(desc.toLowerCase());
              });
              if (matchedFilter) allExts.push({ desc, ext: extVal });
            } else {
              allExts.push({ desc, ext: extVal });
            }
          }
        }

        return {
          dept: aliasInfo.dept_label || primaryDeptName,
          dept_label: aliasInfo.dept_label || primaryDeptName,
          floor: floors.join(', '),
          extensions: allExts.slice(0, 8)
        };
      }
    }
  }

  // 2. Token-based matching across all 61 departments with whole-word regex
  const stopWordsTelephony = new Set([
    'i', 'need', 'the', 'extension', 'intercom', 'inercom', 'number', 'for', 'what', 'is', 'of', 'in',
    'phone', 'phones', 'telephone', 'telephones', 'contact', 'ext', 'exts', 'numbers', 'extensions',
    'please', 'give', 'me', 'tell', 'help', 'call', 'calling', 'calls', 'dial', 'dialing', 'to', 'how', 'want',
    'dr', 'doctor', 'staff', 'room', 'dept', 'department'
  ]);

  const rawWords = (qClean.match(/[a-zA-Z0-9\u0B80-\u0BFF]+/g) || [])
    .filter(w => !stopWordsTelephony.has(w) && w.length > 2);
  if (!rawWords.length) return null;

  const scoredResults = [];
  for (const d of INTERCOM) {
    const dept = (d.dept || '').trim();
    const floor = (d.floor || '').trim();
    const exts = d.extensions || [];
    const deptLower = dept.toLowerCase();
    let deptScore = 0;
    const matchingExts = [];

    for (const w of rawWords) {
      const pat = new RegExp('\\b' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
      if (pat.test(deptLower)) {
        deptScore += 500;
      }
      for (const e of exts) {
        const descLower = (e.desc || '').toLowerCase();
        const extNum = String(e.ext || '').trim();
        if (pat.test(descLower)) {
          matchingExts.push({ ext: e, score: 200 });
        } else if (w === extNum || extNum.startsWith(w)) {
          matchingExts.push({ ext: e, score: 400 });
        }
      }
    }

    const seenExt = new Set();
    const finalExts = [];
    matchingExts.sort((a, b) => b.score - a.score).forEach(item => {
      const cleanDesc = (item.ext.desc || '').trim();
      const cleanExt = String(item.ext.ext || '').trim();
      if (!seenExt.has(cleanExt)) {
        seenExt.add(cleanExt);
        finalExts.push({ desc: cleanDesc, ext: cleanExt });
      }
    });

    const totalScore = deptScore + matchingExts.reduce((sum, item) => sum + item.score, 0);
    if (totalScore > 0) {
      if (!finalExts.length) {
        exts.slice(0, 6).forEach(e => {
          finalExts.push({ desc: (e.desc || '').trim(), ext: String(e.ext || '').trim() });
        });
      }
      scoredResults.push({
        score: totalScore,
        data: {
          dept,
          dept_label: dept,
          floor,
          extensions: finalExts
        }
      });
    }
  }

  scoredResults.sort((a, b) => b.score - a.score);
  return scoredResults.length ? scoredResults[0].data : null;
}

function buildIntercomResponse(query, matchedDept) {
  const isTamil = isTamilQuery(query);
  const deptLabel = matchedDept.dept_label || matchedDept.dept;
  const deptUrl = deptLabel ? `./intercom.html?dept=${encodeURIComponent(deptLabel)}` : './intercom.html';
  const extStrs = (matchedDept.extensions || []).slice(0, 6).map(e => `**${e.desc}: ${e.ext}**`);
  const floorInfo = matchedDept.floor ? ` (${matchedDept.floor})` : '';

  let answer = '';
  let suggestions = [];

  if (isTamil) {
    answer = `**${deptLabel}** துறையின் அதிகாரப்பூர்வ தொலைபேசி / இன்டர்காம் இணைப்பு எண்கள்: ${extStrs.join(', ')}. முழுமையான துறை தொடர்பு பட்டியலை கீழே உள்ள இணைப்பில் பார்க்கலாம்.`;
    suggestions = [
      `${deptLabel} Ext: ${matchedDept.extensions && matchedDept.extensions[0] ? matchedDept.extensions[0].ext : '2001'}`,
      `${deptLabel} Intercom Directory`,
      'அவசர பிரிவு: 2001 / 2800'
    ];
  } else {
    answer = `The intercom extension numbers for **${deptLabel}**${floorInfo} are: ${extStrs.join(', ')}. You can access the department directory below.`;
    suggestions = [
      `${deptLabel} Ext: ${matchedDept.extensions && matchedDept.extensions[0] ? matchedDept.extensions[0].ext : '2001'}`,
      `${deptLabel} Intercom Directory`,
      'Campus Directory'
    ];
  }

  const links = [
    {
      title: `${deptLabel} Department Intercom Directory`,
      url: deptUrl,
      category: 'Staff Directory',
      badge: `${deptLabel} Directory`
    },
    {
      title: 'Official Campus Intercom Directory (Full Hospital)',
      url: 'http://192.168.101.75/assets/sub%20files/intercom.html',
      category: 'Staff Directory',
      badge: 'Full Directory'
    }
  ];

  return { answer, links, suggestions };
}

function buildGeneralTelephonyResponse(query) {
  const isTamil = isTamilQuery(query);
  if (isTamil) {
    return {
      answer: 'மருத்துவமனை அவசர உதவி மற்றும் முக்கிய துறை தொலைபேசி எண்கள்: அவசர சிகிச்சை (Casualty): 2001 / 2002, ரத்த வங்கி (24/7): 2131, தீவிர சிகிச்சை (ICU): 2156, மெயின் கேட்: 2800, கணினி உதவி மையம் (IT): 2226 / 2228. அனைத்து துறை எண்களையும் அதிகாரப்பூர்வ தொலைபேசி பட்டியல் அல்லது தேடல் பட்டியலில் பார்க்கலாம்.',
      suggestions: ['கணினி IT பிரிவு: 2226 / 2228', 'அவசர சிகிச்சை: 2001 / 2800', 'ரத்த வங்கி Ext: 2131'],
      links: [
        { title: 'Campus Intercom & Extension Directory', url: 'http://192.168.101.75/assets/sub%20files/intercom.html', category: 'Staff Directory', badge: 'Official Directory' },
        { title: 'Interactive Department Intercom List', url: './intercom.html', category: 'Staff Directory', badge: 'Directory' }
      ]
    };
  }
  return {
    answer: 'Hospital emergency hotlines and departmental lines: Emergency Reception: 2001 / 2002, Blood Bank: 2131, ICU: 2156, Main Gate: 2800, IT Support: 2226 / 2228. Find all department extension numbers in the official Campus Intercom & Extension Directory or searchable online list.',
    suggestions: ['IT Intercom: 2226 / 2228', 'Emergency Casualty: 2001 / 2800', 'Blood Bank Ext: 2131'],
    links: [
      { title: 'Campus Intercom & Extension Directory', url: 'http://192.168.101.75/assets/sub%20files/intercom.html', category: 'Staff Directory', badge: 'Official Directory' },
      { title: 'Interactive Department Intercom List', url: './intercom.html', category: 'Staff Directory', badge: 'Directory' }
    ]
  };
}

// ------------------------------------------------------------------------------
// Canonical Resource Resolution (Exact Registry Matching)
// ------------------------------------------------------------------------------
function resolveExactRegisteredResource(query) {
  if (!query) return null;
  const qLower = query.toLowerCase().trim();
  const qNorm = fuzzyNormalizeQuery(qLower.replace(/-/g, ' '));

  for (const [resId, res] of Object.entries(REGISTRY)) {
    if (res.id === 'DIR_INTERCOM_OFFICIAL' || res.id === 'DIR_INTERCOM_SEARCH') {
      // If query matches a specific department, let department intercom lookup handle it
      if (findIntercomDepartment(query)) {
        continue;
      }
    }

    const titleNorm = fuzzyNormalizeQuery((res.title || '').toLowerCase());
    if (qNorm === titleNorm) return res;

    // Direct alias check
    const aliases = res.aliases || [];
    for (const al of aliases) {
      const alLower = al.toLowerCase().trim();
      if (qLower === alLower) return res;
      if (qNorm === fuzzyNormalizeQuery(alLower)) return res;
      if (alLower.length > 3) {
        let matches = false;
        if (/[\u0B80-\u0BFF]/.test(alLower)) {
          matches = qLower.includes(alLower);
        } else {
          matches = new RegExp('\\b' + alLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i').test(qLower);
        }

        if (matches) {
          // Negative alias check
          const negs = res.negative_aliases || [];
          const hasNeg = negs.some(n => qLower.includes(n.toLowerCase()));
          if (!hasNeg) return res;
        }
      }
    }
  }

  return null;
}

// ------------------------------------------------------------------------------
// Master Search Pipeline (Replicates execute_search_pipeline from server.py)
// ------------------------------------------------------------------------------
function executeSearch(query) {
  const q = (query || '').trim();
  if (!q) {
    return {
      answer: 'Please enter a search query to locate clinical forms, staff directories, or hospital records.',
      links: [],
      suggestions: ['HIS Login', 'Intercom Directory', 'Recent Circulars', 'List of Holidays 2026']
    };
  }

  const isTamil = isTamilQuery(q);

  // Stage 0a: Month MOM Resolution FIRST
  const monthMom = resolveMonthMomQuery(q);
  if (monthMom) return monthMom;

  // Stage 0b: Year Circulars Resolution
  const yearCirc = resolveYearCircularQuery(q);
  if (yearCirc) return yearCirc;

  // Stage 0c: Exact Canonical Resource Resolution
  const exact = resolveExactRegisteredResource(q);
  if (exact) {
    // Check if handcrafted canonical response exists in CANONICAL_RESPONSES
    const stored = CANONICAL_RESPONSES[exact.id];
    if (stored) {
      const chosen = (isTamil && stored.ta) ? stored.ta : stored.en;
      return {
        ...chosen,
        auto_open: !!exact.is_app,
        auto_open_url: exact.target_url || exact.primary_url || (chosen.links && chosen.links[0] ? chosen.links[0].url : ''),
        auto_open_title: exact.title || '',
        is_app: !!exact.is_app
      };
    }

    // Default canonical response if not individually handcrafted
    return {
      answer: isTamil
        ? `அதிகாரப்பூர்வ மருத்துவமனை பதிவு: **${exact.title}**. கீழே உள்ள நேரடி இணைப்பைப் பயன்படுத்தி அணுகலாம்.`
        : `Official verified hospital resource: **${exact.title}**. Access the verified document below.`,
      links: [
        {
          title: exact.title,
          url: exact.primary_url || exact.target_url || '#',
          category: exact.category || 'Hospital Records',
          badge: exact.is_app ? 'System' : 'Document'
        }
      ],
      suggestions: [exact.title, 'Campus Directory', 'Forms Vault'],
      auto_open: !!exact.is_app,
      auto_open_url: exact.target_url || exact.primary_url || '',
      auto_open_title: exact.title,
      is_app: !!exact.is_app
    };
  }

  // Stage 1: Intercom Department & Telephony Lookups
  const isTelecom = isTelephonyQuery(q);
  const matchedDept = findIntercomDepartment(q);

  if (matchedDept && isTelecom) {
    return buildIntercomResponse(q, matchedDept);
  }

  if (isTelecom && !matchedDept) {
    return buildGeneralTelephonyResponse(q);
  }

  // If matched department and not asking for a form/manual, route to intercom
  if (matchedDept && !anyInText(['form', 'manual', 'sop', 'policy', 'tariff', 'pdf'], q)) {
    return buildIntercomResponse(q, matchedDept);
  }

  // Stage 2: Catalog Search Fallback
  const qNorm = fuzzyNormalizeQuery(q);
  const tokens = cleanAndTokenize(qNorm).filter(t => !STOP_WORDS.has(t));

  let bestMatch = null;
  let maxScore = 0;

  for (const item of CATALOG) {
    const titleNorm = fuzzyNormalizeQuery(item.title || '');
    const descNorm = fuzzyNormalizeQuery(item.description || '');
    let score = 0;

    for (const t of tokens) {
      if (titleNorm === t) score += 30;
      else if (new RegExp('\\b' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i').test(titleNorm)) score += 15;
      else if (titleNorm.includes(t)) score += 5;

      if (new RegExp('\\b' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i').test(descNorm)) score += 6;
    }

    if (score > maxScore) {
      maxScore = score;
      bestMatch = item;
    }
  }

  if (bestMatch && maxScore >= 10) {
    return {
      answer: isTamil
        ? `தேடல் முடிவு: **${bestMatch.title}** (${bestMatch.category || 'Hospital Document'}). ஆவணத்தை நேரடியாக கீழே திறந்து பார்க்கலாம்.`
        : `Found hospital record: **${bestMatch.title}** (${bestMatch.category || 'Hospital Document'}). Access the verified document below.`,
      links: [
        {
          title: bestMatch.title,
          url: bestMatch.url,
          category: bestMatch.category || 'Hospital Records',
          badge: bestMatch.badge || 'Document'
        }
      ],
      suggestions: [bestMatch.title, 'Campus Directory', 'Forms Vault'],
      auto_open: false
    };
  }

  // Final fallback
  return {
    answer: isTamil
      ? `**"${q}"** தொடர்பான ஆவணங்கள் அல்லது தொலைபேசி எண்கள் நேரடியாக கிடைக்கவில்லை. மருத்துவமனை இன்டர்காம் பட்டியல் அல்லது படிவங்கள் பிரிவை கீழே உள்ள இணைப்புகள் மூலம் பார்வையிடவும்.`
      : `No exact matches found for **"${q}"**. Please explore the Campus Intercom Directory or Forms Vault using the links below.`,
    links: [
      { title: 'Interactive Department Intercom List', url: './intercom.html', category: 'Staff Directory', badge: 'Directory' },
      { title: 'Hospital Forms Vault', url: './commonforms.html', category: 'Forms Vault', badge: 'Forms' }
    ],
    suggestions: ['Campus Intercom Directory', 'HIS Login', 'IT Helpdesk Ext: 2226']
  };
}

module.exports = {
  executeSearch,
  findIntercomDepartment,
  resolveMonthMomQuery,
  resolveYearCircularQuery,
  resolveExactRegisteredResource
};
