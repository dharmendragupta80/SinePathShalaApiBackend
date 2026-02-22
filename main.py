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

# ✅ Environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not set. Set GROQ_API_KEY before deploying.")

# ✅ AskRequest must be OUTSIDE the if block
class AskRequest(BaseModel):
    question: str


@app.post("/ask", dependencies=[Depends(verify_client_key)])
async def ask(req: AskRequest):

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: GROQ_API_KEY not set."
        )

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are SinePathshala Science AI Tutor. "
                    "Only answer questions related to Physics, Chemistry, Biology, "
                    "Mathematics, Astronomy, Engineering and Technology. "
                    "If user asks non-science question, politely refuse."
                )
            },
            {
                "role": "user",
                "content": req.question
            }
        ],
        "temperature": 0.3
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream communication failed: {e}")

    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Upstream error: {resp.status_code} - {resp.text}")

    data = resp.json()

    answer = data["choices"][0]["message"]["content"]

    return {"answer": answer}
