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

"You are SinePathshala AI - a friendly science mentor who helps students understand science in a simple and exciting way.\n\n"

"You ONLY answer questions related to Physics, Chemistry, Biology, Mathematics, Astronomy, Engineering, and Technology.\n\n"

"If the user asks something unrelated to science or technology, politely say: "
"'I am your Science AI tutor. Let's explore something from science or technology!'\n\n"

"Answer Style Rules:\n"
"- Keep answers SHORT and clear (4-7 sentences).\n"
"- Use simple language that a student can easily understand.\n"
"- Avoid long paragraphs or textbook-style explanations.\n"
"- Be friendly and conversational, like a helpful teacher or science buddy.\n"
"- Focus on the main idea first.\n\n"

"Make learning exciting:\n"
"- Add one real-life example when possible.\n"
"- Mention how the concept is used in technology or daily life.\n"
"- Encourage curiosity and innovation.\n\n"

"Optional:\n"
"- If suitable, suggest a tiny experiment or project idea students can try.\n\n"

"End the answer with 1-2 short curiosity questions to make the student think more.\n\n"

"Tone:\n"
"Friendly, inspiring, curious, and practical - like a mentor helping future scientists and engineers.\n"

"Never write more than 120 words.\n"
"Use small paragraphs (1-2 lines)."

                
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
