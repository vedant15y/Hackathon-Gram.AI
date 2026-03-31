from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sqlite3
import json

from ollama_client import MedGemmaChat

app = FastAPI()

# CORS (important for HTML frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = MedGemmaChat()

# =========================
# REQUEST MODEL
# =========================
class ChatRequest(BaseModel):
    message: str
    user_id: int | None = None


# =========================
# 🔥 STREAMING GENERATOR
# =========================
def stream_generator(message):
    bot.messages.append({
        "role": "user",
        "content": message
    })

    response = bot.url

    import requests

    r = requests.post(
        response,
        json={
            "model": bot.model,
            "messages": bot.messages,
            "stream": True
        },
        stream=True
    )

    full_reply = ""

    for line in r.iter_lines():
        if line:
            try:
                chunk = json.loads(line.decode("utf-8"))
                content = chunk.get("message", {}).get("content", "")
                full_reply += content
                yield content   # 🔥 STREAM TO FRONTEND
            except:
                pass

    bot.messages.append({
        "role": "assistant",
        "content": full_reply
    })


# =========================
# 🔥 STREAM ENDPOINT
# =========================
@app.post("/chat-stream")
def chat_stream(data: ChatRequest):
    return StreamingResponse(
        stream_generator(data.message),
        media_type="text/plain"
    )


# =========================
# NORMAL CHAT (fallback)
# =========================
@app.post("/chat")
def chat(data: ChatRequest):
    result = bot.send_text(data.message)
    return {"response": result["response"]}
from fastapi import Body
import sqlite3

# =========================
# SIGNUP
# =========================
@app.post("/signup")
def signup(data: dict = Body(...)):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"status": "fail", "error": "Missing fields"}

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )
        conn.commit()

        user_id = c.lastrowid

        return {
            "status": "success",
            "user_id": user_id
        }

    except sqlite3.IntegrityError:
        return {"status": "fail", "error": "User already exists"}

    finally:
        conn.close()


# =========================
# LOGIN
# =========================
@app.post("/login")
def login(data: dict = Body(...)):
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT id FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = c.fetchone()
    conn.close()

    if user:
        return {
            "status": "success",
            "user_id": user[0]
        }

    return {"status": "fail", "error": "Invalid credentials"}