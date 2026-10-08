from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz


# ============================================================
# Configuration
# ============================================================

DEFAULT_Y_TOLERANCE = 4.0
DEFAULT_X_GAP = 12.0

MIN_TABLE_ROWS = 2
MIN_TABLE_COLUMNS = 2


# ============================================================
# Generic helpers
# ============================================================


def clean_cell(value: Any) -> str:
    """
    Normalize a table cell without aggressively modifying
    insurance-specific content.

    We preserve:

    - percentages
    - INR amounts
    - numbers
    - symbols
    - policy terminology
    """

    if value is None:
        return ""

    text = str(value)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    return " ".join(lines).strip()


def normalize_row(
    row: list[Any],
) -> list[str]:
    """
    Normalize all cells in a table row.
    """

    return [
        clean_cell(cell)
        for cell in row
    ]


def row_is_empty(
    row: list[str],
) -> bool:
    """
    Return True if all cells in a row are empty.
    """

    return not any(
        cell.strip()
        for cell in row
    )


def remove_empty_rows(
    rows: list[list[str]],
) -> list[list[str]]:
    """
    Remove completely empty table rows.
    """

    return [
        row
        for row in rows
        if not row_is_empty(row)
    ]


def normalize_row_length(
    rows: list[list[str]],
) -> list[list[str]]:
    """
    Ensure all rows have the same number of columns.

    This is important because PDF table extraction can sometimes
    return rows with missing trailing cells.

    This function performs only structural padding.
    It does not remove or infer semantic columns.
    """

    if not rows:
        return rows

    max_columns = max(
        len(row)
        for row in rows
    )

    normalized = []

    for row in rows:

        padded = row + [""] * (
            max_columns - len(row)
        )

        normalized.append(
            padded
        )

    return normalized


# ============================================================
# Table validation
# ============================================================


def is_valid_table(
    rows: list[list[str]],
) -> bool:
    """
    Conservative table validation.

    We don't want ordinary paragraphs to be incorrectly
    classified as tables.
    """

    if len(rows) < MIN_TABLE_ROWS:
        return False

    column_count = max(
        (
            len(row)
            for row in rows
        ),
        default=0,
    )

    if column_count < MIN_TABLE_COLUMNS:
        return False

    non_empty_cells = sum(
        1
        for row in rows
        for cell in row
        if cell.strip()
    )

    if non_empty_cells < 4:
        return False

    return True


# ============================================================
# Header handling
# ============================================================


def make_headers(
    rows: list[list[str]],
) -> tuple[list[str], list[list[str]]]:
    """
    Convert the first physical row into headers.

    IMPORTANT:

    This function is intentionally conservative.

    It does NOT attempt to understand:

    - multi-level headers
    - merged cells
    - insurance plan columns
    - nested tables
    - continuation tables

    Those responsibilities belong to:

        table_classifier.py
        table_normalizer.py

    If the first row contains at least two meaningful values,
    it is treated as the physical header row.

    Otherwise generic column names are generated.
    """

    if not rows:
        return [], []

    first_row = rows[0]

    meaningful_headers = sum(
        bool(cell.strip())
        for cell in first_row
    )

    if meaningful_headers >= 2:

        headers = []

        for index, cell in enumerate(
            first_row
        ):

            header = cell.strip()

            if not header:
                header = (
                    f"column_{index + 1}"
                )

            headers.append(
                header
            )

        return (
            headers,
            rows[1:],
        )

    column_count = len(
        first_row
    )

    headers = [
        f"column_{index + 1}"
        for index in range(
            column_count
        )
    ]

    return (
        headers,
        rows,
    )


# ============================================================
# Convert rows into structured records
# ============================================================


def rows_to_records(
    headers: list[str],
    rows: list[list[str]],
) -> list[dict[str, str]]:
    """
    Convert table rows into dictionaries.

    This creates a basic structural representation.

    Semantic insurance normalization is intentionally handled
    later by table_normalizer.py.
    """

    records = []

    for row in rows:

        record = {}

        for index, header in enumerate(
            headers
        ):

            value = (
                row[index]
                if index < len(row)
                else ""
            )

            record[header] = value

        # Ignore completely empty records.
        if any(
            value.strip()
            for value in record.values()
        ):
            records.append(
                record
            )

    return records


# ============================================================
# Table → retrieval-friendly text
# ============================================================


def table_to_text(
    title: str,
    headers: list[str],
    records: list[dict[str, str]],
) -> str:
    """
    Convert structured table data into retrieval-friendly text.

    This creates a basic key/value representation.

    Complex semantic relationships are handled later by
    table_normalizer.py.
    """

    parts = []

    if title:

        parts.append(
            f"Table: {title}"
        )

    for record in records:

        row_parts = []

        for header, value in record.items():

            if not value:
                continue

            row_parts.append(
                f"{header}: {value}"
            )

        if row_parts:

            parts.append(
                ". ".join(
                    row_parts
                ) + "."
            )

    return "\n".join(
        parts
    ).strip()


# ============================================================
# Native PyMuPDF table extraction
# ============================================================


def extract_tables_native(
    page: fitz.Page,
) -> list[dict[str, Any]]:
    """
    Extract tables using PyMuPDF native table detection.

    IMPORTANT:

    This function performs only SAFE structural normalization.

    It does NOT:

        - merge semantic headers
        - remove physical columns
        - merge continuation rows
        - infer insurance plan structures
        - infer table families

    Those operations belong to:

        table_classifier.py
        table_normalizer.py

    The cleaned physical rows are preserved in ``raw_rows``.
    """

    if not hasattr(
        page,
        "find_tables",
    ):
        return []

    try:

        finder = page.find_tables()

    except Exception:

        return []

    tables = getattr(
        finder,
        "tables",
        [],
    )

    extracted_tables = []

    for table_index, table in enumerate(
        tables,
        start=1,
    ):

        try:

            raw_rows = table.extract()

        except Exception:

            continue

        if not raw_rows:
            continue

        # ----------------------------------------------------
        # SAFE STRUCTURAL NORMALIZATION
        # ----------------------------------------------------
        #
        # We only:
        #
        #   1. Clean cell values
        #   2. Remove completely empty rows
        #   3. Pad rows to the same physical width
        #
        # We intentionally DO NOT:
        #
        #   - merge multi-level headers
        #   - remove spacer columns
        #   - merge continuation rows
        #   - infer plan columns
        #
        # Those operations are table-family specific.
        # ----------------------------------------------------

        rows = [
            normalize_row(row)
            for row in raw_rows
        ]

        rows = remove_empty_rows(
            rows
        )

        rows = normalize_row_length(
            rows
        )

        if not is_valid_table(
            rows
        ):
            continue

        # ----------------------------------------------------
        # Basic physical header representation.
        # ----------------------------------------------------

        headers, data_rows = make_headers(
            rows
        )

        records = rows_to_records(
            headers,
            data_rows,
        )

        if not records:
            continue

        bbox = getattr(
            table,
            "bbox",
            None,
        )

        if bbox is not None:
            bbox = list(bbox)

        extracted_tables.append(
            {
                "table_index": table_index,

                "bbox": bbox,

                # Basic structural representation.
                "headers": headers,
                "rows": data_rows,
                "records": records,

                # IMPORTANT:
                # Preserve the complete cleaned physical
                # table structure for downstream normalization.
                "raw_rows": rows,

                "extraction_method": "pymupdf",
            }
        )

    return extracted_tables


# ============================================================
# Fallback: word-coordinate table reconstruction
# ============================================================


def get_page_words(
    page: fitz.Page,
) -> list[dict[str, Any]]:
    """
    Extract words with their coordinates.

    PyMuPDF returns approximately:

        x0, y0, x1, y1, word, block_no, line_no, word_no
    """

    words = page.get_text(
        "words"
    )

    result = []

    for item in words:

        if len(item) < 5:
            continue

        x0, y0, x1, y1, text = item[:5]

        text = str(text).strip()

        if not text:
            continue

        result.append(
            {
                "text": text,
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
            }
        )

    return result


def group_words_into_lines(
    words: list[dict[str, Any]],
    y_tolerance: float = DEFAULT_Y_TOLERANCE,
) -> list[list[dict[str, Any]]]:
    """
    Group words using their vertical positions.

    This is a fallback only. Native table detection is preferred.
    """

    sorted_words = sorted(
        words,
        key=lambda word: (
            word["y0"],
            word["x0"],
        ),
    )

    lines: list[
        list[dict[str, Any]]
    ] = []

    for word in sorted_words:

        placed = False

        for line in lines:

            reference_y = (
                line[0]["y0"]
            )

            if abs(
                word["y0"]
                - reference_y
            ) <= y_tolerance:

                line.append(
                    word
                )

                placed = True

                break

        if not placed:

            lines.append(
                [word]
            )

    for line in lines:

        line.sort(
            key=lambda word: word["x0"]
        )

    return lines


def line_to_cells(
    line: list[dict[str, Any]],
    x_gap: float = DEFAULT_X_GAP,
) -> list[str]:
    """
    Convert a line of words into approximate cells.

    A large horizontal gap is treated as a column boundary.
    """

    if not line:
        return []

    cells = []

    current_words = [
        line[0]["text"]
    ]

    previous_x1 = (
        line[0]["x1"]
    )

    for word in line[1:]:

        gap = (
            word["x0"]
            - previous_x1
        )

        if gap >= x_gap:

            cells.append(
                " ".join(
                    current_words
                )
            )

            current_words = [
                word["text"]
            ]

        else:

            current_words.append(
                word["text"]
            )

        previous_x1 = word["x1"]

    cells.append(
        " ".join(
            current_words
        )
    )

    return [
        clean_cell(cell)
        for cell in cells
    ]


def detect_fallback_table(
    page: fitz.Page,
) -> list[dict[str, Any]]:
    """
    Approximate table detection using word coordinates.

    This is intentionally conservative because normal policy
    paragraphs can also contain multiple visual gaps.

    Semantic normalization is NOT performed here.
    """

    words = get_page_words(
        page
    )

    if not words:
        return []

    lines = group_words_into_lines(
        words
    )

    candidate_rows = []

    for line in lines:

        cells = line_to_cells(
            line
        )

        if len(cells) >= MIN_TABLE_COLUMNS:

            candidate_rows.append(
                cells
            )

    if len(candidate_rows) < MIN_TABLE_ROWS:
        return []

    # --------------------------------------------------------
    # Find contiguous runs of table-like rows.
    # --------------------------------------------------------

    runs: list[
        list[list[str]]
    ] = []

    current_run: list[
        list[str]
    ] = []

    for row in candidate_rows:

        if len(row) >= MIN_TABLE_COLUMNS:

            if current_run:

                previous_width = len(
                    current_run[-1]
                )

                current_width = len(
                    row
                )

                # Allow small differences caused by PDF layout.
                if abs(
                    previous_width
                    - current_width
                ) <= 1:

                    current_run.append(
                        row
                    )

                else:

                    if len(
                        current_run
                    ) >= MIN_TABLE_ROWS:

                        runs.append(
                            current_run
                        )

                    current_run = [
                        row
                    ]

            else:

                current_run = [
                    row
                ]

    if len(
        current_run
    ) >= MIN_TABLE_ROWS:

        runs.append(
            current_run
        )

    tables = []

    for table_index, rows in enumerate(
        runs,
        start=1,
    ):

        rows = normalize_row_length(
            rows
        )

        if not is_valid_table(
            rows
        ):
            continue

        headers, data_rows = make_headers(
            rows
        )

        records = rows_to_records(
            headers,
            data_rows,
        )

        if not records:
            continue

        tables.append(
            {
                "table_index": table_index,

                "bbox": None,

                "headers": headers,
                "rows": data_rows,
                "records": records,

                # Preserve physical rows for downstream
                # semantic normalization.
                "raw_rows": rows,

                "extraction_method": (
                    "coordinate_fallback"
                ),
            }
        )

    return tables


# ============================================================
# Deduplication
# ============================================================


def table_signature(
    table: dict[str, Any],
) -> tuple:
    """
    Generate a lightweight signature for deduplicating tables
    detected by multiple methods.
    """

    headers = tuple(
        table.get(
            "headers",
            [],
        )
    )

    first_rows = tuple(
        tuple(row)
        for row in table.get(
            "rows",
            [],
        )[:3]
    )

    return (
        headers,
        first_rows,
    )


def deduplicate_tables(
    tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Remove duplicate table structures.
    """

    seen = set()

    unique = []

    for table in tables:

        signature = table_signature(
            table
        )

        if signature in seen:
            continue

        seen.add(
            signature
        )

        unique.append(
            table
        )

    return unique


# ============================================================
# Main extraction
# ============================================================


def extract_tables(
    pdf_path: Path,
) -> dict[str, Any]:
    """
    Extract structured/raw tables from the PDF.

    Strategy:

        1. Open PDF using PyMuPDF.
        2. Attempt native table extraction.
        3. Fall back to coordinate-based reconstruction.
        4. Perform only safe structural normalization.
        5. Preserve raw physical rows.
        6. Preserve page numbers and bounding boxes.
        7. Generate retrieval-friendly structural text.
        8. Deduplicate tables.

    IMPORTANT:

    This function does NOT perform insurance-specific semantic
    normalization.

    Semantic interpretation belongs to:

        table_classifier.py
        table_normalizer.py

    Returns:

        {
            "document": {...},
            "table_count": int,
            "tables": [...]
        }
    """

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    document = fitz.open(
        pdf_path
    )

    page_count = len(
        document
    )

    tables = []

    try:

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            page_tables = extract_tables_native(
                page
            )

            extraction_method = (
                "pymupdf"
            )

            # ------------------------------------------------
            # Fallback only when native extraction finds
            # nothing.
            # ------------------------------------------------

            if not page_tables:

                page_tables = detect_fallback_table(
                    page
                )

                extraction_method = (
                    "coordinate_fallback"
                )

            for table in page_tables:

                table["page_number"] = (
                    page_number
                )

                table["table_id"] = (
                    f"table_page_"
                    f"{page_number}_"
                    f"{table['table_index']}"
                )

                # ------------------------------------------------
                # Structural retrieval text.
                #
                # This is intentionally based on the physical
                # table representation.
                # ------------------------------------------------

                table["text"] = table_to_text(
                    title="",
                    headers=table["headers"],
                    records=table["records"],
                )

                table["source"] = {
                    "filename": pdf_path.name,
                    "page_number": page_number,
                }

                # Preserve the method actually used.
                table[
                    "extraction_method"
                ] = extraction_method

                tables.append(
                    table
                )

    finally:

        document.close()

    # --------------------------------------------------------
    # Remove duplicate physical tables.
    # --------------------------------------------------------

    tables = deduplicate_tables(
        tables
    )

    # --------------------------------------------------------
    # Re-number IDs after deduplication.
    # --------------------------------------------------------

    for index, table in enumerate(
        tables,
        start=1,
    ):

        table["global_table_index"] = (
            index
        )

        table["table_id"] = (
            f"table_{index:05d}"
        )

    return {
        "document": {
            "filename": pdf_path.name,
            "page_count": page_count,
        },
        "table_count": len(tables),
        "tables": tables,
    }


# ============================================================
# Validation
# ============================================================


def validate_tables(
    table_data: dict[str, Any],
) -> list[str]:
    """
    Validate extracted table structure.

    This intentionally checks structure rather than judging
    whether every value is semantically correct.
    """

    errors = []

    if "tables" not in table_data:

        errors.append(
            "Missing 'tables' field."
        )

        return errors

    tables = table_data[
        "tables"
    ]

    if not isinstance(
        tables,
        list,
    ):

        errors.append(
            "'tables' must be a list."
        )

        return errors

    table_ids = set()

    for table in tables:

        table_id = table.get(
            "table_id"
        )

        if not table_id:

            errors.append(
                "Table missing table_id."
            )

        elif table_id in table_ids:

            errors.append(
                f"Duplicate table_id: "
                f"{table_id}"
            )

        else:

            table_ids.add(
                table_id
            )

        page_number = table.get(
            "page_number"
        )

        if (
            not isinstance(
                page_number,
                int,
            )
            or page_number <= 0
        ):

            errors.append(
                f"Invalid page number for "
                f"{table_id}."
            )

        headers = table.get(
            "headers"
        )

        rows = table.get(
            "rows"
        )

        records = table.get(
            "records"
        )

        if (
            not isinstance(
                headers,
                list,
            )
            or not headers
        ):

            errors.append(
                f"Missing headers for "
                f"{table_id}."
            )

        if not isinstance(
            rows,
            list,
        ):

            errors.append(
                f"Invalid rows for "
                f"{table_id}."
            )

        if not isinstance(
            records,
            list,
        ):

            errors.append(
                f"Invalid records for "
                f"{table_id}."
            )

        # ----------------------------------------------------
        # Validate physical row/header alignment.
        #
        # This checks the structural extraction only.
        # Semantic normalization happens later.
        # ----------------------------------------------------

        if (
            isinstance(
                headers,
                list,
            )
            and isinstance(
                rows,
                list,
            )
        ):

            header_count = len(
                headers
            )

            for row_index, row in enumerate(
                rows
            ):

                if len(row) != header_count:

                    errors.append(
                        f"{table_id}: row "
                        f"{row_index} has "
                        f"{len(row)} columns; "
                        f"expected "
                        f"{header_count}."
                    )

    return errors