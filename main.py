from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
import httpx
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_client_key

app = FastAPI(title="SinePathshala Backend - FastAPI")

# Allow CORS from any origin for now (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_KEY = os.getenv("GEMINI_KEY")
if not GEMINI_KEY:
    # We don't raise here to allow local dev without env var; route will fail with proper error.
    print("WARNING: GEMINI_KEY environment variable not set. Set GEMINI_KEY before deploying.")

class AskRequest(BaseModel):
    question: str

@app.post("/ask", dependencies=[Depends(verify_client_key)])
async def ask(req: AskRequest):
    """Proxy endpoint that forwards the question to the Gemini generative language API and returns the JSON response."""
    if not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="Server misconfiguration: GEMINI_KEY not set on server.")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    params = {"key": GEMINI_KEY}
    body = {
        "contents": [
            {"parts": [{"text": req.question}]}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, params=params, json=body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream communication failed: {e}")

    if resp.status_code >= 400:
        # Return upstream error text for debugging; in prod you might hide this.
        raise HTTPException(status_code=502, detail=f"Upstream error: {resp.status_code} - {resp.text}")

    return resp.json()
