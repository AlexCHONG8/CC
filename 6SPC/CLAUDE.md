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

#### 5. **AnalysisEngine** (`src/analysis_engine.py`)
AI-powered analysis engine for plastic injection hot runner process control.

**Purpose**: Generates intelligent insights and improvement recommendations based on SPC data.

**Key Class: `PlasticInjectionAnalyzer`**
- `analyze_dimension(dim_data, stats)`: Returns comprehensive analysis including:
  - Status rating (EXCELLENT/GOOD/ACCEPTABLE/NEEDS_IMPROVEMENT/CRITICAL)
  - Risk level (LOW/MEDIUM/HIGH/CRITICAL)
  - Overall assessment (bilingual Chinese/English)
  - Capability analysis (Cp vs Cpk, centering, potential vs overall)
  - Stability analysis (within vs overall variation, drift detection)
  - Improvement actions (specific to hot runner systems)
  - Hot runner tips (temperature control,浇口, timing, etc.)

- `generate_executive_summary(analyses)`: Aggregates analysis across all dimensions

**Thresholds**:
- EXCELLENT: Cpk ≥ 1.67, PPM ≤ 100
- GOOD: Cpk ≥ 1.33, PPM ≤ 1,000
- ACCEPTABLE: Cpk ≥ 1.00, PPM ≤ 10,000
- CRITICAL: Cpk < 1.0 or PPM > 50,000

**Usage**: Used by `dashboard_generator.py` to provide AI-powered insights in HTML reports

#### 6. **DashboardGenerator** (`src/dashboard_generator.py`)
Professional HTML report generator with tabbed interface for ISO 13485 compliance.

**Key Function: `generate_professional_dashboard(dim_data, stats_list)`**
- Generates multi-tab HTML reports with executive summary
- Creates all 6 SPC charts with enhanced medical-grade styling
- Includes AI-powered analysis from `PlasticInjectionAnalyzer`
- Saves to `reports/` directory with timestamp filename

**Chart Functions** (see "Chart Generation Best Practices" section):
- `_create_individual_plot()`: Line plot with target/nominal line
- `_create_xbar_chart()`: X-bar control chart with UCL/CL/LCL
- `_create_r_chart()`: R control chart with diamond markers
- `_create_histogram()`: Histogram with normal fit
- `_create_qq_plot()`: Q-Q plot for normality assessment
- `_create_capability_plot()`: Distribution curve with PPM calculations

**HTML Features**:
- Tabbed navigation (Executive Summary + per-dimension tabs)
- Print-friendly styling (Ctrl+P for PDF export)
- Interactive Plotly charts via CDN
- Bilingual labels (Chinese + English)
- Responsive design

**Report Storage**: HTML reports saved to `reports/` directory (auto-created)

---

### Dual Chart System Architecture

The system has TWO separate chart generation approaches:

#### 1. Streamlit Dashboard Charts (`verify_ui.py` lines 35-235)
- **Purpose**: Interactive real-time charts in Streamlit UI
- **Location**: Helper functions defined at top of `verify_ui.py`
- **Return Type**: Plotly Figure objects (`go.Figure()`)
- **Usage**: Displayed via `st.plotly_chart()`
- **Interactivity**: Full Plotly interactivity, zoom, pan, hover

#### 2. HTML Export Charts (`dashboard_generator.py`)
- **Purpose**: Static charts in generated HTML reports
- **Location**: Separate module for HTML report generation
- **Return Type**: HTML strings (`fig.to_html(full_html=False, include_plotlyjs='cdn')`)
- **Usage**: Embedded in HTML template for export/print
- **Interactivity**: Preserved via Plotly CDN in HTML

**Key Difference**:
```python
# Streamlit version (verify_ui.py)
def create_histogram(data, title, usl, lsl, mean):
    fig = go.Figure()
    # ... build chart ...
    return fig  # Return Plotly Figure object

# HTML export version (dashboard_generator.py)
def _create_histogram(measurements, usl, lsl):
    fig = go.Figure()
    # ... build chart ...
    return fig.to_html(full_html=False, include_plotlyjs='cdn')  # Return HTML string
```

**When to Use Which**:
- Use `verify_ui.py` charts for: Real-time interactive dashboard
- Use `dashboard_generator.py` charts for: Final HTML report generation and export

---

### Component Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Upload Scan                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │   OCRService (ocr_service)   │
                │   - Extract measurements    │
                │   - Parse markdown tables   │
                │   - Multi-dimension detect  │
                └──────────────┬──────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
          ┌──────────────────┐   ┌─────────────────┐
          │ SPCEngine        │   │ Utils.py        │
          │ - Calculate      │   │ - Corrections  │
          │   Cp/Cpk/Pp/Ppk  │   │ - Outlier detect│
          │ - Subgroup data  │   │ - Normality test│
          └────────┬─────────┘   └────────┬─────────┘
                   │                     │
                   └──────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
          ┌─────────────────┐  ┌──────────────────┐
          │ verify_ui.py    │  │ AnalysisEngine   │
          │ - Interactive   │  │ - AI insights    │
          │   dashboard     │  │ - Recommendations│
          │ - Edit data     │  └────────┬─────────┘
          │ - View charts   │           │
          └────────┬────────┘           │
                   │                    │
                   └────────┬───────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌───────────────────┐   ┌─────────────────────┐
    │ Streamlit Display │   │ DashboardGenerator  │
    │ (Real-time)       │   │ - Generate HTML     │
    │ - 6 interactive   │   │ - Embed charts      │
    │   charts          │   │ - Add AI analysis   │
    │ - Edit/Export     │   │ - Save to reports/  │
    └───────────────────┘   └─────────────────────┘
```

---

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

## Chart Generation Best Practices

### 6 SPC Chart Styling Standards

All charts in the 6SPC system MUST follow these professional medical-grade styling standards:

#### Visual Enhancements
- **Data Point Visibility**:
  - Marker size: 8-10px (not 7px or smaller)
  - Use white stroke around markers: `line=dict(width=2, color='white')`
  - Marker opacity: 0.85-0.9 for better visual hierarchy
  - Use distinct symbols: circles for individual, diamonds for R chart

- **Line Styling**:
  - Main data line width: 3px (not 2.5px)
  - Control limit lines (UCL/LCL): 3px dashed red
  - Center line (CL): 2.5px solid green
  - Grid lines: 1px with 0.08 opacity

- **Label & Typography**:
  - Title font size: 16px with bold weight
  - Axis label font size: 13px with bold weight
  - Annotation font size: 12px with bold weight
  - General font size: 11px
  - Use HTML bold tags in annotations: `<b>UCL</b>: 1.234`

- **Layout & Spacing**:
  - Chart height: 450px (not 420px)
  - Margins: `dict(l=60, r=30, t=50, b=60)` for proper label display
  - Grid color: `rgba(0,0,0,0.08)` for subtle visibility
  - Zero line: 1.5px gray for axis reference

- **Interactive Hover Templates**:
  ```python
  hovertemplate='<b>Sample %{x}</b><br>Value: %{y:.4f}<extra></extra>'
  ```

- **Legend Position**:
  ```python
  legend=dict(
      orientation="h",
      yanchor="bottom",
      y=1.02,
      xanchor="right",
      x=1,
      font=dict(size=11)
  )
  ```

#### Color Scheme (Medical-Grade)
- Primary data: `#0891B2` (teal/cyan)
- UCL/LCL limits: `#DC2626` (red)
- Center/Target: `#16A34A` (green) or `#22C55E`
- Background: `rgba(255, 255, 255, 0.98)`
- Paper: `white`
- Text: `#374151` (dark gray, not pure black)

#### Chart-Specific Requirements

**Individual Values Plot** (`_create_individual_plot` in `dashboard_generator.py`):
- Add target line at nominal (USL+LSL)/2 with dot pattern
- Circle markers with white stroke
- Grid lines enabled

**X-bar Control Chart** (`_create_xbar_chart`):
- Circle markers (size 10px)
- UCL/LCL: 3px dashed red
- CL: 2.5px solid green
- Bold annotations: `<b>UCL</b>: {value:.4f}`

**R Control Chart** (`_create_r_chart`):
- Diamond markers (distinct from X-bar)
- Same line styling as X-bar
- Only show LCL if > 0

**Histogram** (`_create_histogram` in `verify_ui.py`):
- 20 bins with 0.65-0.7 opacity
- Red normal fit curve (width 2-3px)
- Vertical USL/LSL lines with dashed pattern

**Q-Q Plot** (`_create_qq_plot`):
- Sample markers: 9px with white stroke
- Reference line: 2.5px red dashed
- Zero lines on both axes

**Capability Plot** (`_create_capability_plot`):
- Distribution fill: `rgba(8, 145, 178, 0.15)`
- Annotation box with white background (0.95 opacity)
- 2px border in primary color
- 10px border padding

#### Common Mistakes to Avoid

❌ **WRONG**:
```python
marker=dict(size=7, color='#0891B2')  # Too small, no contrast
line=dict(width=2, dash='dash')      # Too thin, hard to see
annotation_text=f"UCL: {ucl}"        # Not bold, hard to read
height=420                            # Too cramped
```

✅ **CORRECT**:
```python
marker=dict(size=10, color='#0891B2', line=dict(width=2, color='white'), opacity=0.9)
line=dict(width=3, dash='dash')
annotation_text=f"<b>UCL</b>: {ucl:.4f}"
height=450
```

#### Dashboard Generator Chart Functions

When creating charts for HTML dashboard export in `src/dashboard_generator.py`:

1. Always return `fig.to_html(full_html=False, include_plotlyjs='cdn')`
2. Use consistent styling across all 6 SPC charts
3. Apply the medical-grade color scheme
4. Ensure proper spacing with margins
5. Add interactive hover templates for better UX
6. Use bilingual labels (Chinese + English) for all text elements

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
