from __future__ import annotations

from typing import Any

from src.ingestion.table_classifier import (
    TABLE_FAMILY_GENERIC,
    TABLE_FAMILY_MEDICAL_SUB_LIMIT,
    TABLE_FAMILY_PLAN_COMPARISON,
    TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION,
    TABLE_FAMILY_SIMPLE_CIS,
    normalize_text,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLAN_KEY_MAP = {
    "secure basic": "secure_basic",
    "secure elite": "secure_elite",
    "secure supreme": "secure_supreme",
    "secure complete": "secure_complete",
}


PLAN_DISPLAY_NAMES = {
    "secure_basic": "Secure Basic",
    "secure_elite": "Secure Elite",
    "secure_supreme": "Secure Supreme",
    "secure_complete": "Secure Complete",
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def clean_value(value: Any) -> str:
    """
    Normalize a cell value while preserving its meaning.
    """
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def non_empty_values(row: list[Any]) -> list[str]:
    """
    Return non-empty cell values from a row.
    """
    return [
        clean_value(value)
        for value in row
        if clean_value(value)
    ]


def find_plan_key(value: Any) -> str | None:
    """
    Convert a plan name into the canonical plan key.
    """
    normalized = normalize_text(value)

    for plan_name, plan_key in PLAN_KEY_MAP.items():
        if normalized == plan_name:
            return plan_key

    return None


def find_plan_columns(
    headers: list[Any],
) -> dict[str, int]:
    """
    Find Secure plan columns from the extracted table headers.

    Returns:
        {
            "secure_basic": 1,
            "secure_elite": 2,
            ...
        }
    """
    plan_columns: dict[str, int] = {}

    for index, header in enumerate(headers):
        plan_key = find_plan_key(header)

        if plan_key:
            plan_columns[plan_key] = index

    return plan_columns


def get_cell(
    row: list[Any],
    index: int,
) -> str:
    """
    Safely retrieve a cell from a row.
    """
    if index < 0 or index >= len(row):
        return ""

    return clean_value(row[index])


# ---------------------------------------------------------------------------
# Plan comparison normalization
# ---------------------------------------------------------------------------


def normalize_plan_comparison(
    table: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize the main Secure Health Connect plan-comparison table.

    The physical extraction can contain spacer columns and complex
    multi-level headers. This function creates a semantic representation
    without changing the original extracted rows.

    Output shape:

        {
            "table_type": "plan_comparison",
            "plan_columns": {
                "secure_basic": {
                    "header": "Secure Basic",
                    "sum_insured": [...],
                    "benefits": {...}
                },
                ...
            },
            "rows": [...]
        }
    """

    headers = table.get("headers", [])
    rows = table.get("rows", [])

    plan_columns = find_plan_columns(headers)

    normalized_plans: dict[str, dict[str, Any]] = {}

    for plan_key, column_index in plan_columns.items():
        normalized_plans[plan_key] = {
            "header": PLAN_DISPLAY_NAMES[plan_key],
            "sum_insured": [],
            "benefits": {},
        }

    semantic_rows: list[dict[str, Any]] = []

    for row in rows:
        if not row:
            continue

        # The first meaningful cell normally represents the benefit /
        # coverage name.
        label = clean_value(row[0]) if len(row) > 0 else ""

        if not label:
            continue

        row_data: dict[str, Any] = {
            "label": label,
            "values": {},
        }

        for plan_key, column_index in plan_columns.items():
            value = get_cell(row, column_index)

            if value:
                row_data["values"][plan_key] = value

                normalized_label = normalize_text(label)

                # Capture Sum Insured separately.
                if "sum insured" in normalized_label:
                    if value not in normalized_plans[plan_key]["sum_insured"]:
                        normalized_plans[plan_key]["sum_insured"].append(
                            value
                        )

                else:
                    normalized_plans[plan_key]["benefits"][
                        label
                    ] = value

        if row_data["values"]:
            semantic_rows.append(row_data)

    return {
        "table_type": TABLE_FAMILY_PLAN_COMPARISON,
        "plan_columns": normalized_plans,
        "rows": semantic_rows,
    }


# ---------------------------------------------------------------------------
# Plan comparison continuation normalization
# ---------------------------------------------------------------------------


def normalize_plan_comparison_continuation(
    table: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize a physical continuation fragment.

    Continuation fragments do not have enough information to reconstruct
    the complete semantic table independently.

    Therefore this function preserves:
      - detected plan columns
      - extracted rows
      - raw positional values

    It does NOT guess missing labels or inherit data from another table.
    """

    headers = table.get("headers", [])
    rows = table.get("rows", [])

    plan_columns = find_plan_columns(headers)

    normalized_rows: list[dict[str, Any]] = []

    for row in rows:
        values: dict[str, str] = {}

        for plan_key, column_index in plan_columns.items():
            value = get_cell(row, column_index)

            if value:
                values[plan_key] = value

        if values:
            normalized_rows.append(
                {
                    "values": values,
                }
            )

    return {
        "table_type": TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION,
        "plan_columns": {
            plan_key: {
                "header": PLAN_DISPLAY_NAMES[plan_key],
            }
            for plan_key in plan_columns
        },
        "rows": normalized_rows,
    }


# ---------------------------------------------------------------------------
# Medical sub-limit normalization
# ---------------------------------------------------------------------------


def normalize_medical_sub_limit(
    table: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize the medical expense sub-limit table.

    Example semantic output:

        {
            "treatment": "Cataract",
            "limits": {
                "secure_basic": "20,000",
                "secure_elite": "30,000",
                ...
            }
        }
    """

    headers = table.get("headers", [])
    rows = table.get("rows", [])

    plan_columns = find_plan_columns(headers)

    normalized_rows: list[dict[str, Any]] = []

    for row in rows:
        if not row:
            continue

        treatment = clean_value(row[0])

        if not treatment:
            continue

        limits: dict[str, str] = {}

        for plan_key, column_index in plan_columns.items():
            value = get_cell(row, column_index)

            if value:
                limits[plan_key] = value

        if limits:
            normalized_rows.append(
                {
                    "treatment": treatment,
                    "limits": limits,
                }
            )

    return {
        "table_type": TABLE_FAMILY_MEDICAL_SUB_LIMIT,
        "plan_columns": {
            plan_key: {
                "header": PLAN_DISPLAY_NAMES[plan_key],
            }
            for plan_key in plan_columns
        },
        "rows": normalized_rows,
    }


# ---------------------------------------------------------------------------
# Simple CIS normalization
# ---------------------------------------------------------------------------


def normalize_simple_cis(
    table: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize a simple Customer Information Sheet table.

    The original column headers are retained rather than assuming
    a fixed schema.
    """

    headers = [
        clean_value(header)
        for header in table.get("headers", [])
    ]

    rows = table.get("rows", [])

    normalized_rows: list[dict[str, str]] = []

    for row in rows:
        record: dict[str, str] = {}

        for index, header in enumerate(headers):
            if not header:
                continue

            record[header] = get_cell(row, index)

        if any(record.values()):
            normalized_rows.append(record)

    return {
        "table_type": TABLE_FAMILY_SIMPLE_CIS,
        "headers": headers,
        "rows": normalized_rows,
    }


# ---------------------------------------------------------------------------
# Generic normalization
# ---------------------------------------------------------------------------


def normalize_generic(
    table: dict[str, Any],
) -> dict[str, Any]:
    """
    Conservative normalization for unknown table families.

    No semantic assumptions are made.
    """

    headers = [
        clean_value(header)
        for header in table.get("headers", [])
    ]

    rows = [
        [
            clean_value(value)
            for value in row
        ]
        for row in table.get("rows", [])
    ]

    return {
        "table_type": TABLE_FAMILY_GENERIC,
        "headers": headers,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Main normalization dispatcher
# ---------------------------------------------------------------------------


def normalize_table(
    table: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize one classified physical table.

    The original table object is copied and preserved.
    Semantic information is added under:

        table["normalized"]
    """

    result = dict(table)

    table_family = table.get(
        "table_family",
        TABLE_FAMILY_GENERIC,
    )

    if table_family == TABLE_FAMILY_PLAN_COMPARISON:
        normalized = normalize_plan_comparison(table)

    elif table_family == TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION:
        normalized = normalize_plan_comparison_continuation(table)

    elif table_family == TABLE_FAMILY_MEDICAL_SUB_LIMIT:
        normalized = normalize_medical_sub_limit(table)

    elif table_family == TABLE_FAMILY_SIMPLE_CIS:
        normalized = normalize_simple_cis(table)

    else:
        normalized = normalize_generic(table)

    result["normalized"] = normalized

    return result


# ---------------------------------------------------------------------------
# Batch normalization
# ---------------------------------------------------------------------------


def normalize_tables(
    tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Normalize all classified tables.
    """
    return [
        normalize_table(table)
        for table in tables
    ]