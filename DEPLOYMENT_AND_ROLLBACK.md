# APH Portal AI Search Engine: Deployment & Rollback Instructions

**Document ID:** APH-DEPLOY-2026-PHASE2  
**Target Branch:** `feature/phase2-search-security-fixes`  
**Production Branch:** `main`  
**Host Environment:** Ubuntu Linux, Port 3000 (`http://localhost:3000` / `http://192.168.101.75:3000`)  
**Deployment Type:** Standard Zero-Downtime Hot-Reload  

---

## 1. Pre-Deployment Verification Checklist

Before deploying changes to production, ensure all automated verification checks pass:

```bash
# 1. Verify you are on the feature branch
git branch --show-current
# Expected output: feature/phase2-search-security-fixes

# 2. Run the automated regression test suite
python3 tests/test_search_regression.py
# Expected output: Ran 24 tests ... OK

# 3. Run the 34 benchmark evaluation script
python3 scripts/evaluate_34_queries.py
# Expected output: 34/34 PASSED (100.0%)
```

---

## 2. Production Deployment Steps

### Step 1: Commit Feature Branch Changes
```bash
git add server.py index.html search_registry.py tests/ scripts/
git commit -m "feat(search): Phase 2 critical fixes - Security remediation, Canonical Resource Registry, Intent Routing, and Multilingual expansion"
```

### Step 2: Merge into Main Branch
```bash
# Switch to main branch
git checkout main

# Merge feature branch
git merge --no-ff feature/phase2-search-security-fixes -m "merge: Phase 2 AI Search Engine Critical Fixes and Security Hardening"
```

### Step 3: Restart Server Process Cleanly
```bash
# Identify running server process on port 3000
PID=$(lsof -ti :3000)

# Gracefully terminate the old server process
if [ -n "$PID" ]; then
    kill -15 $PID
    sleep 1
fi

# Start updated multithreaded server in background
nohup python3 server.py > server.log 2>&1 &

# Confirm server is listening
sleep 1
curl -s -I http://localhost:3000/
# Expected output: HTTP/1.0 200 OK
```

### Step 4: Post-Deployment Smoke Test
```bash
# Verify security barrier blocks .env
curl -s -I http://localhost:3000/.env
# Expected: HTTP/1.0 403 Forbidden

# Verify search API functionality
curl -s -X POST http://localhost:3000/api/ai-search \
  -H "Content-Type: application/json" \
  -d '{"query": "open his"}' | grep "admin/login.aspx"
```

---

## 3. Gemini API Key Rotation Instructions

Since `.env` was previously accessible over the network prior to Phase 2:

1. **Obtain New Key:** Generate a new key in [Google AI Studio](https://aistudio.google.com/app/apikey).
2. **Update `.env` securely on the server host:**
   ```bash
   chmod 600 .env
   echo 'GEMINI_API_KEY="YOUR_NEW_API_KEY_HERE"' > .env
   ```
3. **Revoke Old Key:** Delete the old key in Google AI Studio.
4. **Restart Server:**
   ```bash
   kill -15 $(lsof -ti :3000) && nohup python3 server.py > server.log 2>&1 &
   ```

---

## 4. Rollback Plan

If an unforeseen operational issue occurs in production, execute the following rollback:

### Immediate Rollback (Under 30 Seconds)
```bash
# 1. Rollback git working tree to previous commit
git checkout main
git reset --hard HEAD~1

# 2. Restart server process
kill -15 $(lsof -ti :3000)
nohup python3 server.py > server.log 2>&1 &

# 3. Verify server state
curl -s -I http://localhost:3000/
```

### Rollback Verification
Confirm that the portal is serving traffic:
```bash
curl -s http://localhost:3000/ | grep -i "Adhiparasakthi"
```
