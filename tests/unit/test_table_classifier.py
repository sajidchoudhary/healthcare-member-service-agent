from src.ingestion.table_classifier import (
    TABLE_FAMILY_PLAN_COMPARISON,
    TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION,
    TABLE_FAMILY_MEDICAL_SUB_LIMIT,
    TABLE_FAMILY_SIMPLE_CIS,
    TABLE_FAMILY_GENERIC,
    classify_table,
    classify_tables,
    get_classification_summary,
    is_plan_comparison_table,
    is_medical_sub_limit_table,
    is_simple_cis_table,
    looks_like_continuation,
)


# ---------------------------------------------------------------------------
# Sample tables
# ---------------------------------------------------------------------------

PLAN_COMPARISON_TABLE = {
    "table_index": 1,
    "page_number": 1,
    "headers": [
        "Policy Plans",
        "Secure Basic",
        "Secure Elite",
        "Secure Supreme",
        "Secure Complete",
    ],
    "rows": [
        [
            "In-patient Hospitalization",
            "Covered",
            "Covered",
            "Covered",
            "Covered",
        ],
        [
            "Room Rent",
            "1% of Sum Insured",
            "1% of Sum Insured",
            "1% of Sum Insured",
            "1% of Sum Insured",
        ],
    ],
}


MEDICAL_SUB_LIMIT_TABLE = {
    "table_index": 7,
    "page_number": 7,
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


SIMPLE_CIS_TABLE = {
    "table_index": 2,
    "page_number": 1,
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


CONTINUATION_TABLE = {
    "table_index": 3,
    "page_number": 2,
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


GENERIC_TABLE = {
    "table_index": 20,
    "page_number": 20,
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
# Individual detector tests
# ---------------------------------------------------------------------------


def test_is_plan_comparison_table():
    assert is_plan_comparison_table(PLAN_COMPARISON_TABLE) is True


def test_is_not_plan_comparison_table():
    assert is_plan_comparison_table(MEDICAL_SUB_LIMIT_TABLE) is False
    assert is_plan_comparison_table(GENERIC_TABLE) is False


def test_is_medical_sub_limit_table():
    assert is_medical_sub_limit_table(MEDICAL_SUB_LIMIT_TABLE) is True


def test_is_not_medical_sub_limit_table():
    assert is_medical_sub_limit_table(PLAN_COMPARISON_TABLE) is False
    assert is_medical_sub_limit_table(GENERIC_TABLE) is False


def test_is_simple_cis_table():
    assert is_simple_cis_table(SIMPLE_CIS_TABLE) is True


def test_is_not_simple_cis_table():
    assert is_simple_cis_table(PLAN_COMPARISON_TABLE) is False
    assert is_simple_cis_table(GENERIC_TABLE) is False


def test_looks_like_continuation_table():
    assert looks_like_continuation(CONTINUATION_TABLE) is True


def test_regular_table_is_not_continuation():
    assert looks_like_continuation(SIMPLE_CIS_TABLE) is False
    assert looks_like_continuation(GENERIC_TABLE) is False


# ---------------------------------------------------------------------------
# Main classification tests
# ---------------------------------------------------------------------------


def test_classify_plan_comparison():
    result = classify_table(PLAN_COMPARISON_TABLE)

    assert result == TABLE_FAMILY_PLAN_COMPARISON


def test_classify_medical_sub_limit():
    result = classify_table(MEDICAL_SUB_LIMIT_TABLE)

    assert result == TABLE_FAMILY_MEDICAL_SUB_LIMIT


def test_classify_simple_cis():
    result = classify_table(SIMPLE_CIS_TABLE)

    assert result == TABLE_FAMILY_SIMPLE_CIS


def test_classify_continuation():
    result = classify_table(CONTINUATION_TABLE)

    assert result == TABLE_FAMILY_PLAN_COMPARISON_CONTINUATION


def test_classify_generic():
    result = classify_table(GENERIC_TABLE)

    assert result == TABLE_FAMILY_GENERIC


# ---------------------------------------------------------------------------
# classify_tables tests
# ---------------------------------------------------------------------------


def test_classify_tables_adds_table_family():
    tables = [
        PLAN_COMPARISON_TABLE.copy(),
        MEDICAL_SUB_LIMIT_TABLE.copy(),
        SIMPLE_CIS_TABLE.copy(),
        GENERIC_TABLE.copy(),
    ]

    results = classify_tables(tables)

    assert len(results) == 4

    assert results[0]["table_family"] == TABLE_FAMILY_PLAN_COMPARISON
    assert results[1]["table_family"] == TABLE_FAMILY_MEDICAL_SUB_LIMIT
    assert results[2]["table_family"] == TABLE_FAMILY_SIMPLE_CIS
    assert results[3]["table_family"] == TABLE_FAMILY_GENERIC


def test_classify_tables_preserves_original_fields():
    table = PLAN_COMPARISON_TABLE.copy()

    result = classify_tables([table])[0]

    assert result["table_index"] == table["table_index"]
    assert result["page_number"] == table["page_number"]
    assert result["headers"] == table["headers"]
    assert result["rows"] == table["rows"]


# ---------------------------------------------------------------------------
# Classification summary
# ---------------------------------------------------------------------------


def test_get_classification_summary():
    tables = [
        classify_tables([PLAN_COMPARISON_TABLE.copy()])[0],
        classify_tables([MEDICAL_SUB_LIMIT_TABLE.copy()])[0],
        classify_tables([SIMPLE_CIS_TABLE.copy()])[0],
        classify_tables([GENERIC_TABLE.copy()])[0],
        classify_tables([GENERIC_TABLE.copy()])[0],
    ]

    summary = get_classification_summary(tables)

    assert summary[TABLE_FAMILY_PLAN_COMPARISON] == 1
    assert summary[TABLE_FAMILY_MEDICAL_SUB_LIMIT] == 1
    assert summary[TABLE_FAMILY_SIMPLE_CIS] == 1
    assert summary[TABLE_FAMILY_GENERIC] == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_table_is_generic():
    table = {
        "table_index": 100,
        "headers": [],
        "rows": [],
    }

    result = classify_table(table)

    assert result == TABLE_FAMILY_GENERIC


def test_classification_is_case_insensitive():
    table = {
        "table_index": 101,
        "headers": [
            "policy plans",
            "SECURE BASIC",
            "secure elite",
            "Secure Supreme",
            "secure complete",
        ],
        "rows": [],
    }

    result = classify_table(table)

    assert result == TABLE_FAMILY_PLAN_COMPARISON


def test_medical_terms_can_be_detected_from_rows():
    table = {
        "table_index": 102,
        "headers": [
            "Treatment",
            "Amount",
        ],
        "rows": [
            ["Cataract", "20,000"],
            ["Hysterectomy", "35,000"],
            ["PTCA", "80,000"],
        ],
    }

    result = classify_table(table)

    assert result == TABLE_FAMILY_MEDICAL_SUB_LIMIT