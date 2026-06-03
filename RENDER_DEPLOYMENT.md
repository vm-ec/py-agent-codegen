# Render Deployment Guide

## Issue: Gemini API Quota Exceeded (429 Error)

### Root Cause
Your Gemini API key has exceeded the **free tier quota limits**:
- Daily request limit
- Per-minute request limit  
- Input token limit

### Solutions

#### 1. **Switch to gemini-1.5-flash (Higher Free Limits)**
In Render Dashboard → Environment Variables:
```
MODEL_NAME=gemini-1.5-flash
```

#### 2. **Upgrade to Paid Tier**
- Visit: https://aistudio.google.com/apikey
- Enable billing on your Google Cloud project
- Paid tier has much higher limits

#### 3. **Wait for Quota Reset**
Free tier quotas reset every 24 hours. Check usage at: https://ai.dev/rate-limit

---

## Render Environment Setup

### Required Environment Variables
Set these in Render Dashboard → Your Service → Environment tab:

```bash
GEMINI_API_KEY=<your-gemini-api-key>
PROMPT_HUB_REPO=https://github.com/saikumar0210/prompt-hub-agent.git
MODEL_NAME=gemini-2.5-flash
GITHUB1_TOKEN=<your-github-token>
GITHUB1_USERNAME=saireddy-collab
PORT=8000
```

### Deployment Configuration

**For FastAPI (api.py) — Active:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Port: `8000`

---

## Code Changes Made

### Added Retry Logic with Exponential Backoff
All Gemini API calls now automatically retry on quota errors with delays:
- 1st retry: 10 seconds
- 2nd retry: 20 seconds
- 3rd retry: 40 seconds

### Files Updated
- `config/settings.py` - Added `generate_with_retry()` helper
- `agents/orchestrator.py` - Uses retry logic
- `agents/story_analyzer.py` - Uses retry logic
- `agents/repo_edit_agent.py` - Uses retry logic
- `runtime/execution_engine.py` - Uses retry logic
- `app.py` - Uses retry logic

---

## Security Warning

**NEVER commit `.env` file to Git!**

Your exposed credentials should be rotated immediately:
- `GEMINI_API_KEY` - Generate new key at https://aistudio.google.com/apikey
- `GITHUB1_TOKEN` - Revoke and create new at https://github.com/settings/tokens

Add to `.gitignore`:
```
.env
```
