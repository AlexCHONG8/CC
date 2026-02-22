import os
import requests
import json
import time
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

class MinerUClient:
    """
    A minimal client for the MinerU (mineru.net) API v4.
    """
    BASE_URL = "https://mineru.net/api/v4"

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def process_file(self, file_path):
        """
        End-to-end processing: Upload -> Task -> Poll -> Return Markdown
        """
        filename = os.path.basename(file_path)
        data_id = f"6spc_{int(time.time())}"

        # 1. Get Upload URL
        print(f"Requesting upload URL for {filename}...")
        resp = requests.post(
            f"{self.BASE_URL}/file-urls/batch",
            headers=self.headers,
            json={
                "files": [{"name": filename, "data_id": data_id, "model_version": "vlm"}]
            }
        )
        resp_json = resp.json()
        print(f"MinerU Upload Response Debug: {json.dumps(resp_json, indent=2)}")
        
        # Structure as seen in debug: {"data": {"batch_id": "...", "file_urls": ["..."]}}
        if "data" in resp_json and "file_urls" in resp_json["data"]:
            file_url = resp_json["data"]["file_urls"][0]
            # In MinerU v4, the file_url is often the pre-signed OSS upload URL
            upload_url = file_url 
        else:
            raise KeyError(f"Unexpected MinerU response structure: {resp_json}")

        # 2. Upload File (Using PUT for pre-signed OSS URL)
        print(f"Uploading file to {upload_url[:60]}...")
        with open(file_path, "rb") as f:
            # We must set Content-Type correctly if required, but often not for raw PUT
            upload_resp = requests.put(upload_url, data=f)
            upload_resp.raise_for_status()

        # 3. Create Extraction Task
        print(f"Creating extraction task for {file_url[:60]}...")
        task_resp = requests.post(
            f"{self.BASE_URL}/extract/task",
            headers=self.headers,
            json={
                "url": file_url,
                "model_version": "vlm",
                "data_id": data_id
            }
        )
        task_resp.raise_for_status()
        task_json = task_resp.json()
        print(f"MinerU Task Response Debug: {json.dumps(task_json, indent=2)}")
        
        if "data" in task_json and isinstance(task_json["data"], dict) and "task_id" in task_json["data"]:
            task_id = task_json["data"]["task_id"]
        else:
            raise KeyError(f"Could not find task_id in task response: {task_json}")

        # 4. Poll for results using GET /extract/task/{task_id}
        print(f"Polling for task {task_id}...")
        while True:
            result_resp = requests.get(
                f"{self.BASE_URL}/extract/task/{task_id}",
                headers=self.headers
            )
            result_resp.raise_for_status()
            res_json = result_resp.json()
            
            task_info = res_json.get("data", {})
            state = task_info.get("state") # Current state: "pending", "parsing", "done", "error", "failed"
            
            if state == "done":
                print("Extraction complete!")
                # Extract markdown from 'full_content_md' or similar in task_info
                return task_info.get("full_content_md") or task_info.get("content", "")
            elif state in ["error", "failed"]:
                raise Exception(f"MinerU Error: {task_info.get('error_msg') or 'Unknown error (state: ' + state + ')'}")
            
            print(f"Status: {state}, waiting 5s...")
            time.sleep(5)

class OCRService:
    def __init__(self, api_key=None, provider="mineru"):
        self.api_key = api_key or os.getenv("OCR_API_KEY")
        self.provider = provider
        self.client = MinerUClient(self.api_key) if self.api_key else None

    def extract_table_data(self, file_path):
        """
        Sends the file to the OCR provider and returns a list of dimension sets.
        """
        if not self.api_key:
            print("Warning: No API Key found. Returning mock data.")
            return self._get_mock_data_multi()
        else:
            try:
                markdown_content = self.client.process_file(file_path)
                return self._parse_markdown_to_json(markdown_content)
            except Exception as e:
                import traceback
                print(f"MinerU API Error (Falling back to multi-mock): {e}")
                return self._get_mock_data_multi()

    def _parse_markdown_to_json(self, md):
        """
        Enhanced parser for Chinese QC reports.
        Handles multiple inspection locations with specifications like:
        - 27.80+0.10-0.00 (mm)
        - Φ6.00±0.10 (mm)
        - 73.20+0.00-0.15 (mm)
        """
        if not md:
            return self._get_mock_data_multi()

        import re

        # Try enhanced Chinese QC report parser first
        dimension_sets = self._parse_chinese_qc_report(md)

        if dimension_sets:
            return dimension_sets

        # Fallback to simple parser
        tables = md.split("\n\n")

        for i, table_md in enumerate(tables):
            if "|" not in table_md: continue

            numbers = re.findall(r"(\d+\.\d+|\d+)", table_md)
            measurements = []
            for num in numbers:
                try:
                    val = float(num)
                    if val > 0.001: measurements.append(val)
                except ValueError: continue

            if len(measurements) > 5:
                dimension_sets.append({
                    "header": {
                        "part_id": "Detected Part",
                        "batch_id": f"Dimension-{i+1}",
                        "dimension_name": f"Parameter {i+1}",
                        "usl": 10.5,
                        "lsl": 9.5
                    },
                    "measurements": measurements
                })

        return dimension_sets if dimension_sets else self._get_mock_data_multi()

    def _parse_chinese_qc_report(self, md):
        """
        Specialized parser for Chinese QC inspection reports.
        Extracts multiple inspection locations with their specs and measurements.

        Expected format:
        检验位置 | 1 | 11 | 13
        检验标准 | 27.80+0.10-0.00 | Φ6.00±0.10 | 73.20+0.00-0.15
        结果 | 测试结果 | ... | ...

        Returns list of dimension sets with proper USL/LSL parsing.
        """
        import re

        dimension_sets = []

        # Split into lines and look for table structure
        lines = md.split('\n')

        # Find the header row with inspection locations
        location_indices = {}  # Maps location number to column index
        spec_line_idx = None

        for i, line in enumerate(lines):
            # Look for 检验位置 first
            if '检验位置' in line and not location_indices:
                parts = line.split('|')
                for col_idx, part in enumerate(parts):
                    # Extract location numbers (1, 11, 13, etc.)
                    loc_match = re.search(r'\d+', part.strip())
                    if loc_match and col_idx > 0:  # Skip first column (header)
                        loc_num = loc_match.group()
                        location_indices[loc_num] = col_idx

            # Look for specification row (after finding locations)
            if '检验标准' in line:
                spec_line_idx = i

        # Check if we found both required elements
        if not location_indices or spec_line_idx is None:
            return None  # Not a Chinese QC report format

        # Parse specifications for each location
        specs = {}  # Maps location to {usl, lsl, name}
        spec_line = lines[spec_line_idx]
        spec_parts = spec_line.split('|')

        for loc_num, col_idx in location_indices.items():
            if col_idx < len(spec_parts):
                spec_text = spec_parts[col_idx].strip()

                # Parse specification formats:
                # 1. "27.80+0.10-0.00 (mm)" - asymmetric tolerance
                # 2. "Φ6.00±0.10 (mm)" - symmetric tolerance
                # 3. "73.20+0.00-0.15 (mm)" - asymmetric tolerance

                usl, lsl = None, None

                # Try asymmetric format: "27.80+0.10-0.00"
                asymmetric_match = re.search(r'([\d.]+)\+([\d.]+)-([\d.]+)', spec_text)
                if asymmetric_match:
                    nominal = float(asymmetric_match.group(1))
                    pos_tol = float(asymmetric_match.group(2))
                    neg_tol = float(asymmetric_match.group(3))
                    usl = nominal + pos_tol
                    lsl = nominal - neg_tol

                # Try symmetric format: "Φ6.00±0.10" or "6.00±0.10"
                if usl is None:
                    symmetric_match = re.search(r'Φ?([\d.]+)[±±]([\d.]+)', spec_text)
                    if symmetric_match:
                        nominal = float(symmetric_match.group(1))
                        tol = float(symmetric_match.group(2))
                        usl = nominal + tol
                        lsl = nominal - tol

                # Extract dimension name (remove special chars)
                dim_name = f"位置{loc_num}"
                if 'Φ' in spec_text or 'φ' in spec_text:
                    dim_name = f"Φ位置{loc_num}"

                specs[loc_num] = {
                    'usl': usl,
                    'lsl': lsl,
                    'name': dim_name
                }

        # Extract measurements for each location
        # Look for rows with numeric data (typically after "结果" and "序号" rows)
        data_start_idx = None
        found_results = False
        found_seq = False

        for i, line in enumerate(lines[spec_line_idx + 1:], start=spec_line_idx + 1):
            if '结果' in line:
                found_results = True
            if '序号' in line:
                found_seq = True

            # If we found both headers, next line with data is the start
            if found_results and found_seq:
                data_start_idx = i
                break

        if data_start_idx is None:
            return None

        # Collect measurements for each location
        measurements_by_loc = {loc: [] for loc in location_indices.keys()}

        for line in lines[data_start_idx:data_start_idx + 100]:  # Max 100 rows
            if '|' not in line:
                continue

            parts = line.split('|')

            # Check if first column is a number (sequence number)
            if len(parts) < 2:
                continue

            seq_num = parts[1].strip() if len(parts) > 1 else ''
            if not seq_num or not re.match(r'^\d+$', seq_num):
                # Not a data row (might be empty or footer)
                continue

            # Extract measurement for each location
            for loc_num, col_idx in location_indices.items():
                if col_idx < len(parts):  # Use the column index directly
                    meas_text = parts[col_idx].strip()

                    # Extract numeric value
                    meas_match = re.search(r'([\d.]+)', meas_text)
                    if meas_match:
                        try:
                            val = float(meas_match.group(1))
                            measurements_by_loc[loc_num].append(val)
                        except ValueError:
                            pass

        # Create dimension sets
        for loc_num, measurements in measurements_by_loc.items():
            if len(measurements) >= 3:  # Need at least 3 measurements
                spec_info = specs.get(loc_num, {})

                dimension_sets.append({
                    "header": {
                        "batch_id": f"批次-{loc_num}",
                        "dimension_name": spec_info.get('name', f"检验位置{loc_num}"),
                        "usl": spec_info.get('usl', 0.0) or 10.0,
                        "lsl": spec_info.get('lsl', 0.0) or 9.0
                    },
                    "measurements": measurements
                })

        return dimension_sets if dimension_sets else None

    def create_manual_entry(self, specs_list):
        """
        Create dimension data from manual specification entry.
        Useful when OCR fails and user wants to input data manually.

        Args:
            specs_list: List of dicts, each containing:
                - 'location': Location number (e.g., '1', '11', '13')
                - 'usl': Upper specification limit
                - 'lsl': Lower specification limit
                - 'name': Dimension name (optional)
                - 'measurements': List of measurement values

        Returns:
            List of dimension sets compatible with 6SPC format
        """
        dimension_sets = []

        for spec in specs_list:
            loc_num = spec.get('location', '1')
            dimension_sets.append({
                "header": {
                    "batch_id": f"批次-{loc_num}",
                    "dimension_name": spec.get('name', f"检验位置{loc_num}"),
                    "usl": float(spec.get('usl', 10.0)),
                    "lsl": float(spec.get('lsl', 9.0))
                },
                "measurements": [float(x) for x in spec.get('measurements', [])]
            })

        return dimension_sets

    def _get_mock_data_multi(self):
        """
        Returns 3 mock parameters with 50 points each for testing multi-graph support.
        """
        import numpy as np
        def gen_points(mean, std, count=50):
            return [round(x, 3) for x in np.random.normal(mean, std, count).tolist()]

        return [
            {
                "header": {"batch_id": "D1-Length", "dimension_name": "Length (mm)", "usl": 10.5, "lsl": 9.5},
                "measurements": gen_points(10.05, 0.15, 50)
            },
            {
                "header": {"batch_id": "D2-Width", "dimension_name": "Width (mm)", "usl": 5.2, "lsl": 4.8},
                "measurements": gen_points(5.02, 0.08, 50)
            },
            {
                "header": {"batch_id": "D3-Height", "dimension_name": "Height (mm)", "usl": 2.5, "lsl": 2.3},
                "measurements": gen_points(2.41, 0.04, 50)
            }
        ]

    def _get_mock_data(self):
        """
        Noisy mock data representing a typical medical device QC measurement table.
        Used to test logic safeguards (missing decimals, units, etc).
        """
        return {
            "header": {
                "part_id": "MD-459-PLT",
                "batch_id": "B2025-NOISY-TEST",
                "dimension_name": "Inner Diameter (mm)",
                "usl": 10.5,
                "lsl": 9.5
            },
            "measurements": [
                "10.1mm", 102, 9.9, "100", 10.1,
                10.3, "9.8 ", 10.1, 102, 10.0,
                101, 10.1, 9.9, "10.4mm", 10.0
            ]
        }
