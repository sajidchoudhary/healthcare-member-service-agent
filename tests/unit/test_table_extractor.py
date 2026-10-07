from src.config.settings import settings
from src.ingestion.table_extractor import (
    extract_tables,
    validate_tables,
)


def test_table_extraction():

    result = extract_tables(
        settings.pdf_path
    )

    assert "document" in result
    assert "tables" in result

    assert result["document"]["page_count"] == 57
    assert isinstance(result["tables"], list)


def test_tables_are_valid():

    result = extract_tables(
        settings.pdf_path
    )

    errors = validate_tables(
        result
    )

    assert errors == []


def test_tables_have_required_fields():

    result = extract_tables(
        settings.pdf_path
    )

    for table in result["tables"]:

        assert table["table_id"]
        assert table["page_number"] > 0

        assert isinstance(
            table["headers"],
            list,
        )

        assert isinstance(
            table["rows"],
            list,
        )

        assert isinstance(
            table["records"],
            list,
        )

        assert isinstance(
            table["text"],
            str,
        )