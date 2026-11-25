CREATE DATABASE IF NOT EXISTS medinexus_db;
USE medinexus_db;

-- 1. Users & Doctor Authentication Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'DOCTOR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    whatsapp_number VARCHAR(20) NOT NULL,
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Prescriptions & Digital Signatures Table
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id VARCHAR(50) PRIMARY KEY,
    doctor_id INT NOT NULL,
    patient_id VARCHAR(50) NOT NULL,
    clinical_data JSON NOT NULL,
    digital_signature TEXT NOT NULL,
    pdf_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES users(user_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);