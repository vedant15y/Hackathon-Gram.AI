from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    
    patients = relationship("Patient", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    
    doctor = relationship("User", back_populates="patients")
    chats = relationship("ConsultationChat", back_populates="patient")
    readings = relationship("PatientReading", back_populates="patient")

class ConsultationChat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    message = Column(String)
    response = Column(String)
    analysis_json = Column(String, nullable=True) # Storing structured LLM analysis
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    
    patient = relationship("Patient", back_populates="chats")

class PatientReading(Base):
    __tablename__ = "patient_readings"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    metric = Column(String, index=True) # e.g. 'glucose', 'Heart Rate'
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    
    patient = relationship("Patient", back_populates="readings")
