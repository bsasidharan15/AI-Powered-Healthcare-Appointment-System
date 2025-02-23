# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

app = FastAPI()

# Create a directory for PDFs if it doesn't exist
if not os.path.exists('appointment_pdfs'):
    os.makedirs('appointment_pdfs')

# In-memory storage (replace with database in production)
appointments = []

class Appointment(BaseModel):
    patient_name: str
    contact_number: str
    appointment_date: Optional[str] = None
    reference_id: Optional[str] = None
    status: Optional[str] = "scheduled"

class AppointmentResponse(BaseModel):
    reference_id: str
    status: str
    message: str
    pdf_path: Optional[str]

def generate_appointment_pdf(appointment_data: dict) -> str:
    """Generate PDF for appointment confirmation"""
    pdf_filename = f"appointment_pdfs/appointment_{appointment_data['reference_id']}.pdf"
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add content
    elements.append(Paragraph("Appointment Confirmation", title_style))
    elements.append(Spacer(1, 12))
    
    # Create table data
    data = [
        ["Reference ID:", appointment_data['reference_id']],
        ["Patient Name:", appointment_data['patient_name']],
        ["Contact Number:", appointment_data['contact_number']],
        ["Appointment Date:", appointment_data['appointment_date']],
        ["Status:", appointment_data['status']]
    ]
    
    # Create table
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Add footer
    footer_text = "Thank you for choosing our healthcare services. Please arrive 15 minutes before your scheduled appointment."
    elements.append(Paragraph(footer_text, styles["Normal"]))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_filename

@app.post("/appointments/", response_model=AppointmentResponse)
async def create_appointment(appointment: Appointment):
    # Validate phone number
    if not appointment.contact_number.startswith('+91'):
        raise HTTPException(status_code=400, detail="Invalid phone number format. Must start with +91")
    
    # Generate reference ID
    reference_id = f"APT-{len(appointments)+1:04d}"
    
    # Add reference ID and date to appointment
    appointment_dict = appointment.dict()
    appointment_dict["reference_id"] = reference_id
    appointment_dict["appointment_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save appointment
    appointments.append(appointment_dict)
    
    # Generate PDF
    pdf_path = generate_appointment_pdf(appointment_dict)
    
    return AppointmentResponse(
        reference_id=reference_id,
        status="confirmed",
        message="Appointment scheduled successfully",
        pdf_path=pdf_path
    )

@app.get("/appointments/{reference_id}")
async def get_appointment(reference_id: str):
    for apt in appointments:
        if apt["reference_id"] == reference_id:
            return apt
    raise HTTPException(status_code=404, detail="Appointment not found")

@app.get("/appointments/")
async def list_appointments():
    return appointments

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
