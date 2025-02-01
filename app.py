import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
import requests
import json
import base64
import os
import re

API_URL = "http://localhost:8000"
PHONE_PATTERN = re.compile(r'^\+91\s\d{10}$')
REFERENCE_ID_PATTERN = re.compile(r'^APT-\d{4}$')

SYSTEM_PROMPT = """You are a healthcare appointment assistant. Follow these strict rules:
- Verify patient name contains only letters/spaces.
- Validate phone number format: +91 followed by 10 digits.
- Reference IDs should match APT-XXXX format.
- Don't assume appointment details, always confirm first.
- Use only the provided tools: book_appointment and check_appointment.
"""

def validate_patient_name(name: str) -> bool:
    return bool(name) and all(c.isalpha() or c.isspace() for c in name)

def validate_phone_number(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone))

def validate_reference_id(ref_id: str) -> bool:
    return bool(REFERENCE_ID_PATTERN.match(ref_id))

@tool(parse_docstring=True)
def book_appointment(patient_name: str, contact_number: str):
    """Books an appointment through the external API."""
    if not validate_patient_name(patient_name):
        return {"status": "error", "message": "Invalid patient name."}
    
    if not validate_phone_number(contact_number):
        return {"status": "error", "message": "Invalid phone number format."}

    response = requests.post(f"{API_URL}/appointments/", json={
        "patient_name": patient_name,
        "contact_number": contact_number
    })
    
    if response.status_code == 200:
        return response.json()
    return {"status": "error", "message": response.json().get('detail', 'Error occurred')}

@tool(parse_docstring=True)
def check_appointment(reference_id: str):
    """Checks the status of an appointment using the reference ID."""
    if not validate_reference_id(reference_id):
        return {"status": "error", "message": "Invalid reference ID format."}

    response = requests.get(f"{API_URL}/appointments/{reference_id}")
    if response.status_code == 200:
        return response.json()
    return {"status": "error", "message": "Appointment not found."}

def main():
    st.title("🏥 Healthcare Appointment System")

    if 'messages' not in st.session_state:
        st.session_state.messages = [SystemMessage(content=SYSTEM_PROMPT)]

    user_input = st.chat_input("How can I assist you?")
    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        llm = ChatOllama(model="mistral-nemo:latest", temperature=0.1)
        llm_with_tools = llm.bind_tools([book_appointment, check_appointment])

        response = llm_with_tools.invoke(st.session_state.messages)
        st.session_state.messages.append(response)
        st.write(response.content)

if __name__ == "__main__":
    main()
