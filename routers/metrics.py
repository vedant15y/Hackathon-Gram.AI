from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

@router.get("/metrics/readings")
def get_patient_readings(patient_id: int = 1, db: Session = Depends(get_db)):
    """Fetch structured patient readings to power the realtime charts."""
    # Get all readings for the provided patient ID, sorted by timestamp
    readings = db.query(models.PatientReading).filter(
        models.PatientReading.patient_id == patient_id
    ).order_by(models.PatientReading.timestamp.asc()).all()

    # Format into structured JSON the frontend can use easily
    formatted_data = {"heart_rate": [], "systolic_bp": [], "diastolic_bp": [], "glucose": [], "labels": []}
    
    unique_dates = []
    
    for r in readings:
        date_str = r.timestamp.strftime("%Y-%m-%d %H:%M")
        if date_str not in unique_dates:
            unique_dates.append(date_str)
            formatted_data["labels"].append(date_str)
            
        # Group by metric
        metric = r.metric.lower().strip()
        if metric in formatted_data:
            formatted_data[metric].append(r.value)

    return formatted_data

@router.get("/metrics/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    patients_count = db.query(models.Patient).count()
    chats_count = db.query(models.ConsultationChat).count()
    media_count = db.query(models.ConsultationChat).filter(models.ConsultationChat.message.like("%[IMAGE]%")).count()
    
    recent_chats = db.query(models.ConsultationChat).order_by(models.ConsultationChat.timestamp.desc()).limit(3).all()
    recent = []
    for c in recent_chats:
        title = "Clinical Consultation"
        icon = "solar:chat-line-linear"
        if "[IMAGE]" in (c.message or ""):
            title = "Image Analysis"
            icon = "solar:gallery-linear"
            
        recent.append({
            "title": title,
            "patient_id": c.patient_id or "N/A",
            "icon": icon,
            "time_ago": "Just now" # Real time ago logic could be handled via JS
        })
        
    return {
        "patients": patients_count,
        "interactions": chats_count,
        "time_saved": round(chats_count * 1.5, 1),
        "media_uploads": media_count,
        "recent_activity": recent
    }

@router.get("/metrics/patient-summaries")
def get_patient_summaries(db: Session = Depends(get_db)):
    chats = db.query(models.ConsultationChat).order_by(models.ConsultationChat.timestamp.desc()).limit(15).all()
    summaries = []
    for c in chats:
        clean_response = c.response.replace('\n', ' ')
        summaries.append({
            "id": f"PT-{c.patient_id or 1}",
            "name": "General Patient", 
            "initials": "GP",
            "last_visit": c.timestamp.strftime("%b %d, %Y %H:%M"),
            "summary": clean_response[:100] + "..." if len(clean_response) > 100 else clean_response,
            "full_analysis": c.response,
            "status": "Review"
        })
    return summaries
