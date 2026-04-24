import base64
import json
import os
import re
import tempfile

import requests
from fastapi import APIRouter, Body, Depends, File, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

import models
from database import get_db
from language_utils import process_input
from ollama_client import MedGemmaChat
from speech_utils import transcribe_audio
from text_utils import text_to_speech


router = APIRouter()
bot = MedGemmaChat()


def intercept_and_save_metrics(response: str, patient_id: int, db: Session):
    match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
    if match:
        metrics_json = match.group(1)
        try:
            metrics_data = json.loads(metrics_json)
            for metric_key, val in metrics_data.items():
                if val in (None, ""):
                    continue
                reading = models.PatientReading(
                    patient_id=patient_id if patient_id else 1,
                    metric=metric_key,
                    value=float(val),
                    unit="",
                )
                db.add(reading)
            db.commit()
        except Exception as e:
            print("Failed to save intercepted JSON metrics:", e)

        response = re.sub(r"```json\s*\{.*?\}\s*```", "", response, flags=re.DOTALL | re.IGNORECASE).strip()
    return response


@router.post("/chat")
def chat(data: dict, db: Session = Depends(get_db)):
    message = data.get("message")
    user_id = data.get("user_id")
    patient_id = data.get("patient_id") or 1

    past_chats = (
        db.query(models.ConsultationChat)
        .filter(models.ConsultationChat.patient_id == patient_id)
        .order_by(models.ConsultationChat.timestamp.desc())
        .limit(3)
        .all()
    )
    if past_chats:
        history_context = "Patient's Past Summaries: " + " | ".join(
            [c.response.replace("\n", " ")[:100] + "..." for c in past_chats]
        )
        augmented_message = f"[{history_context}]\n\nUser Message: {message}"
    else:
        augmented_message = message

    try:
        result = bot.send_text(augmented_message)
        response = result.get("response", "")
        response = intercept_and_save_metrics(response, patient_id, db)
    except Exception as e:
        response = f"LLM not available {str(e)}"

    if user_id:
        new_chat = models.ConsultationChat(
            patient_id=patient_id if patient_id else None,
            message=message,
            response=response,
        )
        db.add(new_chat)
        db.commit()

    return {"response": response}


@router.post("/chat-image")
async def chat_image(
    file: UploadFile = File(...),
    text: str = "",
    user_id: int = 0,
    patient_id: int = 0,
    db: Session = Depends(get_db),
):
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            path = tmp.name

        if text:
            bot.messages.append({"role": "user", "content": text})

        response = bot.send_image(path, text or "Analyze this medical image")
        response = intercept_and_save_metrics(response, patient_id, db)

        if user_id:
            new_chat = models.ConsultationChat(
                patient_id=patient_id if patient_id else None,
                message="[IMAGE] " + (text or ""),
                response=response,
            )
            db.add(new_chat)
            db.commit()

        return {"response": response}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


def stream_generator(message):
    bot.messages.append({"role": "user", "content": message})
    response = requests.post(
        bot.url,
        json={"model": bot.model, "messages": bot.messages, "stream": True},
        stream=True,
        timeout=300,
    )
    for line in response.iter_lines():
        if line:
            try:
                chunk = json.loads(line.decode())
                yield chunk.get("message", {}).get("content", "")
            except Exception:
                pass


@router.post("/chat-stream")
def chat_stream(data: dict):
    return StreamingResponse(stream_generator(data.get("message")), media_type="text/plain")


@router.post("/stt")
async def stt(file: UploadFile = File(...)):
    path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        path = tmp.name
    try:
        stt_result = transcribe_audio(path)
        processed = process_input(stt_result["text"])
        return {
            "original": stt_result["text"],
            "transliterated": processed["transliterated"],
            "english": processed["english"],
        }
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


@router.post("/stt-text")
def stt_text(data: dict):
    text = data.get("text")
    processed = process_input(text)
    return {
        "original": text,
        "transliterated": processed["transliterated"],
        "english": processed["english"],
    }


@router.post("/tts")
async def tts(request: Request, text: str | None = Body(default=None)):
    if text is None:
        raw_text = await request.body()
        text = raw_text.decode("utf-8").strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
    if not text:
        return Response(content=b"", media_type="audio/mpeg")
    path = text_to_speech(text, "out.mp3")
    with open(path, "rb") as f:
        audio = f.read()
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...), db: Session = Depends(get_db)):
    path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        path = tmp.name
    try:
        stt_result = transcribe_audio(path)
        text = stt_result["text"]
        try:
            result = bot.send_text(text)
            response = result["response"]
            response = intercept_and_save_metrics(response, 1, db)
        except Exception:
            response = "LLM not available"

        tts_path = text_to_speech(response, "voice.mp3")
        with open(tts_path, "rb") as f:
            audio = base64.b64encode(f.read()).decode()

        return {
            "input": text,
            "response": response,
            "audio": audio,
        }
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


@router.post("/history")
def history(data: dict, db: Session = Depends(get_db)):
    patient_id = data.get("patient_id")

    query = db.query(models.ConsultationChat)
    if patient_id:
        query = query.filter(models.ConsultationChat.patient_id == patient_id)

    rows = query.order_by(models.ConsultationChat.timestamp.asc()).all()

    history = []
    for row in rows:
        history.append({"role": "user", "message": row.message})
        history.append({"role": "ai", "message": row.response})

    return {"history": history}
