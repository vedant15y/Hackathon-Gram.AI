from pydantic import BaseModel
from typing import Optional, List
import datetime

class UserAuth(BaseModel):
    email: str
    password: str


class SessionRequest(BaseModel):
    token: str

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str

class PatientResponse(PatientCreate):
    id: int
    doctor_id: int
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    patient_id: Optional[int] = None

class PatientReadingCreate(BaseModel):
    metric: str
    value: float
    unit: str
