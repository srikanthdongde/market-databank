import csv
import io
import os
from django.core.exceptions import ValidationError

MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024  # 10 Megabytes


def validate_csv_file(uploaded_file):
    """
    Validates uploaded CSV file:
    1. Checks filename extension.
    2. Validates file size (limit 10MB).
    3. Reads and decodes byte stream using UTF-8/UTF-8-SIG/Latin-1.
    4. Uses standard library `csv.reader` to verify tabular structure.
    5. Ensures file contains at least headers and one data row.

    Returns:
        tuple: (is_valid: bool, error_message: str or None, metadata: dict)
    """
    # 1. Extension check
    filename = uploaded_file.name
    if not filename.lower().endswith('.csv'):
        return False, "Invalid file format. Only standard comma-separated (.csv) files are permitted.", {}

    # 2. File size check
    if uploaded_file.size > MAX_CSV_SIZE_BYTES:
        size_mb = uploaded_file.size / (1024 * 1024)
        return False, f"File size ({size_mb:.1f} MB) exceeds the maximum allowed limit of 10 MB.", {}

    if uploaded_file.size == 0:
        return False, "The uploaded file is empty.", {}

    # 3. Read and decode content safely
    try:
        raw_bytes = uploaded_file.read()
        uploaded_file.seek(0)  # Reset pointer for subsequent save
    except Exception as e:
        return False, f"Failed to read file: {str(e)}", {}

    # Attempt decodings
    text_content = None
    used_encoding = None
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            text_content = raw_bytes.decode(enc)
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    if text_content is None:
        return False, "File encoding is not supported. Please save your file in UTF-8 format.", {}

    # 4. Parse CSV structure
    try:
        string_io = io.StringIO(text_content)
        # Attempt dialect sniffing
        sample = text_content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ','

        string_io.seek(0)
        reader = csv.reader(string_io, delimiter=delimiter)
        
        headers = None
        data_row_count = 0
        column_count = 0

        for row_idx, row in enumerate(reader):
            # Clean and strip fields
            cleaned_row = [field.strip() for field in row]
            if not any(cleaned_row):
                # Skip empty lines
                continue

            if headers is None:
                headers = cleaned_row
                column_count = len(headers)
            else:
                data_row_count += 1

        if not headers or len(headers) == 0:
            return False, "The CSV file does not contain a valid header row.", {}

        if data_row_count == 0:
            return False, "The CSV file contains column headers but has no data rows.", {}

        metadata = {
            'file_size': uploaded_file.size,
            'row_count': data_row_count,
            'column_count': column_count,
            'column_names': ', '.join(headers[:30]),  # store up to 30 headers
            'encoding': used_encoding,
            'delimiter': delimiter,
        }
        return True, None, metadata

    except Exception as e:
        return False, f"Error parsing CSV structure: {str(e)}", {}


def get_csv_preview(file_field, max_rows=20):
    """
    Reads the dataset file and extracts headers and first `max_rows` rows for display.
    Also extracts simple column stats for market visualization.
    """
    if not file_field or not os.path.exists(file_field.path):
        return {
            'headers': [],
            'rows': [],
            'total_preview_rows': 0,
            'numeric_columns': [],
            'chart_labels': [],
            'chart_values': [],
            'chart_column_name': '',
        }

    try:
        # Determine encoding and read
        raw_bytes = open(file_field.path, 'rb').read()
        text_content = None
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                text_content = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if not text_content:
            return {'headers': [], 'rows': [], 'total_preview_rows': 0}

        sample = text_content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ','

        string_io = io.StringIO(text_content)
        reader = csv.reader(string_io, delimiter=delimiter)

        headers = []
        rows = []
        all_parsed_rows = []

        for row_idx, row in enumerate(reader):
            cleaned = [c.strip() for c in row]
            if not any(cleaned):
                continue

            if not headers:
                headers = cleaned
            else:
                all_parsed_rows.append(cleaned)
                if len(rows) < max_rows:
                    rows.append(cleaned)

        # Detect a candidate numeric column for an authentic trend/sample preview chart
        numeric_col_idx = -1
        numeric_col_name = ''
        chart_labels = []
        chart_values = []

        if headers and all_parsed_rows:
            # Check headers for typical market metrics (Price, Close, High, Value, Volume, Rate, Yield)
            candidate_indices = []
            for col_idx, col_name in enumerate(headers):
                lower_name = col_name.lower()
                if any(term in lower_name for term in ['price', 'close', 'rate', 'value', 'index', 'yield', 'amount', 'profit', 'sales']):
                    candidate_indices.append(col_idx)

            if not candidate_indices:
                # Fallback to any column that parses as float
                for col_idx in range(len(headers)):
                    candidate_indices.append(col_idx)

            for c_idx in candidate_indices:
                parsed_vals = []
                for r in all_parsed_rows[:15]:
                    if c_idx < len(r):
                        val_str = r[c_idx].replace('$', '').replace('€', '').replace(',', '').strip()
                        try:
                            parsed_vals.append(float(val_str))
                        except ValueError:
                            parsed_vals = []
                            break
                if parsed_vals:
                    numeric_col_idx = c_idx
                    numeric_col_name = headers[c_idx]
                    chart_values = parsed_vals
                    # Try using first column as labels if string/date
                    label_idx = 0 if numeric_col_idx != 0 else 1
                    chart_labels = [
                        (r[label_idx] if label_idx < len(r) and r[label_idx] else f"Row {i+1}")
                        for i, r in enumerate(all_parsed_rows[:len(chart_values)])
                    ]
                    break

        return {
            'headers': headers,
            'rows': rows,
            'total_preview_rows': len(rows),
            'chart_column_name': numeric_col_name,
            'chart_labels': chart_labels,
            'chart_values': chart_values,
        }

    except Exception:
        return {
            'headers': [],
            'rows': [],
            'total_preview_rows': 0,
            'chart_column_name': '',
            'chart_labels': [],
            'chart_values': [],
        }
