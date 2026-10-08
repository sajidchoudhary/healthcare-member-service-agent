from src.ingestion.table_classifier import (
    TABLE_FAMILY_GENERIC,
    TABLE_FAMILY_MEDICAL_SUB_LIMIT,
    TABLE_FAMILY_PLAN_COMPARISON,
    TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION,
    TABLE_FAMILY_SIMPLE_CIS,
)

from src.ingestion.table_normalizer import (
    normalize_generic,
    normalize_medical_sub_limit,
    normalize_plan_comparison,
    normalize_plan_comparison_continuation,
    normalize_simple_cis,
    normalize_table,
    normalize_tables,
)


# ---------------------------------------------------------------------------
# Sample tables
# ---------------------------------------------------------------------------


PLAN_COMPARISON_TABLE = {
    "table_index": 1,
    "page_number": 1,
    "table_family": TABLE_FAMILY_PLAN_COMPARISON,
    "headers": [
        "Policy Plans",
        "Secure Basic",
        "Secure Elite",
        "Secure Supreme",
        "Secure Complete",
    ],
    "rows": [
        [
            "Room Rent",
            "1% of Sum Insured or maximum up to INR 3000/day, whichever is lower",
            "1% of Sum Insured or maximum up to INR 5000/day, whichever is lower",
            "1% of Sum Insured or maximum up to INR 5000/day, whichever is lower",
            "1% of Sum Insured or maximum up to INR 2500/day, whichever is lower",
        ],
        [
            "ICU",
            "2% of Sum Insured or maximum up to INR 6000/day, whichever is lower",
            "2% of Sum Insured or maximum up to INR 6000/day, whichever is lower",
            "2% of Sum Insured or maximum up to INR 7500/day, whichever is lower",
            "2% of Sum Insured or maximum up to INR 5000/day, whichever is lower",
        ],
    ],
    "raw_rows": [
        [
            "Policy Plans",
            "Secure Basic",
            "Secure Elite",
            "Secure Supreme",
            "Secure Complete",
        ]
    ],
}


MEDICAL_SUB_LIMIT_TABLE = {
    "table_index": 7,
    "page_number": 7,
    "table_family": TABLE_FAMILY_MEDICAL_SUB_LIMIT,
    "headers": [
        "Medical Expense",
        "Secure Basic",
        "Secure Elite",
        "Secure Supreme",
        "Secure Complete",
    ],
    "rows": [
        ["Cataract", "20,000", "30,000", "40,000", "40,000"],
        ["Hysterectomy", "35,000", "45,000", "55,000", "55,000"],
        ["PTCA", "80,000", "1,20,000", "1,50,000", "1,50,000"],
        ["CABG", "1,00,000", "1,50,000", "2,00,000", "2,00,000"],
    ],
}


CONTINUATION_TABLE = {
    "table_index": 8,
    "page_number": 2,
    "table_family": TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION,
    "headers": [
        "Secure Basic",
        "Secure Elite",
        "Secure Supreme",
        "Secure Complete",
    ],
    "rows": [
        [
            "Covered",
            "Covered",
            "Covered",
            "Covered",
        ],
        [
            "1% of Sum Insured",
            "1% of Sum Insured",
            "1% of Sum Insured",
            "1% of Sum Insured",
        ],
    ],
}


SIMPLE_CIS_TABLE = {
    "table_index": 2,
    "page_number": 1,
    "table_family": TABLE_FAMILY_SIMPLE_CIS,
    "headers": [
        "SR NO",
        "Title",
        "Description",
        "Reference",
    ],
    "rows": [
        [
            "1",
            "Product Name",
            "Secure Health Connect",
            "Policy",
        ],
        [
            "2",
            "Coverage",
            "Health Insurance",
            "Policy",
        ],
    ],
}


GENERIC_TABLE = {
    "table_index": 20,
    "page_number": 20,
    "table_family": TABLE_FAMILY_GENERIC,
    "headers": [
        "Item",
        "Description",
    ],
    "rows": [
        [
            "Example",
            "Example description",
        ],
        [
            "Another",
            "Another description",
        ],
    ],
}


# ---------------------------------------------------------------------------
# Plan comparison tests
# ---------------------------------------------------------------------------


def test_normalize_plan_comparison():
    result = normalize_plan_comparison(PLAN_COMPARISON_TABLE)

    assert result["table_type"] == TABLE_FAMILY_PLAN_COMPARISON

    assert "plan_columns" in result

    assert "secure_basic" in result["plan_columns"]
    assert "secure_elite" in result["plan_columns"]
    assert "secure_supreme" in result["plan_columns"]
    assert "secure_complete" in result["plan_columns"]


def test_plan_comparison_headers():
    result = normalize_plan_comparison(PLAN_COMPARISON_TABLE)

    plans = result["plan_columns"]

    assert plans["secure_basic"]["header"] == "Secure Basic"
    assert plans["secure_elite"]["header"] == "Secure Elite"
    assert plans["secure_supreme"]["header"] == "Secure Supreme"
    assert plans["secure_complete"]["header"] == "Secure Complete"


def test_plan_comparison_benefits():
    result = normalize_plan_comparison(PLAN_COMPARISON_TABLE)

    plans = result["plan_columns"]

    assert (
        plans["secure_basic"]["benefits"]["Room Rent"]
        == "1% of Sum Insured or maximum up to INR 3000/day, whichever is lower"
    )

    assert (
        plans["secure_supreme"]["benefits"]["ICU"]
        == "2% of Sum Insured or maximum up to INR 7500/day, whichever is lower"
    )


# ---------------------------------------------------------------------------
# Medical sub-limit tests
# ---------------------------------------------------------------------------


def test_normalize_medical_sub_limit():
    result = normalize_medical_sub_limit(
        MEDICAL_SUB_LIMIT_TABLE
    )

    assert result["table_type"] == TABLE_FAMILY_MEDICAL_SUB_LIMIT

    assert len(result["rows"]) == 4


def test_medical_sub_limit_treatment():
    result = normalize_medical_sub_limit(
        MEDICAL_SUB_LIMIT_TABLE
    )

    assert result["rows"][0]["treatment"] == "Cataract"
    assert result["rows"][1]["treatment"] == "Hysterectomy"
    assert result["rows"][2]["treatment"] == "PTCA"
    assert result["rows"][3]["treatment"] == "CABG"


def test_medical_sub_limit_values():
    result = normalize_medical_sub_limit(
        MEDICAL_SUB_LIMIT_TABLE
    )

    cataract = result["rows"][0]

    assert cataract["limits"]["secure_basic"] == "20,000"
    assert cataract["limits"]["secure_elite"] == "30,000"
    assert cataract["limits"]["secure_supreme"] == "40,000"
    assert cataract["limits"]["secure_complete"] == "40,000"


# ---------------------------------------------------------------------------
# Continuation tests
# ---------------------------------------------------------------------------


def test_normalize_plan_comparison_continuation():
    result = normalize_plan_comparison_continuation(
        CONTINUATION_TABLE
    )

    assert (
        result["table_type"]
        == TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION
    )

    assert "secure_basic" in result["plan_columns"]
    assert "secure_elite" in result["plan_columns"]
    assert "secure_supreme" in result["plan_columns"]
    assert "secure_complete" in result["plan_columns"]


def test_continuation_rows():
    result = normalize_plan_comparison_continuation(
        CONTINUATION_TABLE
    )

    assert len(result["rows"]) == 2

    assert (
        result["rows"][0]["values"]["secure_basic"]
        == "Covered"
    )

    assert (
        result["rows"][1]["values"]["secure_complete"]
        == "1% of Sum Insured"
    )


# ---------------------------------------------------------------------------
# Simple CIS tests
# ---------------------------------------------------------------------------


def test_normalize_simple_cis():
    result = normalize_simple_cis(
        SIMPLE_CIS_TABLE
    )

    assert result["table_type"] == TABLE_FAMILY_SIMPLE_CIS

    assert len(result["rows"]) == 2


def test_simple_cis_values():
    result = normalize_simple_cis(
        SIMPLE_CIS_TABLE
    )

    first_row = result["rows"][0]

    assert first_row["SR NO"] == "1"
    assert first_row["Title"] == "Product Name"
    assert first_row["Description"] == "Secure Health Connect"
    assert first_row["Reference"] == "Policy"


# ---------------------------------------------------------------------------
# Generic table tests
# ---------------------------------------------------------------------------


def test_normalize_generic():
    result = normalize_generic(
        GENERIC_TABLE
    )

    assert result["table_type"] == TABLE_FAMILY_GENERIC

    assert result["headers"] == [
        "Item",
        "Description",
    ]

    assert len(result["rows"]) == 2


# ---------------------------------------------------------------------------
# Main dispatcher tests
# ---------------------------------------------------------------------------


def test_normalize_table_plan_comparison():
    result = normalize_table(
        PLAN_COMPARISON_TABLE
    )

    assert result["table_family"] == TABLE_FAMILY_PLAN_COMPARISON
    assert result["normalized"]["table_type"] == TABLE_FAMILY_PLAN_COMPARISON


def test_normalize_table_medical_sub_limit():
    result = normalize_table(
        MEDICAL_SUB_LIMIT_TABLE
    )

    assert result["table_family"] == TABLE_FAMILY_MEDICAL_SUB_LIMIT
    assert (
        result["normalized"]["table_type"]
        == TABLE_FAMILY_MEDICAL_SUB_LIMIT
    )


def test_normalize_table_continuation():
    result = normalize_table(
        CONTINUATION_TABLE
    )

    assert (
        result["table_family"]
        == TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION
    )

    assert (
        result["normalized"]["table_type"]
        == TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION
    )


def test_normalize_table_simple_cis():
    result = normalize_table(
        SIMPLE_CIS_TABLE
    )

    assert result["table_family"] == TABLE_FAMILY_SIMPLE_CIS
    assert result["normalized"]["table_type"] == TABLE_FAMILY_SIMPLE_CIS


def test_normalize_table_generic():
    result = normalize_table(
        GENERIC_TABLE
    )

    assert result["table_family"] == TABLE_FAMILY_GENERIC
    assert result["normalized"]["table_type"] == TABLE_FAMILY_GENERIC


# ---------------------------------------------------------------------------
# Batch normalization
# ---------------------------------------------------------------------------


def test_normalize_tables():
    tables = [
        PLAN_COMPARISON_TABLE,
        MEDICAL_SUB_LIMIT_TABLE,
        CONTINUATION_TABLE,
        SIMPLE_CIS_TABLE,
        GENERIC_TABLE,
    ]

    results = normalize_tables(tables)

    assert len(results) == 5

    assert results[0]["normalized"]["table_type"] == (
        TABLE_FAMILY_PLAN_COMPARISON
    )

    assert results[1]["normalized"]["table_type"] == (
        TABLE_FAMILY_MEDICAL_SUB_LIMIT
    )

    assert results[2]["normalized"]["table_type"] == (
        TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION
    )

    assert results[3]["normalized"]["table_type"] == (
        TABLE_FAMILY_SIMPLE_CIS
    )

    assert results[4]["normalized"]["table_type"] == (
        TABLE_FAMILY_GENERIC
    )


# ---------------------------------------------------------------------------
# Critical data-preservation tests
# ---------------------------------------------------------------------------


def test_normalization_preserves_raw_rows():
    table = {
        **PLAN_COMPARISON_TABLE,
        "raw_rows": [
            [
                "Policy Plans",
                "Secure Basic",
                "Secure Elite",
                "Secure Supreme",
                "Secure Complete",
            ]
        ],
    }

    original_raw_rows = [
        row.copy()
        for row in table["raw_rows"]
    ]

    result = normalize_table(table)

    assert result["raw_rows"] == original_raw_rows


def test_normalization_preserves_original_headers():
    original_headers = PLAN_COMPARISON_TABLE["headers"].copy()

    result = normalize_table(
        PLAN_COMPARISON_TABLE
    )

    assert result["headers"] == original_headers


def test_normalization_preserves_original_rows():
    original_rows = [
        row.copy()
        for row in PLAN_COMPARISON_TABLE["rows"]
    ]

    result = normalize_table(
        PLAN_COMPARISON_TABLE
    )

    assert result["rows"] == original_rows


def test_normalization_does_not_modify_input_table():
    original = {
        key: value
        for key, value in PLAN_COMPARISON_TABLE.items()
    }

    normalize_table(PLAN_COMPARISON_TABLE)

    assert PLAN_COMPARISON_TABLE == original