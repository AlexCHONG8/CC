# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

6SPC Pro Max is a medical device quality control system that digitizes handwritten QC inspection records into ISO 13485 compliant statistical process control (SPC) analysis reports. The system automates the transformation from scanned documents to 6-SPC capability analysis with interactive verification.

**Core Value**: Reduces QC report generation from 2 hours to 15 minutes (8x efficiency gain) while maintaining <0.5% error rate.

## Build & Setup Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Environment configuration
# .env must contain: OCR_API_KEY=your_mineru_token_here

# Activate virtual environment (if using .venv)
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

### Execution & Testing

```bash
# CLI test - Fastest way to verify OCR + statistical calculations
python3 main.py

# Interactive Streamlit Dashboard
python3 -m streamlit run src/verify_ui.py

# With custom port (if default 8501 is in use)
python3 -m streamlit run src/verify_ui.py --server.port 8511
```

## Architecture

### Data Flow Pipeline

```
Scan Upload (PDF/JPG/PNG)
    ↓
OCR Extraction (MinerU API v4)
    ↓
Data Validation & Correction (utils.py)
    ↓
SPC Calculation (spc_engine.py)
    ↓
Interactive Verification (verify_ui.py)
    ↓
Report Export (HTML/Excel/History)
```

### Core Components

#### 1. **OCRService** (`src/ocr_service.py`)
MinerU API v4 client wrapper with graceful degradation.

**Key Methods:**
- `extract_table_data(file_path)`: Returns list of dimension sets from scans
- `MinerUClient`: Low-level API handler (upload → poll → retrieve markdown)

**Behavior:**
- If `OCR_API_KEY` missing or API fails: Returns mock data for testing
- Parses markdown tables into structured dimension sets
- Supports multi-dimension detection (multiple parameters per document)

**Usage:**
```python
ocr = OCRService()
data = ocr.extract_table_data("scan.pdf")  # Returns: [{"header": {...}, "measurements": [...]}]
```

#### 2. **SPCEngine** (`src/spc_engine.py`)
Statistical computation engine for process capability analysis.

**Key Methods:**
- `calculate_stats(data, subgroup_size=5)`: Returns all SPC indices and subgroup data
- `_calculate_capability(...)` (internal): Computes Cp/Cpk/Pp/Ppk

**Calculations:**
- **Within-subgroup variation**: σ_within = R-bar / d2 (d2=2.326 for n=5)
- **Overall variation**: σ_overall = sample standard deviation (ddof=1)
- **Cp/Cpk**: Potential capability (using σ_within)
- **Pp/Ppk**: Overall performance (using σ_overall)
- **Subgrouping**: Automatic X-bar/R chart data generation

**Compliance Threshold:** Cpk ≥ 1.33 = PASS

**Usage:**
```python
engine = SPCEngine(usl=10.5, lsl=9.5)
stats = engine.calculate_stats(measurements)
# Returns: {"mean": 10.0, "cpk": 1.33, "subgroups": {...}, ...}
```

#### 3. **Utils Module** (`src/utils.py`)
Data validation, correction, and export utilities (v1.5+ features).

**Key Functions:**
- `detect_outliers(data, threshold=3.0)`: 3σ outlier detection
- `correct_measurements(data, usl, lsl)`: OCR error correction (missing decimals, unit noise, character substitutions)
- `normality_test(data)`: Shapiro-Wilk and Anderson-Darling tests
- `suggest_boxcox(data)`: Box-Cox transformation recommendations
- `calculate_control_limits(data)`: X-bar/R chart control limits (A2, D3, D4 constants)
- `export_to_excel(data, stats, filepath)`: 4-sheet Excel export (info, raw data, subgroups, summary)
- `HistoryManager`: Class for report save/load/search/delete operations

**HistoryManager Methods:**
- `save_report(data, stats, metadata)`: Save to `reports_history/`
- `list_reports()`: Get all saved reports
- `search_reports(query)`: Filter by batch ID or keyword
- `delete_report(report_id)`: Remove report
- `get_report(report_id)`: Load full report data

#### 4. **Streamlit UI** (`src/verify_ui.py`)
Human-in-the-loop verification dashboard with 6 SPC charts.

**Structure:**
- **Lines 35-235**: Helper functions for Plotly charts (`create_histogram`, `create_qq_plot`, `create_capability_plot`)
  - **IMPORTANT**: These must remain at the top of the file after imports (lines 35-235) to avoid NameError during Streamlit execution
- **Lines 240+**: Page configuration, CSS, and main UI logic
- **Three pages**: Data Analysis, History, Settings

**6 SPC Charts:**
1. Individual Readings Plot (single values)
2. X-bar Control Chart (subgroup means)
3. R Control Chart (subgroup ranges)
4. Histogram with normal fit (20 bins)
5. Q-Q Plot (normality assessment)
6. Capability Plot (distribution + PPM calculations)

**Features:**
- Real-time editable data tables with automatic stat recalculation
- Multi-dimension support with expandable sections
- Smart correction button (applies `correct_measurements`)
- Outlier highlighting in red
- Excel export (4 worksheets via `export_to_excel`)
- History save/load/search/delete
- HTML report preview with print support (Ctrl+P)

### Data Structures

#### Dimension Set (OCR → SPC)
```python
{
    "header": {
        "batch_id": str,           # Batch identifier
        "dimension_name": str,     # Parameter being measured
        "usl": float,              # Upper specification limit
        "lsl": float               # Lower specification limit
    },
    "measurements": List[float]    # Raw measurement values (50+ typical)
}
```

#### SPC Results (SPCEngine output)
```python
{
    "mean": float,
    "std_overall": float,         # Sample std (ddof=1)
    "std_within": float,          # R-bar/d2 estimate
    "min": float, "max": float,
    "count": int,
    "cp": float, "cpk": float,    # Potential capability
    "pp": float, "ppk": float,    # Overall performance
    "cpk_status": "PASS" | "FAIL",
    "subgroups": {
        "x_bar": List[float],      # Subgroup means
        "r": List[float],          # Subgroup ranges
        "size": int                # Subgroup size (default 5)
    }
}
```

#### Control Limits (X-bar/R charts)
```python
{
    "x_bar": {
        "ucl": float,  # X-double-bar + A2 * R-bar
        "cl": float,   # X-double-bar
        "lcl": float   # X-double-bar - A2 * R-bar
    },
    "r": {
        "ucl": float,  # D4 * R-bar
        "cl": float,   # R-bar
        "lcl": float   # D3 * R-bar (often 0 for n=5)
    },
    "constants": {
        "A2": float, "D3": float, "D4": float, "d2": float
    }
}
```

### File System

```
6SPC/
├── src/
│   ├── __init__.py
│   ├── ocr_service.py          # MinerU API client
│   ├── spc_engine.py           # SPC calculations
│   ├── verify_ui.py            # Streamlit dashboard (1000+ lines)
│   └── utils.py                # v1.5 utilities (corrections, tests, export, history)
├── reports_history/             # JSON report storage (managed by HistoryManager)
│   └── index.json              # Report index metadata
├── Scan PDF/                    # Test files for real OCR validation
├── main.py                      # CLI orchestrator (demonstrates full pipeline)
├── requirements.txt             # Python dependencies
├── .env                         # OCR_API_KEY (not in git)
├── CLAUDE.md                    # This file
├── README.md                    # User-facing documentation
└── sample_scan.pdf              # API flow test file
```

## Statistical Standards

### Control Chart Constants (n=5)
- **A2 = 0.577**: X-bar chart multiplier
- **D3 = 0**: R chart LCL multiplier
- **D4 = 2.114**: R chart UCL multiplier
- **d2 = 2.326**: Within-subgroup sigma divisor

### Formulas
- **σ_within** = R-bar / d2
- **σ_overall** = sample standard deviation
- **Cp** = (USL - LSL) / (6 × σ_within)
- **Cpk** = min[(USL - μ)/(3σ_within), (μ - LSL)/(3σ_within)]
- **Pp** = (USL - LSL) / (6 × σ_overall)
- **Ppk** = min[(USL - μ)/(3σ_overall), (μ - LSL)/(3σ_overall)]

### Normality Tests
- **Shapiro-Wilk**: 3 ≤ n ≤ 5000, p ≥ 0.05 → normal
- **Anderson-Darling**: Any n, statistic < critical value → normal

## Project Standards

### Code Organization
- **PEP 8** for Python code style
- **Separation of Concerns**:
  - OCR operations → `OCRService` only
  - SPC math → `SPCEngine` only
  - Validation/correction → `utils.py` functions
  - UI logic → `verify_ui.py` only
- **No Circular Imports**: Utils depends on scipy/numpy, not on SPCEngine/OCRService

### Error Handling
- **Graceful Degradation**: OCR failures fall back to mock data
- **User-Facing Errors**: Streamlit error messages, not stack traces
- **Data Validation**: Warn on incomplete extraction (< 20% expected data)

### Helper Function Placement (Critical)
When editing `src/verify_ui.py`:
- **ALWAYS define helper functions before line 240** (after imports, before page config)
- Streamlit executes top-to-bottom on every interaction
- Moving chart functions to bottom causes NameError
- Current valid location: Lines 35-235

### UI/UX Patterns
- **Medical-grade color scheme**: Teal/cyan (#0891B2), green (#22C55E), red (#EF4444)
- **Expandable sections**: Use `st.expander()` for multi-dimension data
- **Editable tables**: `st.data_editor()` for in-place editing
- **Real-time updates**: Use session state to track data changes

## Environment Variables

```bash
# Required for OCR functionality
OCR_API_KEY=your_mineru_token_here

# Optional: MinerU API endpoint (default: https://mineru.net/api/v4)
MINERU_BASE_URL=https://mineru.net/api/v4
```

## Testing Strategy

### Unit Testing
```bash
# Test OCR safeguards (mock data flow)
python3 main.py  # Uses sample_scan.pdf

# Expected output:
# - OCR extraction success
# - 3+ dimension sets detected
# - Corrections applied (missing decimals, unit noise)
# - Outliers detected (if any)
# - Cpk/Pp indices calculated
# - Normality test passed/failed
# - Control limits computed
```

### Integration Testing
```bash
# Test full dashboard workflow
python3 -m streamlit run src/verify_ui.py

# Manual checklist:
# 1. Upload PDF/JPG scan
# 2. Verify OCR extraction
# 3. Click "✨ 智能修正数据" (smart correction)
# 4. Edit data table cells
# 5. Check stat recalculation
# 6. View all 6 charts
# 7. Export Excel
# 8. Save to history
# 9. Search history
# 10. Load saved report
```

### Test Data Locations
- **Unit tests**: `sample_scan.pdf` (project root)
- **Real scans**: `Scan PDF/` directory
- **History tests**: `reports_history/` (auto-created on first save)

## Common Issues

### Streamlit NameError
**Symptom**: `NameError: name 'create_histogram' is not defined`
**Cause**: Helper functions moved below line 240 in `verify_ui.py`
**Fix**: Keep chart helper functions at lines 35-235 (after imports, before page config)

### Port Conflicts
**Symptom**: `Port 8501 is already in use`
**Fix 1**: Kill existing process: `pkill -f "streamlit run src/verify_ui.py"`
**Fix 2**: Use different port: `python3 -m streamlit run src/verify_ui.py --server.port 8511`

### OCR API Failures
**Symptom**: `MinerU API Error (Falling back to multi-mock)`
**Behavior**: System uses mock data automatically - this is intentional graceful degradation
**Fix**: Check `.env` for valid `OCR_API_KEY`, or use mock data for development

### Missing Dependencies
**Symptom**: `ModuleNotFoundError: No module named 'plotly'`
**Fix**: `pip install -r requirements.txt`

### File Upload Type Error
**Symptom**: `expected str, bytes or os.PathLike object, not UploadedFile`
**Cause**: Streamlit's `st.file_uploader()` returns `UploadedFile` objects (in-memory file-like objects), but `OCRService.extract_table_data()` expects file path strings
**Fix Implemented** (lines 400-411 in `verify_ui.py`):
```python
# Save uploaded file to temp location for OCR processing
with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
    tmp_file.write(uploaded_file.getbuffer())
    tmp_file_path = tmp_file.name

try:
    st.session_state.dim_data = ocr.extract_table_data(tmp_file_path)
    st.session_state.original_data = [d.copy() for d in st.session_state.dim_data]
finally:
    # Clean up temp file
    if os.path.exists(tmp_file_path):
        os.unlink(tmp_file_path)
```
**Note**: The fix automatically handles cleanup via the `finally` block to prevent temp file accumulation
