from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
from database import get_db, init_db
from ollama_client import generate_from_ollama
from routers.auth import router as auth_router
from routers.chat import router as chat_router
from routers.metrics import router as metrics_router
from routers.patients import router as patients_router
from vertex_client import analyze_image, generate_from_vertex


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(metrics_router)
app.include_router(patients_router)


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ai")
def ai(prompt: str, db: Session = Depends(get_db)):
    try:
        response = generate_from_ollama(prompt)
        db.add(
            models.ConsultationChat(
                patient_id=1,
                message=prompt,
                response=response,
            )
        )
        db.commit()
        return {"response": response}
    except Exception as e:
        print("Ollama error:", e)
        try:
            fallback = generate_from_vertex(prompt)
            return {"response": fallback}
        except Exception as vertex_error:
            raise HTTPException(
                status_code=503,
                detail=f"AI services unavailable: {vertex_error}",
            ) from vertex_error


@app.post("/analyze-image")
async def analyze_image_api(
    file: UploadFile = File(...),
    text: str = Form(default=""),
    user_id: int = Form(default=0),
    patient_id: int = Form(default=1),
    db: Session = Depends(get_db),
):
    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"

        try:
            vertex_result = analyze_image(image_bytes, mime_type=mime_type)
        except Exception as vertex_error:
            raise HTTPException(
                status_code=503,
                detail=f"Image analysis unavailable: {vertex_error}",
            ) from vertex_error

        prompt = f"""
You are an advanced medical AI assistant.

Based on the following image analysis:
{vertex_result}

Provide structured output EXACTLY in this format:

1. Observations:
[Detailed clinical findings]

2. Possible Conditions:
[Medical possibilities]

3. Risk Level:
(Low / Moderate / High / Critical)

4. Recommended Action:
[Next steps, no diagnosis]
"""

        try:
            final_response = generate_from_ollama(prompt)
        except Exception as e:
            print("Ollama failed, using Vertex fallback:", e)
            try:
                final_response = generate_from_vertex(prompt)
            except Exception:
                final_response = vertex_result

        if user_id:
            db.add(
                models.ConsultationChat(
                    patient_id=patient_id,
                    message="[IMAGE] " + (text or ""),
                    response=final_response,
                )
            )
            db.commit()

        return {
            "vertex_analysis": vertex_result,
            "final_response": final_response,
        }
    except Exception as e:
        print("Image processing error:", e)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e)) from e
