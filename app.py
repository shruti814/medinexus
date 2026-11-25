import os
import json
import base64
import secrets
import tempfile
from functools import wraps
from urllib.parse import quote_plus

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import qrcode

from nlp_extraction import extract_medical_info
from ai_support import ai_medical_support

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "medinexus-dev-secret-key-change-me")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ==========================================
# 1. DATABASE CONFIGURATION
# ==========================================
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "1234")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "medinexus_db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{quote_plus(MYSQL_USER)}:"
    f"{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}/{MYSQL_DB}"
)

db = SQLAlchemy(app)
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(
            os.getenv("WHISPER_MODEL", "base"),
            device="cpu",
            compute_type="int8"
        )
    return _whisper_model


# ==========================================
# 2. DATABASE MODELS
# ==========================================
class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="DOCTOR")


class Patient(db.Model):
    __tablename__ = "patients"
    patient_id = db.Column(db.String(50), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    whatsapp_number = db.Column(db.String(20))
    medical_history = db.Column(db.Text)


class Prescription(db.Model):
    __tablename__ = "prescriptions"
    prescription_id = db.Column(db.String(50), primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    patient_id = db.Column(db.String(50), db.ForeignKey("patients.patient_id"), nullable=False)
    clinical_data = db.Column(db.JSON, nullable=False)
    digital_signature = db.Column(db.Text, nullable=False)
    pdf_path = db.Column(db.String(255))


# ==========================================
# 3. AUTHENTICATION DECORATOR
# ==========================================
def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("doctor_id"):
            return jsonify({
                "status": "error",
                "message": "Please login first"
            }), 401
        return function(*args, **kwargs)
    return wrapper


# ==========================================
# 4. DIGITAL SIGNATURE FUNCTIONS
# ==========================================
def load_private_key():
    with open("keys/doctor_private_key.pem", "rb") as file:
        return serialization.load_pem_private_key(file.read(), password=None)


def load_public_key():
    with open("keys/doctor_public_key.pem", "rb") as file:
        return serialization.load_pem_public_key(file.read())


def canonical_payload(rx_id, doctor_id, patient_id, clinical_data):
    payload = {
        "rxId": rx_id,
        "doctorId": int(doctor_id),
        "patientId": patient_id,
        "data": clinical_data
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")


def generate_digital_signature(payload_bytes):
    private_key = load_private_key()
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("utf-8")


def verify_digital_signature(payload_bytes, signature_b64):
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        public_key = load_public_key()
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


# ==========================================
# 5. PDF GENERATION & WHATSAPP DISPATCH
# ==========================================
def create_prescription_pdf(prescription_id, doctor_name, patient_name, clinical_data, signature):
    os.makedirs("static/pdfs", exist_ok=True)
    pdf_path = f"static/pdfs/prescription_{prescription_id}.pdf"
    qr_path = f"static/pdfs/qr_{prescription_id}.png"

    qr_payload = f"MediNexus Verify | ID: {prescription_id} | Sig: {signature[:24]}..."
    qrcode.make(qr_payload).save(qr_path)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, 750, "MediNexus - Digital Prescription")

    c.setFont("Helvetica", 12)
    c.drawString(60, 710, f"Prescription ID: {prescription_id}")
    c.drawString(60, 690, f"Doctor: {doctor_name}")
    c.drawString(60, 670, f"Patient: {patient_name}")

    c.setFont("Helvetica-Bold", 13)
    c.drawString(60, 630, "Clinical Summary")

    c.setFont("Helvetica", 11)
    c.drawString(60, 610, "Symptoms: " + ", ".join(clinical_data.get("symptoms", [])))
    c.drawString(60, 590, "Conditions: " + ", ".join(clinical_data.get("possible_conditions", [])))
    c.drawString(60, 570, "Medications recorded: " + ", ".join(clinical_data.get("medications", [])))
    c.drawString(60, 550, f"Severity: {clinical_data.get('severity', 'UNKNOWN')}")

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(60, 510, "Prototype output: not a diagnosis or prescription.")
    c.drawString(60, 495, "Clinical decisions require licensed doctor review.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, 455, "Digital Signature (RSA-PSS SHA-256):")
    c.setFont("Helvetica", 8)
    c.drawString(60, 440, signature[:95])
    c.drawString(60, 428, signature[95:190])

    c.drawImage(qr_path, 420, 440, width=100, height=100)
    c.save()

    if os.path.exists(qr_path):
        os.remove(qr_path)

    return pdf_path


def send_whatsapp_notification(to_number, patient_name, prescription_id, pdf_path):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    if not account_sid or not auth_token or not to_number:
        return None

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        formatted_to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
        msg_kwargs = {
            "from_": from_whatsapp,
            "to": formatted_to,
            "body": (
                f"Hello {patient_name}, your digitally signed MediNexus prescription "
                f"({prescription_id}) is ready."
            )
        }
        if public_base_url:
            msg_kwargs["media_url"] = [f"{public_base_url}/{pdf_path}"]

        message = client.messages.create(**msg_kwargs)
        return message.sid
    except Exception:
        app.logger.exception("Twilio WhatsApp dispatch failed")
        return None


# ==========================================
# 6. ROUTES
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/me", methods=["GET"])
def current_user():
    if session.get("doctor_id"):
        return jsonify({
            "authenticated": True,
            "userId": session["doctor_id"],
            "fullName": session.get("doctor_name", "Doctor")
        })
    return jsonify({"authenticated": False}), 200


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("fullName") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name or not email or len(password) < 8:
        return jsonify({
            "status": "error",
            "message": "Name, email and password (8+ characters) required"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "status": "error",
            "message": "Email already registered"
        }), 409

    user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Doctor registered successfully"
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

    session.clear()
    session["doctor_id"] = user.user_id
    session["doctor_name"] = user.full_name

    return jsonify({
        "status": "success",
        "userId": user.user_id,
        "fullName": user.full_name
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({
        "status": "success",
        "message": "Logged out"
    })


@app.route("/api/process-audio-consultation", methods=["POST"])
@login_required
def process_audio_consultation():
    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify({
            "status": "error",
            "message": "No audio file provided"
        }), 400

    try:
        model = get_whisper_model()
        suffix = os.path.splitext(audio_file.filename or "")[1] or ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_path = temp.name
            audio_file.save(temp_path)

        try:
            segments, _ = model.transcribe(temp_path)
            transcription = " ".join(seg.text for seg in segments).strip()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        extracted = extract_medical_info(transcription)
        support = ai_medical_support(extracted["symptoms"])

        return jsonify({
            "status": "success",
            "transcript": transcription,
            "extracted_data": {
                "symptoms": extracted["symptoms"],
                "medications": extracted["medicines"],
                "possible_conditions": support["possible_conditions"],
                "severity": support["severity"],
                "urgent_warning": support["urgent_warning"],
                "disclaimer": support["disclaimer"]
            }
        })

    except Exception as exc:
        app.logger.exception("Audio processing failed")
        return jsonify({
            "status": "error",
            "message": f"Audio processing failed: {str(exc)}"
        }), 500


@app.route("/api/finalize-prescription", methods=["POST"])
@login_required
def finalize_prescription():
    data = request.get_json(silent=True) or {}
    doctor_id = session["doctor_id"]
    patient_id = (data.get("patientId") or "").strip()
    patient_name = (data.get("patientName") or "").strip()
    patient_whatsapp = (data.get("patientWhatsApp") or "").strip()
    clinical_data = data.get("clinicalData")

    if not patient_id or not patient_name or not isinstance(clinical_data, dict):
        return jsonify({
            "status": "error",
            "message": "Patient information and clinical data are required"
        }), 400

    try:
        patient = db.session.get(Patient, patient_id)
        if not patient:
            patient = Patient(
                patient_id=patient_id,
                full_name=patient_name,
                whatsapp_number=patient_whatsapp
            )
            db.session.add(patient)
            db.session.flush()
        elif patient_whatsapp:
            patient.whatsapp_number = patient_whatsapp

        rx_id = "RX_" + secrets.token_hex(4).upper()
        payload = canonical_payload(rx_id, doctor_id, patient_id, clinical_data)
        signature = generate_digital_signature(payload)

        pdf_path = create_prescription_pdf(
            rx_id,
            session["doctor_name"],
            patient_name,
            clinical_data,
            signature
        )

        prescription = Prescription(
            prescription_id=rx_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            clinical_data=clinical_data,
            digital_signature=signature,
            pdf_path=pdf_path
        )
        db.session.add(prescription)
        db.session.commit()

        whatsapp_sid = send_whatsapp_notification(
            patient_whatsapp,
            patient_name,
            rx_id,
            pdf_path
        )

        return jsonify({
            "status": "success",
            "prescriptionId": rx_id,
            "signature": signature,
            "pdfPath": pdf_path,
            "whatsappSid": whatsapp_sid
        }), 201

    except Exception:
        db.session.rollback()
        app.logger.exception("Prescription finalization failed")
        return jsonify({
            "status": "error",
            "message": "Prescription generation failed"
        }), 500


@app.route("/api/verify-prescription", methods=["POST"])
@login_required
def verify_prescription():
    data = request.get_json(silent=True) or {}
    rx_id = (data.get("prescriptionId") or "").strip()

    record = db.session.get(Prescription, rx_id)
    if not record:
        return jsonify({
            "status": "NOT_FOUND",
            "message": "Prescription not found"
        }), 404

    if record.doctor_id != session["doctor_id"]:
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 403

    payload = canonical_payload(
        record.prescription_id,
        record.doctor_id,
        record.patient_id,
        record.clinical_data
    )
    valid = verify_digital_signature(payload, record.digital_signature)

    return jsonify({
        "prescriptionId": rx_id,
        "isTampered": not valid,
        "status": "VALID" if valid else "TAMPERED"
    })


@app.route("/api/my-records", methods=["GET"])
@login_required
def get_my_records():
    doctor_id = session["doctor_id"]

    records = (
        db.session.query(Prescription, Patient)
        .join(Patient, Prescription.patient_id == Patient.patient_id)
        .filter(Prescription.doctor_id == doctor_id)
        .all()
    )

    output = []
    for rx, patient in records:
        output.append({
            "prescriptionId": rx.prescription_id,
            "patientId": patient.patient_id,
            "patientName": patient.full_name,
            "patientWhatsApp": patient.whatsapp_number or "N/A",
            "clinicalData": rx.clinical_data,
            "pdfPath": rx.pdf_path
        })

    return jsonify({
        "status": "success",
        "count": len(output),
        "records": output
    })


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )