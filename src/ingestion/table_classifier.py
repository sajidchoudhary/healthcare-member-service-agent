from collections import Counter
from typing import Any


# ---------------------------------------------------------------------------
# Table family constants
# ---------------------------------------------------------------------------

TABLE_FAMILY_PLAN_COMPARISON = "plan_comparison"

TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION = (
    "plan_comparison_continuation"
)

TABLE_FAMILY_MEDICAL_SUB_LIMIT = "medical_sub_limit"

TABLE_FAMILY_SIMPLE_CIS = "simple_cis"

TABLE_FAMILY_GENERIC = "generic"


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def normalize_text(value: Any) -> str:
    """
    Convert a value to normalized lowercase text.
    """
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def table_text(table: dict[str, Any]) -> str:
    """
    Combine headers and rows into one searchable text representation.
    """
    parts: list[str] = []

    for header in table.get("headers", []):
        parts.append(normalize_text(header))

    for row in table.get("rows", []):
        for cell in row:
            parts.append(normalize_text(cell))

    return " ".join(part for part in parts if part)


def contains_any(text: str, terms: list[str]) -> bool:
    """
    Return True if any term is present in the supplied text.
    """
    return any(term in text for term in terms)


# ---------------------------------------------------------------------------
# Known insurance terminology
# ---------------------------------------------------------------------------

PLAN_NAMES = [
    "secure basic",
    "secure elite",
    "secure supreme",
    "secure complete",
]

PLAN_COMPARISON_TERMS = [
    "policy plans",
    "sum insured",
    "in-patient hospitalization",
    "pre-hospitalization",
    "post-hospitalization",
    "day care",
    "optional covers",
]


MEDICAL_SUB_LIMIT_TERMS = [
    "cataract",
    "hysterectomy",
    "ptca",
    "cabg",
    "angioplasty",
    "bypass surgery",
    "medical expense",
    "medical expenses",
    "sub limit",
    "sub-limit",
]


SIMPLE_CIS_TERMS = [
    "sr no",
    "sr. no",
    "serial no",
    "title",
    "description",
    "reference",
]


# ---------------------------------------------------------------------------
# Basic structural helpers
# ---------------------------------------------------------------------------


def has_serial_number(table: dict[str, Any]) -> bool:
    """
    Check whether the table contains a serial-number style column/header.
    """
    headers = [
        normalize_text(header)
        for header in table.get("headers", [])
    ]

    serial_terms = [
        "sr no",
        "sr. no",
        "serial no",
        "s no",
        "s. no",
    ]

    return any(
        any(term in header for term in serial_terms)
        for header in headers
    )


def count_plan_names(table: dict[str, Any]) -> int:
    """
    Count distinct Secure Health Connect plan names present in the table.
    """
    text = table_text(table)

    return sum(
        1
        for plan_name in PLAN_NAMES
        if plan_name in text
    )


# ---------------------------------------------------------------------------
# Medical sub-limit detection
# ---------------------------------------------------------------------------


def is_medical_sub_limit_table(table: dict[str, Any]) -> bool:
    """
    Identify medical expense sub-limit tables.

    Detection is based on insurance-specific treatment/procedure terms,
    rather than the presence of Secure plan names.

    This is important because medical sub-limit tables also contain:
        Secure Basic
        Secure Elite
        Secure Supreme
        Secure Complete
    """
    text = table_text(table)

    matched_terms = [
        term
        for term in MEDICAL_SUB_LIMIT_TERMS
        if term in text
    ]

    # Strong signal:
    # At least two known medical procedures/expense terms.
    if len(matched_terms) >= 2:
        return True

    # A single strong structural term such as "medical expense" +
    # multiple plan columns is also sufficient.
    if (
        any(
            term in text
            for term in [
                "medical expense",
                "medical expenses",
                "sub limit",
                "sub-limit",
            ]
        )
        and count_plan_names(table) >= 2
    ):
        return True

    return False


# ---------------------------------------------------------------------------
# Continuation detection
# ---------------------------------------------------------------------------


def looks_like_continuation(table: dict[str, Any]) -> bool:
    """
    Detect a physical table fragment that looks like a continuation
    of a previous plan-comparison table.

    A continuation generally:
      - does not have a serial number column
      - contains multiple Secure plan names
      - does not contain strong NEW table headers
      - does not contain medical sub-limit terminology
      - contains meaningful rows

    Important:
    "Sum Insured" may legitimately occur inside a benefit value such as:

        1% of Sum Insured or maximum up to INR 3000/day

    Therefore, we only inspect the HEADERS when checking whether
    "Sum Insured" represents a new plan-comparison header.
    """

    if has_serial_number(table):
        return False

    # Medical sub-limit tables must never be treated as
    # plan-comparison continuations.
    if is_medical_sub_limit_table(table):
        return False

    headers = [
        normalize_text(header)
        for header in table.get("headers", [])
    ]

    header_text = " ".join(
        header for header in headers if header
    )

    plan_count = count_plan_names(table)

    if plan_count < 2:
        return False

    # These indicate that the current physical table is probably
    # the beginning of a new comparison table rather than a continuation.
    strong_new_table_headers = [
        "policy plans",
        "sum insured",
        "plan",
        "benefit",
        "coverage",
        "cover",
    ]

    if any(
        term in header_text
        for term in strong_new_table_headers
    ):
        return False

    rows = table.get("rows", [])

    meaningful_rows = 0

    for row in rows:
        meaningful_cells = [
            normalize_text(cell)
            for cell in row
            if normalize_text(cell)
        ]

        if len(meaningful_cells) >= 2:
            meaningful_rows += 1

    return meaningful_rows >= 1

# ---------------------------------------------------------------------------
# Plan comparison detection
# ---------------------------------------------------------------------------


def is_plan_comparison_table(table: dict[str, Any]) -> bool:
    """
    Identify the main Secure Health Connect plan comparison table.

    Important:
    Medical sub-limit tables also contain the four Secure plan names,
    therefore plan names alone are NOT sufficient.
    """
    # Highest-priority exclusion.
    if is_medical_sub_limit_table(table):
        return False

    text = table_text(table)

    plan_count = count_plan_names(table)

    if plan_count < 2:
        return False

    # Strong structural indicators of the actual comparison table.
    comparison_term_count = sum(
        1
        for term in PLAN_COMPARISON_TERMS
        if term in text
    )

    if comparison_term_count >= 2:
        return True

    # "Policy Plans" + multiple plan names is a very strong signal.
    if "policy plans" in text and plan_count >= 2:
        return True

    return False


# ---------------------------------------------------------------------------
# Simple CIS detection
# ---------------------------------------------------------------------------


def is_simple_cis_table(table: dict[str, Any]) -> bool:
    """
    Identify simple Customer Information Sheet tables.
    """
    headers = [
        normalize_text(header)
        for header in table.get("headers", [])
    ]

    matched = 0

    for term in SIMPLE_CIS_TERMS:
        if any(term in header for header in headers):
            matched += 1

    return matched >= 2


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------


def classify_table(table: dict[str, Any]) -> str:
    """
    Classify one extracted physical table.

    Order is intentional:

        1. Medical sub-limit
        2. Continuation
        3. Main plan comparison
        4. Simple CIS
        5. Generic
    """

    # Medical sub-limit must come first because it also contains
    # Secure Basic / Elite / Supreme / Complete.
    if is_medical_sub_limit_table(table):
        return TABLE_FAMILY_MEDICAL_SUB_LIMIT

    # Continuation fragments can contain Secure plan names.
    if looks_like_continuation(table):
        return TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION

    if is_plan_comparison_table(table):
        return TABLE_FAMILY_PLAN_COMPARISON

    if is_simple_cis_table(table):
        return TABLE_FAMILY_SIMPLE_CIS

    return TABLE_FAMILY_GENERIC


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------


def classify_tables(
    tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add table_family to every extracted table.

    Original table information is preserved.
    """
    classified_tables: list[dict[str, Any]] = []

    for table in tables:
        classified_table = dict(table)

        classified_table["table_family"] = classify_table(table)

        classified_tables.append(classified_table)

    return classified_tables


# ---------------------------------------------------------------------------
# Classification summary
# ---------------------------------------------------------------------------


def get_classification_summary(
    tables: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Return counts of each classified table family.
    """
    counter = Counter(
        table.get("table_family", TABLE_FAMILY_GENERIC)
        for table in tables
    )

    return dict(counter)