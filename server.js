#!/usr/bin/env node
// ==============================================================================
// Adhiparasakthi Hospitals & Research Institute (APH) Intranet Server
// Pure Node.js Implementation (Zero npm dependencies)
// ==============================================================================

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const url = require('node:url');
const { executeSearch } = require('./search_engine');

// Port Configuration: Default to 3000 (override via CLI arg or PORT env)
const PORT = parseInt(process.argv[2] || process.env.PORT || '3000', 10);
const BASE_DIR = __dirname;
const FILES_DIR = path.join(BASE_DIR, 'files');
const DATA_DIR = path.join(BASE_DIR, 'data');

// MIME Types
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.pdf': 'application/pdf',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  '.txt': 'text/plain; charset=utf-8'
};

// Security Blocklist: sensitive patterns
const BLOCKED_PATTERNS = [
  /^\/\.env/i,
  /\/\.git/i,
  /\/\.gemini/i,
  /\.py$/i,
  /\.sh$/i,
  /\.db$/i,
  /search_index/i,
  /\.\./
];

// Common Headers (Security + Strict Cache-Busting)
function setCommonHeaders(contentType, extra = {}) {
  return {
    'Content-Type': contentType,
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache',
    'Expires': '0',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Session-Token',
    ...extra
  };
}

// ------------------------------------------------------------------------------
// HTTP Server
// ------------------------------------------------------------------------------
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  let pathname = parsedUrl.pathname || '/';

  // Security Check: Block sensitive files
  if (BLOCKED_PATTERNS.some(p => p.test(pathname))) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Access Denied: Sensitive file or configuration is strictly prohibited.');
    return;
  }

  // CORS Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, setCommonHeaders('text/plain'));
    res.end();
    return;
  }

  // API Route: /api/ai-search & /api/search (Supports POST and GET)
  if (pathname === '/api/ai-search' || pathname === '/api/search') {
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        try {
          const data = body ? JSON.parse(body) : {};
          const query = (data.query || '').trim();
          const result = executeSearch(query);

          let jsonStr = JSON.stringify(result);
          if (PORT !== 3000) {
            jsonStr = jsonStr.replace(/:3000/g, `:${PORT}`);
          }

          const outBytes = Buffer.from(jsonStr, 'utf-8');
          res.writeHead(200, setCommonHeaders('application/json; charset=utf-8', {
            'Content-Length': outBytes.length
          }));
          res.end(outBytes);
        } catch (err) {
          const errBytes = Buffer.from(JSON.stringify({ error: 'Invalid JSON payload' }), 'utf-8');
          res.writeHead(400, setCommonHeaders('application/json; charset=utf-8', {
            'Content-Length': errBytes.length
          }));
          res.end(errBytes);
        }
      });
      return;
    } else if (req.method === 'GET') {
      const query = (parsedUrl.query.q || parsedUrl.query.query || '').trim();
      const result = executeSearch(query);

      let jsonStr = JSON.stringify(result);
      if (PORT !== 3000) {
        jsonStr = jsonStr.replace(/:3000/g, `:${PORT}`);
      }

      const outBytes = Buffer.from(jsonStr, 'utf-8');
      res.writeHead(200, setCommonHeaders('application/json; charset=utf-8', {
        'Content-Length': outBytes.length
      }));
      res.end(outBytes);
      return;
    }
  }

  // API Route: /api/auth/logout
  if (pathname === '/api/auth/logout' && req.method === 'POST') {
    const resp = JSON.stringify({ status: 'success', message: 'Successfully logged out.' });
    res.writeHead(200, setCommonHeaders('application/json; charset=utf-8', {
      'Set-Cookie': 'aph_session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Lax'
    }));
    res.end(resp);
    return;
  }

  // Static File Serving (GET/HEAD only)
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, setCommonHeaders('text/plain'));
    res.end('Method Not Allowed');
    return;
  }

  // Default to index.html for root path
  if (pathname === '/') {
    pathname = '/index.html';
  }

  // URL decoding for filenames with spaces (e.g. "His%20User%20Creation.pdf")
  let decodedPath = '';
  try {
    decodedPath = decodeURIComponent(pathname);
  } catch (e) {
    decodedPath = pathname;
  }

  // Resolve file location on disk
  let filePath = path.join(BASE_DIR, decodedPath);

  // If path starts with /files/, check files directory, root, and pdf_cache (including subdirs and basenames)
  if (decodedPath.startsWith('/files/')) {
    const filename = decodedPath.replace(/^\/files\//, '');
    const baseName = path.basename(filename);
    const cleanName = filename.replace(/[^a-zA-Z0-9_\-\.]/g, '_');
    const cleanBase = baseName.replace(/[^a-zA-Z0-9_\-\.]/g, '_');

    const candidates = [
      path.join(FILES_DIR, filename),
      path.join(BASE_DIR, filename),
      path.join(FILES_DIR, baseName),
      path.join(BASE_DIR, baseName),
      path.join(DATA_DIR, 'pdf_cache', baseName),
      path.join(DATA_DIR, 'pdf_cache', cleanBase),
      path.join(DATA_DIR, 'pdf_cache', cleanName)
    ];

    for (const cand of candidates) {
      try {
        if (fs.existsSync(cand) && fs.statSync(cand).isFile()) {
          filePath = cand;
          break;
        }
      } catch (e) {}
    }
  }

  // Ensure path is within BASE_DIR (prevent directory traversal, Windows case-insensitive safe)
  const resolvedPath = path.resolve(filePath);
  const resolvedBase = path.resolve(BASE_DIR);
  if (!resolvedPath.toLowerCase().startsWith(resolvedBase.toLowerCase())) {
    res.writeHead(403, setCommonHeaders('text/plain'));
    res.end('Forbidden');
    return;
  }

  // Check file existence
  fs.stat(resolvedPath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, setCommonHeaders('text/html; charset=utf-8'));
      res.end(`<!DOCTYPE html><html><head><title>404 Not Found</title></head><body style="font-family:sans-serif;padding:40px;text-align:center;"><h2>404 - Document Not Found</h2><p>The requested file <code>${pathname}</code> was not found on this intranet server.</p><a href="/" style="color:#2563eb;font-weight:bold;">Return to Intranet Portal &rarr;</a></body></html>`);
      return;
    }

    const ext = path.extname(resolvedPath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    // For HTML, JSON, and JS, adapt hardcoded :3000 to custom PORT if needed
    if (PORT !== 3000 && (ext === '.html' || ext === '.json' || ext === '.js')) {
      fs.readFile(resolvedPath, 'utf8', (readErr, content) => {
        if (readErr) {
          res.writeHead(500, setCommonHeaders('text/plain'));
          res.end('Internal Server Error');
          return;
        }

        const adapted = content.replace(/:3000/g, `:${PORT}`);
        const outBuf = Buffer.from(adapted, 'utf-8');
        res.writeHead(200, setCommonHeaders(contentType, { 'Content-Length': outBuf.length }));
        if (req.method === 'HEAD') {
          res.end();
        } else {
          res.end(outBuf);
        }
      });
      return;
    }

    // Stream other files (PDFs, images, etc.)
    res.writeHead(200, setCommonHeaders(contentType, { 'Content-Length': stats.size }));
    if (req.method === 'HEAD') {
      res.end();
      return;
    }

    const stream = fs.createReadStream(resolvedPath);
    stream.pipe(res);
    stream.on('error', () => {
      if (!res.headersSent) {
        res.writeHead(500, setCommonHeaders('text/plain'));
        res.end('Internal Server Error');
      }
    });
  });
});

// ------------------------------------------------------------------------------
// Start Server
// ------------------------------------------------------------------------------
server.listen(PORT, '0.0.0.0', () => {
  console.log(`========================================================================`);
  console.log(`🏥 APH Hospital Intranet Server (Node.js Engine) Running on Port: ${PORT}`);
  console.log(`🌐 Localhost:     http://localhost:${PORT}`);
  console.log(`🌐 Hospital LAN:  http://192.168.101.75:${PORT}`);
  console.log(`🚀 Ready to serve clinical records, forms vault, & AI search.`);
  console.log(`========================================================================`);
});
