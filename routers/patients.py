from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter()

@router.post("/patients", response_model=schemas.PatientResponse)
def create_patient(data: schemas.PatientCreate, doctor_id: int, db: Session = Depends(get_db)):
    new_patient = models.Patient(**data.model_dump(), doctor_id=doctor_id)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@router.get("/patients/{doctor_id}")
def get_patients(doctor_id: int, db: Session = Depends(get_db)):
    patients = db.query(models.Patient).filter(models.Patient.doctor_id == doctor_id).all()
    return patients
