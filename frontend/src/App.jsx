import React, { useState } from "react";
import "./App.css";
import jsPDF from "jspdf";

function App() {
  const [file, setFile] = useState(null);
  const [extracted, setExtracted] = useState(null);
  const [transactions, setTransactions] = useState(null);
  const [average, setAverage] = useState(null);
  const [kycResult, setKycResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [darkMode, setDarkMode] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setExtracted(null);
    setTransactions(null);
    setAverage(null);
    setKycResult(null);
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setExtracted(null);
    setTransactions(null);
    setAverage(null);
    setKycResult(null);
    setError("");
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (response.ok && data.extracted) {
        setExtracted(data.extracted);
        setTransactions(data.transactions);
        setAverage(data.average_transaction);
        setKycResult(data.kyc_result);
      } else {
        setError(data.error || "Extraction failed.");
      }
    } catch (err) {
      setError("Server error. Please try again.");
    }
    setLoading(false);
  };

const handleDownloadPDF = () => {
  const doc = new jsPDF();
  doc.setFontSize(16);
  doc.text("KYC Report", 15, 15);

  doc.setFontSize(12);
  doc.text("Extracted Details:", 15, 30);
  let y = 38;
  if (extracted) {
    Object.entries(extracted).forEach(([key, value]) => {
      doc.text(`${key}: ${value || "Not found"}`, 20, y);
      y += 8;
    });
  }

  if (average || (transactions && (transactions.MaxTransaction || transactions.TransactionCount))) {
    doc.text("Transaction Summary:", 15, y + 4);
    y += 12;
    if (average) {
      doc.text(`Average Transaction: ₹ ${average}`, 20, y);
      y += 8;
    }
    if (transactions && transactions.MaxTransaction) {
      doc.text(`Maximum Transaction: ₹ ${transactions.MaxTransaction}`, 20, y);
      y += 8;
    }
    if (transactions && transactions.TransactionCount) {
      doc.text(`Transaction Count: ${transactions.TransactionCount}`, 20, y);
      y += 8;
    }
  }

  if (kycResult) {
    doc.setFontSize(13);
    doc.text("KYC Result:", 15, y);
    doc.setFontSize(12);
    doc.text(`${kycResult.status}: ${kycResult.message}`, 20, y + 8);
    y += 18;

    if (kycResult.status === "Rejected") {
      doc.setFont("helvetica", "italic");
      doc.text(
        "Reason: The average transaction amount exceeded the allowed threshold, indicating a potential risk profile. For further assistance, please visit your nearest KYC center with your documents.",
        15,
        y,
        { maxWidth: 180 }
      );
      y += 24;
      doc.setFont("helvetica", "normal");
      doc.setTextColor(200, 0, 0);
      doc.text(
        "Note: Visit your nearest KYC center for manual verification.",
        15,
        y
      );
      doc.setTextColor(0, 0, 0);
    }
  }

  doc.save("kyc_report.pdf");
};

  const handleToggleDark = () => setDarkMode((prev) => !prev);

  return (
    <div className={`kyc-bg${darkMode ? " dark" : ""}`}>
      <button
        className="dark-toggle-btn"
        onClick={handleToggleDark}
        aria-label="Toggle dark mode"
        title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
      >
        {darkMode ? "🌙" : "☀️"}
      </button>
      <div className="kyc-container">
        <h1 className="kyc-title">KYC Document Checker</h1>
        <form onSubmit={handleSubmit} className="kyc-form">
          <label className="kyc-label">
            Upload Aadhar Document
            <input
              type="file"
              accept="image/*,application/pdf"
              onChange={handleFileChange}
              className="kyc-input"
              required
            />
          </label>
          <button type="submit" className="kyc-btn" disabled={loading}>
            {loading ? "Extracting..." : "Extract & Check KYC"}
          </button>
        </form>
        {error && (
          <div className="kyc-section">
            <div className="kyc-result kyc-result-fail">{error}</div>
          </div>
        )}
        {extracted && (
          <div className="kyc-section">
            <h2 className="kyc-subtitle">Extracted Details</h2>
            <div className="kyc-details">
              {Object.entries(extracted).map(([key, value]) => (
                <div key={key} className="kyc-detail-row">
                  <span className="kyc-detail-key">{key}</span>
                  <span className="kyc-detail-value">
                    {value || <em>Not found</em>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        {average && (
          <div className="kyc-section">
            <h2 className="kyc-subtitle">Average Transaction</h2>
            <div className="kyc-result kyc-result-pass">₹ {average}</div>
          </div>
        )}
        {kycResult && (
          <div className="kyc-section">
            <h2 className="kyc-subtitle">KYC Result</h2>
            <div
              className={
                kycResult.status === "Success"
                  ? "kyc-result kyc-result-pass"
                  : "kyc-result kyc-result-fail"
              }
            >
              {kycResult.message}
            </div>
            <center>
              <button
                className="kyc-btn"
                style={{ marginTop: "18px" }}
                onClick={handleDownloadPDF}
                type="button"
              >
                Get Report
              </button>
            </center>
          </div>
        )}
      </div>
      <footer className="kyc-footer">© 2025 KYC Checker</footer>
    </div>
  );
}

export default App;