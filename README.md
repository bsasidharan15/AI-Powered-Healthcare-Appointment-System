# 🏥 AI-Powered Healthcare Appointment System 📅

## 🚀 Overview
This project provides an **AI-driven Healthcare Appointment System** using **FastAPI** for backend appointment management and **Streamlit with LangChain** for an interactive chatbot experience.

### ✨ Key Features:
- 🤖 **AI-powered chatbot** for booking/checking appointments
- 📅 **Automated appointment scheduling** via API
- 📄 **Generate & Download Appointment PDFs**
- 🔢 **Unique Reference IDs (APT-XXXX) for tracking**
- 📞 **Validates Indian phone numbers (+91 format)**
- 🌐 **FastAPI backend with RESTful API**
- 🎨 **Streamlit UI for a seamless experience**

## 📦 Installation

Clone the repository and install dependencies:
```sh
git clone https://github.com/your-repo/ai-appointment-scheduler.git
cd ai-appointment-scheduler
pip install -r requirements.txt
```

## ▶️ Running the Project

### 1️⃣ **Start the FastAPI Backend**
```sh
uvicorn api:app --reload
```
The API will be available at: `http://127.0.0.1:8000`

### 2️⃣ **Start the Streamlit Chatbot**
```sh
streamlit run app.py
```
This will launch the chatbot interface in your web browser.

## 🔗 API Endpoints

### 📌 **Book an Appointment**
- **POST** `/appointments/`
- **Request:**
  ```json
  {
    "patient_name": "John Doe",
    "contact_number": "+91 1234567890"
  }
  ```
- **Response:**
  ```json
  {
    "reference_id": "APT-0001",
    "status": "confirmed",
    "message": "Appointment scheduled successfully",
    "pdf_path": "appointment_pdfs/appointment_APT-0001.pdf"
  }
  ```

### 🔍 **Check Appointment Status**
- **GET** `/appointments/{reference_id}`

### 📜 **List All Appointments**
- **GET** `/appointments/`

## 🛠 Requirements
Create a `requirements.txt` file with the following dependencies:
```txt
fastapi
uvicorn
pydantic
streamlit
requests
langchain
langchain_ollama
reportlab
```

## 🏁 License
This project is licensed under the **Apache 2.0 License**. 🚀
