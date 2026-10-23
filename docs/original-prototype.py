
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="CICC Forensic AI Analyzer")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "cicc-agent:latest"

SYSTEM_PROMPT = """
You are a digital forensic analysis assistant.

Your role is to assist authorized investigators.
Distinguish facts from investigative hypotheses.
Do not invent evidence, timestamps, or identifiers.
Do not claim to have examined evidence that was
not supplied to you.
"""

class ChatRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {
        "application": "CICC Forensic AI Analyzer",
        "status": "Running",
        "model": MODEL
    }

@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": request.question}
                ]
            },
            timeout=180
        )
        response.raise_for_status()
        return {
            "answer": response.json()["message"]["content"]
        }
    except (requests.RequestException, KeyError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama communication failed: {exc}"
        )
