from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
import httpx
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_client_key

app = FastAPI(title="SinePathshala Backend - FastAPI")

# Allow CORS (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not set. Set GROQ_API_KEY in Render environment variables.")

# Request model
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
        "model": "llama-3.1-8b-instant",  # Updated working Groq model
        "messages": [
            {
                "role": "system",


                
"content": (
    "You are SinePathshala Science AI TUTOR  — an inspiring and practical science guide. "
    "You only answer questions related to Physics, Chemistry, Biology, Mathematics, "
    "Astronomy, Engineering and Technology. "
    "If a user asks something unrelated to science or technology, politely refuse and guide them back to science topics.\n\n"

    "While answering:\n"
    "- Explain clearly with simple language.\n"
    "- Connect every concept to real-world application.\n"
    "- Mention how it is used in modern technology or industry.\n"
    "- Avoid boring textbook tone.\n"
    "- Encourage creativity and innovation mindset.\n"
    "- Suggest beginner-friendly project ideas when possible.\n"
    "- Motivate students to think like scientists and engineers.\n"
    "- Promote problem-solving and skill development.\n\n"

    "Your goal is not just to teach facts, but to build future innovators."
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

        # Handle Groq API errors
        if resp.status_code >= 400:
            print("===== GROQ ERROR =====")
            print("Status:", resp.status_code)
            print("Response:", resp.text)
            print("======================")
            raise HTTPException(status_code=502, detail="Groq upstream error")

        data = resp.json()

        if "choices" not in data:
            print("Invalid Groq response:", data)
            raise HTTPException(status_code=502, detail="Invalid Groq response")

        answer = data["choices"][0]["message"]["content"]

        return {"answer": answer}

    except httpx.RequestError as e:
        print("HTTPX Error:", str(e))
        raise HTTPException(status_code=502, detail="Upstream communication failed")

    except Exception as e:
        print("Server Error:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
