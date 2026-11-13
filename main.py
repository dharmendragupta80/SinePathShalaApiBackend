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


# ==========================================
# ✅ NEW: AUTO-MODEL SELECTOR LOGIC
# ==========================================
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]

cached_working_model = None

async def get_active_groq_model():
    global cached_working_model
    if cached_working_model:
        return cached_working_model

    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                active_ids = [m["id"] for m in data.get("data", [])]
                
                # Pick the best model from our list that is currently active
                for model in PREFERRED_MODELS:
                    if model in active_ids:
                        cached_working_model = model
                        print(f"Auto-selected working model: {cached_working_model}")
                        return cached_working_model
                
                # Fallback: just grab the first available model
                if active_ids:
                    cached_working_model = active_ids[0]
                    return cached_working_model
    except Exception as e:
        print("Failed to fetch live models from Groq:", str(e))
    
    # Ultimate fallback if the models endpoint fails
    return "mixtral-8x7b-32768"
# ==========================================


@app.post("/ask", dependencies=[Depends(verify_client_key)])
async def ask(req: AskRequest):
    global cached_working_model

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: GROQ_API_KEY not set."
        )

    # Automatically fetch the verified working model
    active_model = await get_active_groq_model()

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": active_model,  # ✅ USING THE AUTO-SELECTED MODEL
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
            
            # ✅ NEW: If the cached model died, clear the cache so it fetches a new one next time
            if "model_not_found" in resp.text or "model_decommissioned" in resp.text:
                print(f"Model {active_model} failed. Clearing cache...")
                cached_working_model = None 
                raise HTTPException(status_code=502, detail="Groq model rotated. Please try again in 1 second.")
                
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
