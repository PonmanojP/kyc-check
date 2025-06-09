from flask import Flask, request, jsonify
import pytesseract
import cv2
import re
import numpy as np
import pandas as pd
from flask_cors import CORS
import os
import joblib

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Ensure CORS is open for all routes

# Load the dataset once at startup
DATASET_PATH = os.path.join("references", "synthetic_aadhaar_financial_data_with_fraud.csv")
df = pd.read_csv(DATASET_PATH, dtype=str)  # Read all columns as string to avoid scientific notation

# Load the ML model
MODEL_PATH = os.path.join("model", "fraud_model2.pkl")
model = joblib.load(MODEL_PATH)

def extract_ocr_content(file):
    # Use OCR to extract content from the uploaded document
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    raw_text = pytesseract.image_to_string(gray)

    name = re.search(r'Name:\s*(.*)', raw_text)
    aadhaar = re.search(r'(?:Aadhaar\s*No[:\s]*)?(\d{4}[\s\-]?\d{4}[\s\-]?\d{4,12})', raw_text, re.IGNORECASE)
    dob = re.search(r'(?:DOB|D\.O\.B\.?)[:\s]*([\d]{2}[-/][\d]{2}[-/][\d]{4})', raw_text, re.IGNORECASE)
    gender = re.search(r'(?:Gender)[:\s]*(Male|Female|MALE|FEMALE)', raw_text, re.IGNORECASE)
    if not gender:
        if re.search(r'\b(MALE|Male)\b', raw_text):
            gender = re.search(r'\b(MALE|Male)\b', raw_text)
        elif re.search(r'\b(FEMALE|Female)\b', raw_text):
            gender = re.search(r'\b(FEMALE|Female)\b', raw_text)

    # Remove spaces from Aadhaar number if found
    aadhaar_no_clean = aadhaar.group(1).replace(" ", "") if aadhaar else None

    return {
        "Name": name.group(1).strip() if name else None,
        "DOB": dob.group(1).strip() if dob else None,
        "Gender": gender.group(1).strip() if gender else None,
        "Aadhaar No": aadhaar_no_clean,
    }

def fetch_transactions(aadhar_data):
    """
    aadhar_data: dict with keys like 'Aadhaar No', 'Name', etc.
    Returns: dict with transaction info and average transaction
    """
    aadhaar_no = aadhar_data.get("Aadhaar No")
    if not aadhaar_no:
        return {"error": "Aadhaar number not found in OCR data."}

    # Try to match Aadhaar number (remove spaces, handle scientific notation)
    aadhaar_no_clean = aadhaar_no.replace(" ", "").replace("-", "")
    matches = df[
        (df["AadhaarID"].str.replace(".", "", regex=False).str.replace("E+","", regex=False).str.contains(aadhaar_no_clean, na=False)) |
        (df["AadhaarID"].str.replace(" ", "").str.replace("-", "").str.contains(aadhaar_no_clean, na=False))
    ]

    if matches.empty:
        return {"error": "No transactions found for this Aadhaar number."}

    # Take the first match (assuming unique)
    row = matches.iloc[0]
    avg_transaction = row.get("AverageTransaction")
    max_transaction = row.get("MaxTransaction")
    transaction_count = row.get("TransactionCount")
    return {
        "AadhaarID": row.get("AadhaarID"),
        "Name": row.get("Name"),
        "AverageTransaction": avg_transaction,
        "MaxTransaction": max_transaction,
        "TotalTransactionAmount": row.get("TotalTransactionAmount"),
        "TransactionCount": transaction_count,
        "Fraudulent": row.get("Fraudulent"),
        "raw_row": row.to_dict()
    }

def calculate_average(transactions):
    return transactions.get("AverageTransaction")

def predict_kyc_status(average):
    """
    ML-based KYC status using regression model:
    - If model output >= 0.5: Fraudulent
    - Else: Not Fraudulent
    """
    try:
        avg = float(average)
        model_score = model.predict([[avg]])[0]
        model_pred = 1 if model_score >= 0.5 else 0
    except Exception:
        return {
            "status": "Error",
            "message": "Invalid average transaction amount or model error. Cannot determine KYC status."
        }
    if model_pred == 1:
        return {
            "status": "Rejected",
            "message": "Sorry, KYC cannot be provided. Do check with your nearest KYC center.",
            "model_score": round(model_score, 4),
            "model_pred": int(model_pred)
        }
    else:
        return {
            "status": "Success",
            "message": "KYC successful. You can proceed further.",
            "model_score": round(model_score, 4),
            "model_pred": int(model_pred)
        }

def proceed_kyc(result):
    # Proceed or reject KYC based on model output
    pass

@app.route("/upload", methods=["POST"])
def upload_route():
    # Handle document upload and call OCR extraction
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    extracted_data = extract_ocr_content(file)
    transactions = fetch_transactions(extracted_data)
    average = calculate_average(transactions)
    kyc_result = predict_kyc_status(average)

    return jsonify({
        "extracted": extracted_data,
        "transactions": transactions,
        "average_transaction": average,
        "kyc_result": kyc_result
    })

if __name__ == "__main__":
    app.run(debug=True)