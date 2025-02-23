import streamlit as st
import sys
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
import requests
import json
from datetime import datetime
import base64
import os
import re

# API configuration
API_URL = "http://localhost:8000"

# Regex patterns for validation
PHONE_PATTERN = re.compile(r'^\+91\s\d{10}$')
REFERENCE_ID_PATTERN = re.compile(r'^APT-\d{4}$')

# System prompt to reduce hallucinations
SYSTEM_PROMPT = """You are a healthcare appointment assistant. Follow these strict guidelines:

1. VERIFICATION REQUIREMENTS:
- Always verify patient name contains only letters and spaces
- Phone numbers must match Indian format (+91 followed by 10 digits)
- Reference IDs must match format APT-XXXX where X is a digit
- Never make assumptions about appointment dates or times
- Never invent or assume appointment details that weren't provided

2. INFORMATION HANDLING:
- If any required information is missing, explicitly ask for it
- If information is ambiguous, ask for clarification
- Never generate fake appointment details or reference numbers
- Only use the provided tools: book_appointment and check_appointment

3. RESPONSE GUIDELINES:
- Stick to facts present in user input or tool responses
- Say "I don't have that information" when details are unavailable
- Don't make assumptions about medical conditions or treatments
- Don't provide medical advice

4. ERROR HANDLING:
- If API calls fail, clearly communicate the error
- Don't try to recover from errors by making assumptions
- Ask user to retry with correct information

Before taking any action:
1. Validate all input data against required formats
2. Confirm understanding of user request
3. Use tools only when all required information is verified
4. Report back exactly what the tools return without embellishment

Remember: It's better to ask for clarification than to make assumptions."""

def validate_patient_name(name: str) -> bool:
    """Validate patient name contains only letters and spaces"""
    return bool(name) and all(c.isalpha() or c.isspace() for c in name)

def validate_phone_number(phone: str) -> bool:
    """Validate phone number matches Indian format"""
    return bool(PHONE_PATTERN.match(phone))

def validate_reference_id(ref_id: str) -> bool:
    """Validate appointment reference ID format"""
    return bool(REFERENCE_ID_PATTERN.match(ref_id))

def get_pdf_download_link(pdf_path: str, filename: str):
    """Generate a download link for the PDF"""
    with open(pdf_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download Appointment PDF</a>'
    return href

@tool(parse_docstring=True)
def book_appointment(patient_name: str, contact_number: str):
    """
    Books an appointment through the external API.
    Call this whenever a user wants to schedule an appointment or consultation.
    
    Args:
        patient_name: Full name of the patient (letters and spaces only)
        contact_number: Phone number in Indian format (+91 1234567890)
    """
    # Validate inputs before making API call
    if not validate_patient_name(patient_name):
        return {
            "status": "error",
            "message": "Invalid patient name. Please use only letters and spaces."
        }
    
    if not validate_phone_number(contact_number):
        return {
            "status": "error",
            "message": "Invalid phone number. Please use Indian format: +91 1234567890"
        }

    try:
        # Make API call to the FastAPI backend
        response = requests.post(
            f"{API_URL}/appointments/",
            json={
                "patient_name": patient_name,
                "contact_number": contact_number
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Appointment booked successfully!")
            st.info(f"""
            📋 Booking Details:
            - Reference: {data['reference_id']}
            - Status: {data['status']}
            - Message: {data['message']}
            """)
            
            if 'pdf_path' in data and os.path.exists(data['pdf_path']):
                pdf_filename = f"appointment_{data['reference_id']}.pdf"
                st.markdown(
                    get_pdf_download_link(data['pdf_path'], pdf_filename),
                    unsafe_allow_html=True
                )
            
            return data
        else:
            error_msg = response.json().get('detail', 'Unknown error occurred')
            st.error(f"Failed to book appointment: {error_msg}")
            return {"status": "error", "message": error_msg}
            
    except Exception as e:
        error_msg = f"Error booking appointment: {str(e)}"
        st.error(error_msg)
        return {"status": "error", "message": error_msg}

@tool(parse_docstring=True)
def check_appointment(reference_id: str):
    """
    Checks the status of an appointment using the reference ID.
    Call this when a user asks about their appointment status.

    Args:
        reference_id: The appointment reference ID (format: APT-XXXX)
    """
    if not validate_reference_id(reference_id):
        return {
            "status": "error",
            "message": "Invalid reference ID format. Please use format APT-XXXX"
        }

    try:
        response = requests.get(f"{API_URL}/appointments/{reference_id}")
        if response.status_code == 200:
            data = response.json()
            st.info(f"""
            📋 Appointment Details:
            - Reference: {data['reference_id']}
            - Patient: {data['patient_name']}
            - Contact: {data['contact_number']}
            - Date: {data['appointment_date']}
            - Status: {data['status']}
            """)
            
            pdf_path = f"appointment_pdfs/appointment_{data['reference_id']}.pdf"
            if os.path.exists(pdf_path):
                pdf_filename = f"appointment_{data['reference_id']}.pdf"
                st.markdown(
                    get_pdf_download_link(pdf_path, pdf_filename),
                    unsafe_allow_html=True
                )
            
            return data
        else:
            error_msg = "Appointment not found or invalid reference ID"
            st.error(error_msg)
            return {"status": "error", "message": error_msg}
            
    except Exception as e:
        error_msg = f"Error checking appointment: {str(e)}"
        st.error(error_msg)
        return {"status": "error", "message": error_msg}

def main():
    st.title("🏥 Healthcare Appointment System")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

    # Add a sidebar to check API connection
    with st.sidebar:
        st.header("System Status")
        try:
            response = requests.get(f"{API_URL}/appointments/")
            if response.status_code == 200:
                st.success("✅ Connected to API")
            else:
                st.error("❌ API Error")
        except:
            st.error("❌ Cannot connect to API")
            st.warning("Please ensure the API server is running on " + API_URL)

    # Chat interface
    for message in st.session_state.messages[1:]:  # Skip system prompt in display
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        else:
            with st.chat_message("assistant"):
                st.write(message.content)

    # User input
    user_input = st.chat_input("How can I help you today?")

    if user_input:
        with st.chat_message("user"):
            st.write(user_input)

        # Initialize LLM with tools
        llm = ChatOllama(
            model="mistral-nemo:latest",
            temperature=0.1  # Lower temperature for more focused responses
        )
        llm_with_tools = llm.bind_tools([book_appointment, check_appointment])
        
        st.session_state.messages.append(HumanMessage(content=user_input))
        
        with st.chat_message("assistant"):
            response = llm_with_tools.invoke(st.session_state.messages)
            
            if not response.tool_calls:
                st.write(response.content)
                st.session_state.messages.append(response)
            else:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"].lower()
                    if tool_name in ["book_appointment", "check_appointment"]:
                        if tool_name == "book_appointment":
                            tool_response = book_appointment.invoke(tool_call["args"])
                        else:
                            tool_response = check_appointment.invoke(tool_call["args"])
                        
                        st.session_state.messages.append(
                            ToolMessage(content=str(tool_response), 
                                      tool_call_id=tool_call["id"])
                        )
                
                final_response = llm_with_tools.invoke(st.session_state.messages)
                st.write(final_response.content)
                st.session_state.messages.append(final_response)

if __name__ == "__main__":
    main()
