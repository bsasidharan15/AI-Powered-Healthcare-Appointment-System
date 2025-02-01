from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os

app = FastAPI()

if not os.path.exists('appointment_pdfs'):
    os.makedirs('appointment_pdfs')

appointments = []

class Appointment(BaseModel):
    patient_name: str
    contact_number: str

class AppointmentResponse(BaseModel):
    reference_id: str
    status: str
    message: str
    pdf_path: str

def generate_pdf(appointment):
    filename = f"appointment_pdfs/{appointment['reference_id']}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = [Paragraph(f"Appointment Confirmation for {appointment['patient_name']}", getSampleStyleSheet()["Title"])]
    doc.build(elements)
    return filename

@app.post("/appointments/", response_model=AppointmentResponse)
async def create_appointment(appointment: Appointment):
    if not appointment.contact_number.startswith("+91"):
        raise HTTPException(status_code=400, detail="Phone number must start with +91")

    reference_id = f"APT-{len(appointments)+1:04d}"
    appointment_data = {"reference_id": reference_id, **appointment.dict()}
    appointments.append(appointment_data)

    pdf_path = generate_pdf(appointment_data)
    
    return AppointmentResponse(reference_id=reference_id, status="confirmed", message="Appointment booked", pdf_path=pdf_path)

@app.get("/appointments/{reference_id}")
async def get_appointment(reference_id: str):
    for apt in appointments:
        if apt["reference_id"] == reference_id:
            return apt
    raise HTTPException(status_code=404, detail="Appointment not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
