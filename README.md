# MediNexus 🩺🔐
**AI-Powered Clinical Documentation & Digital Signature Verification Platform**

MediNexus is an end-to-end healthcare management platform designed to eliminate manual Electronic Health Record (EHR) typing, prevent prescription tampering, and accelerate medical insurance claim verification. It combines local ambient speech-to-text transcription and clinical entity extraction with 2048-bit RSA digital signatures and automated WhatsApp PDF delivery.

---

## ✨ Key Features

- **Ambient Voice Transcription:** Captures live doctor–patient consultations and transcribes spoken dialogue locally using **OpenAI Whisper** (`base` model).
- **Clinical Entity Extraction & Decision Support:** Automatically parses transcripts to identify symptoms, medications, possible conditions, and severity levels via custom NLP and clinical rules (`nlp_extraction.py` & `ai_support.py`).
- **Human-in-the-Loop Review Gate:** Gives physicians full editorial control on a responsive dashboard to review and modify AI-extracted notes before approval.
- **Tamper-Proof RSA Digital Signatures:** Seals finalized prescription payloads using asymmetric **2048-bit RSA-PSS (SHA-256)** cryptography via the doctor's private key.
- **QR-Embedded PDF & WhatsApp Dispatch:** Generates formatted prescription PDFs embedded with verification QR codes (via **ReportLab**) and pushes them directly to the patient's WhatsApp via **Twilio**.
- **Instant Claim Verification API:** Exposes a public-key verification endpoint (`/api/verify-prescription`) allowing pharmacies and insurance processors to detect any post-issuance tampering in milliseconds.
- **Consultation History & Records:** Stores doctor accounts, patient profiles, and signed prescriptions in a relational **MySQL** database (`medinexus_db`) with searchable dashboard history.

---

## 🏗️ System Architecture

MediNexus follows a modular 4-tier architecture:

1. **Presentation Layer:** Responsive web dashboard (`HTML5`, `CSS3`, `Bootstrap 5`, `JavaScript`) for doctor login, audio recording, clinical review, and record search.
2. **AI & NLP Processing Layer:** Local `Whisper AI` for speech-to-text paired with Python NLP extraction and clinical decision-support modules.
3. **Core Backend & Crypto Gateway:** `Python Flask` REST API orchestrating authentication, RSA-2048 digital signing, PDF/QR generation, and `Twilio WhatsApp` messaging.
4. **Data & Key Storage Layer:** `MySQL` (`Flask-SQLAlchemy` + `PyMySQL`) storing relational records alongside local `.pem` asymmetric key pairs.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Backend** | Python 3.10+, Flask, Flask-SQLAlchemy, PyMySQL |
| **Database** | MySQL 8.0+ (`medinexus_db`) |
| **AI & NLP** | OpenAI Whisper (`base`), Custom Python NLP & Clinical Rules |
| **Security & PDF** | Python `cryptography` (RSA-2048, SHA-256, PSS), ReportLab, QRCode, Pillow |
| **Messaging** | Twilio Programmable Messaging (WhatsApp Business API) |

---

## 📁 Project Structure

```text
Medinexus/
├── app.py                      # Core Flask backend & REST API gateway
├── config.py                   # One-time RSA-2048 key pair generator (generate_keys)
├── nlp_extraction.py           # Medical NLP keyword extraction module
├── ai_support.py               # Clinical decision support & severity rules
├── speech_to_text.py           # Standalone Whisper audio transcription helper
├── schema.sql                  # MySQL database & table initialization script
├── requirements.txt            # Python package dependencies
├── .env                        # Environment variables (excluded from Git)
├── keys/                       # RSA private/public .pem keys (excluded from Git)
├── static/
│   ├── js/
│   │   └── app.js              # Frontend dashboard logic & audio recorder
│   └── pdfs/                   # Generated signed prescription PDFs
└── templates/
    └── index.html              # Doctor dashboard UI
```

---

## ⚙️ Prerequisites & Local Setup

### Prerequisites
- **Python 3.10+**
- **MySQL 8.0+**
- **FFmpeg** (required for audio decoding with Whisper)
- **Twilio Account** *(optional — required only for WhatsApp prescription dispatch)*

### 1. Clone the Repository & Create a Virtual Environment
```bash
git clone https://github.com/shruti814/medinexus.git
cd medinexus
python -m venv venv
```

Activate the virtual environment:
- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source venv/bin/activate`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install faster-whisper
```
> **Note:** `app.py` uses `faster-whisper` (`device="cpu"`, `compute_type="int8"`) for local audio transcription.

### 3. Initialize the MySQL Database
Run `schema.sql` to create the `medinexus_db` database and its tables (`users`, `patients`, `prescriptions`):
```bash
mysql -u root -p < schema.sql
```

### 4. Configure Environment Variables
Create a `.env` file in the project root with the following variables:

| Variable | Required | Default / Description |
| :--- | :---: | :--- |
| `FLASK_SECRET_KEY` | Yes | Secret key used to sign Flask sessions |
| `MYSQL_USER` | Yes | MySQL username (default: `root`) |
| `MYSQL_PASSWORD` | Yes | MySQL password |
| `MYSQL_HOST` | Yes | MySQL host (default: `localhost`) |
| `MYSQL_DB` | Yes | Database name (default: `medinexus_db`) |
| `WHISPER_MODEL` | No | Whisper model size (default: `base`) |
| `TWILIO_ACCOUNT_SID` | No | Twilio Account SID for WhatsApp notifications |
| `TWILIO_AUTH_TOKEN` | No | Twilio Auth Token for WhatsApp notifications |
| `TWILIO_WHATSAPP_NUMBER` | No | Twilio WhatsApp sender (default: `whatsapp:+14155238886`) |
| `PUBLIC_BASE_URL` | No | Public base URL used to attach PDF media links in WhatsApp messages |

### 5. Generate RSA-2048 Cryptographic Keys
Run `config.py` once to generate `keys/doctor_private_key.pem` and `keys/doctor_public_key.pem`:
```bash
python config.py
```

### 6. Start the Application
```bash
python app.py
```
The server starts locally at `http://127.0.0.1:5000`.

---

## 🔌 REST API Endpoints

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/` | No | Renders the doctor dashboard (`templates/index.html`) |
| `POST` | `/api/register` | No | Registers a doctor account (`fullName`, `email`, `password` of 8+ chars) |
| `POST` | `/api/login` | No | Authenticates a doctor and starts a session (`email`, `password`) |
| `POST` | `/api/logout` | No | Clears the active doctor session |
| `GET` | `/api/me` | No | Checks whether the current session is authenticated |
| `POST` | `/api/process-audio-consultation` | Yes | Accepts `multipart/form-data` (`audio`), transcribes via Whisper, and returns extracted symptoms, medications, possible conditions, severity, and urgent warnings |
| `POST` | `/api/finalize-prescription` | Yes | Signs clinical data with RSA-PSS, generates a QR-embedded PDF in `static/pdfs/`, saves the record to MySQL, and dispatches a WhatsApp alert if Twilio is configured |
| `POST` | `/api/verify-prescription` | Yes | Verifies a prescription's digital signature by `prescriptionId` and returns `VALID` or `TAMPERED` |
| `GET` | `/api/my-records` | Yes | Lists all prescriptions and patient details issued by the logged-in doctor |

---

## 🔐 Digital Signature & Tamper Detection Flow

1. **Canonical Serialization:** When finalizing a prescription, `app.py` builds a deterministic UTF-8 JSON payload containing `rxId`, `doctorId`, `patientId`, and `data` (`sort_keys=True`, compact separators).
2. **Signing:** The canonical payload is signed with the doctor's 2048-bit RSA private key (`keys/doctor_private_key.pem`) using **RSA-PSS with MGF1(SHA-256)** and stored Base64-encoded alongside the prescription record.
3. **PDF & QR Embedding:** ReportLab generates `static/pdfs/prescription_<RX_ID>.pdf` containing the clinical summary, signature preview, and a verification QR code.
4. **Verification:** Calling `/api/verify-prescription` reconstructs the canonical payload from the stored record and validates the signature against `keys/doctor_public_key.pem`. Any alteration to the stored clinical data causes verification to return `TAMPERED`.

---

## 🗄️ Database Schema Overview

Defined in `schema.sql` for database `medinexus_db`:

- **`users`** — Stores registered doctor accounts (`user_id`, `full_name`, `email`, `password_hash`, `role`, `created_at`).
- **`patients`** — Stores patient profiles (`patient_id`, `full_name`, `whatsapp_number`, `medical_history`, `created_at`).
- **`prescriptions`** — Stores signed prescriptions (`prescription_id`, `doctor_id` FK → `users`, `patient_id` FK → `patients`, `clinical_data` JSON, `digital_signature`, `pdf_path`, `created_at`).

---

## ⚠️ Clinical Disclaimer

MediNexus is an academic and clinical-support prototype only. AI-extracted symptoms, possible conditions, and severity indicators do **not** constitute a medical diagnosis or prescription; all clinical decisions require licensed physician review.
