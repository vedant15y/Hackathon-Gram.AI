from flask import Flask, request, jsonify
from flask_cors import CORS
from ollama_client import MedGemmaChat
from speech_utils import transcribe_audio
from text_utils import text_to_speech
import tempfile, os
import sqlite3

app = Flask(__name__)
CORS(app)

bot = MedGemmaChat()

# ==============================
# DATABASE SETUP
# ==============================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        response TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ==============================
# AUTH ROUTES
# ==============================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "fail", "error": "Missing fields"})

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )
        conn.commit()

        user_id = c.lastrowid

        return jsonify({
            "status": "success",
            "user_id": user_id
        })

    except sqlite3.IntegrityError:
        return jsonify({"status": "fail", "error": "User already exists"})
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
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
        return jsonify({
            "status": "success",
            "user_id": user[0]
        })
    else:
        return jsonify({"status": "fail", "error": "Invalid credentials"})


# ==============================
# CHAT ROUTE (FIXED)
# ==============================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message")
    user_id = data.get("user_id")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    result = bot.send_text(message)

    response = (
        result.get("response")
        or result.get("english_response")
        or str(result)
    )

    # Save chat to DB
    if user_id:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO chats (user_id, message, response) VALUES (?, ?, ?)",
            (user_id, message, response)
        )
        conn.commit()
        conn.close()

    return jsonify({"response": response})


# ==============================
# HISTORY ROUTE (FIXED)
# ==============================
@app.route("/history", methods=["POST"])
def history():
    data = request.json or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"history": []})

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT message, response FROM chats WHERE user_id=?",
        (user_id,)
    )

    chats = c.fetchall()
    conn.close()

    history = []
    for m, r in chats:
        history.append({"role": "user", "message": m})
        history.append({"role": "ai", "message": r})

    return jsonify({"history": history})


# ==============================
# IMAGE ROUTE
# ==============================
@app.route("/image", methods=["POST"])
def image():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "No file"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        file.save(tmp.name)
        path = tmp.name

    reply = bot.send_image(path)
    os.unlink(path)

    return jsonify({"response": reply})


# ==============================
# VOICE ROUTE
# ==============================
@app.route("/voice", methods=["POST"])
def voice():
    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "No audio"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        file.save(tmp.name)
        path = tmp.name

    text = transcribe_audio(path)["text"]
    result = bot.send_text(text)

    os.unlink(path)
    return jsonify(result)


# ==============================
# TEXT TO SPEECH
# ==============================
@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text")
    path = text_to_speech(text, output_file="tts_output.mp3")
    return app.send_static_file(path)


# ==============================
# RESET CHAT
# ==============================
@app.route("/reset", methods=["POST"])
def reset():
    bot.reset()
    return jsonify({"status": "ok"})


# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(port=5000)