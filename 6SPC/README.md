# 🛡️ 6SPC Analysis Report Tool

A "Zero-Friction" digitization and reporting tool for medical device plastic injection components. It converts handwritten QC scans into compliant 6SPC analysis reports using AI (MinerU).

## 📋 Prerequisites

1. **Python 3.9+**
2. **MinerU API Key**: Already configured in your `.env` file.
3. **Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

---

## 🧪 How to Test

### 1. Functional Logic Test (CLI Mode)

This is the fastest way to verify the MinerU API connection and the statistical calculations.

```bash
python3 main.py
```

**What to expect**:

- The script will "digitize" a sample file.
- It will demonstrate the **Logic Safeguards** (fixing decimal errors like `103` -> `10.3`).
- It will print a formatted SPC report in your terminal (Mean, Cpk, Ppk, etc.).

### 2. Interactive Verification (Dashboard Mode)

This is the "Human-in-the-Loop" portal where you can verify OCR results side-by-side with original scans.

```bash
python3 -m streamlit run src/verify_ui.py
```

**Steps**:

1. Open the URL provided (usually `http://localhost:8501`).
2. Upload a scanned QC sheet (PDF/JPG/PNG).
3. Review the AI-extracted table on the right.
4. Correct any red-flagged cells.
5. Watch the **X-bar Control Chart** and **Cpk metrics** update in real-time.
6. Click **"Approve & Generate PDF Report"**.

### 3. Logic Safeguard Verification

The system is pre-configured to handle these scenarios automatically:

- **Missing Decimals**: `102` will be cleaned to `10.2` if the USL is `10.5`.
- **Unit Noise**: `10.1mm` will be cleaned to `10.1`.
- **Completeness**: If a 50-point batch only has 10 points recognized, you will see a `⚠️ Completeness Alert`.

---

## 📁 Project Structure

- `src/ocr_service.py`: MinerU v4 API Integration.
- `src/spc_engine.py`: High-accuracy statistical indices.
- `src/verify_ui.py`: Streamlit Dashboard.
- `main.py`: CLI Orchestrator.
- `.env`: API Credentials.
