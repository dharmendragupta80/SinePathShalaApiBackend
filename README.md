        # SinePathshala Backend (FastAPI)

This is a simple secure proxy backend that safely stores your Gemini API key on the server and exposes a single endpoint for your Android app.

## Features
- FastAPI based
- Optional small `CLIENT_KEY` header check to reduce casual abuse
- CORS enabled (restrict origins in production)
- Dockerfile included for easy deploy

## Files
- `main.py` - FastAPI app with `/ask` endpoint
- `auth.py` - simple client-key verification dependency
- `requirements.txt` - Python dependencies
- `Dockerfile` - container image build file
- `.env.example` - example environment variables

## Usage (local)
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` with `GEMINI_KEY` set (or set env vars directly):

```bash
export GEMINI_KEY=YOUR_GEMINI_KEY
# optional:
export CLIENT_KEY=some_small_value
```

3. Run the server:

```bash
uvicorn main:app --reload --port 8080
```

4. Test with curl (include x-client-key header if you set CLIENT_KEY):

```bash
curl -X POST http://localhost:8080/ask -H "Content-Type: application/json" -d '{"question":"Hello"}'
```

## Deploy
- Render, Railway, Cloud Run and similar platforms work well. Set `GEMINI_KEY` and optional `CLIENT_KEY` as platform environment variables.

## Android Integration (high-level)
- Replace direct Gemini calls with POST to `https://your-backend-url/ask`.
- If you set `CLIENT_KEY`, send header `x-client-key` with the small value.
- Do not store `GEMINI_KEY` in the Android app.

## Production notes
- Restrict CORS to your app's domains/apps.
- Add rate-limiting and monitoring.
- Implement authenticated user tokens (Firebase Auth) for per-user quotas.

