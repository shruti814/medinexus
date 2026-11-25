# MediNexus 🩺🔐
**AI-Powered Clinical Documentation & Digital Signature Verification Platform**

MediNexus is an end-to-end healthcare management platform designed to eliminate manual Electronic Health Record (EHR) typing, prevent prescription tampering, and accelerate medical insurance claim verification. It combines local ambient speech-to-text transcription and clinical entity extraction with 2048-bit RSA digital signatures and automated WhatsApp PDF delivery[cite: 1, 3, 4].

---

## ✨ Key Features

- **Ambient Voice Transcription:** Captures live doctor–patient consultations and transcribes spoken dialogue locally using **OpenAI Whisper** (`base` model)[cite: 3, 4].
- **Clinical Entity Extraction & Decision Support:** Automatically parses transcripts to identify symptoms, medications, possible conditions, and severity levels via custom NLP and clinical rules (`nlp_extraction.py` & `ai_support.py`)[cite: 3, 4].
- **Human-in-the-Loop Review Gate:** Gives physicians full editorial control on a responsive dashboard to review and modify AI-extracted notes before approval[cite: 1, 3].
- **Tamper-Proof RSA Digital Signatures:** Seals finalized prescription payloads using asymmetric **2048-bit RSA-PSS (SHA-256)** cryptography via the doctor's private key[cite: 1, 3, 4].
- **QR-Embedded PDF & WhatsApp Dispatch:** Generates formatted prescription PDFs embedded with verification QR codes (via **ReportLab**) and pushes them directly to the patient's WhatsApp via **Twilio**[cite: 1, 3].
- **Instant Claim Verification API:** Exposes a public-key verification endpoint (`/api/verify-prescription`) allowing pharmacies and insurance processors to detect any post-issuance tampering in milliseconds[cite: 1, 3].
- **Consultation History & Records:** Stores doctor accounts, patient profiles, and signed prescriptions in a relational **MySQL** database (`medinexus_db`) with searchable dashboard history[cite: 1, 3, 6].

---

## 🏗️ System Architecture

MediNexus follows a modular 4-tier architecture[cite: 4]:

1. **Presentation Layer:** Responsive web dashboard (`HTML5`, `CSS3`, `Bootstrap 5`, `JavaScript`) for doctor login, audio recording, clinical review, and record search[cite: 4, 6].
2. **AI & NLP Processing Layer:** Local `Whisper AI` for speech-to-text paired with Python NLP extraction and clinical decision-support modules[cite: 4].
3. **Core Backend & Crypto Gateway:** `Python Flask` REST API orchestrating authentication, RSA-2048 digital signing, PDF/QR generation, and `Twilio WhatsApp` messaging[cite: 4].
4. **Data & Key Storage Layer:** `MySQL` (`Flask-SQLAlchemy` + `PyMySQL`) storing relational records alongside local `.pem` asymmetric key pairs[cite: 1, 4].

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
├── nlp_extraction.py           # Medical NLP keyword extraction module
├── ai_support.py               # Clinical decision support & severity rules
├── generate_keys.py            # One-time RSA-2048 key pair generator
├── requirements.txt            # Python package dependencies
├── .env                        # Environment variables (excluded from Git)
├── keys/                       # RSA private/public .pem keys (excluded from Git)
├── static/
│   ├── js/
│   │   └── app.js              # Frontend dashboard logic & audio recorder
│   └── pdfs/                   # Generated signed prescription PDFs
└── templates/
    └── index.html              # Doctor dashboard UI
