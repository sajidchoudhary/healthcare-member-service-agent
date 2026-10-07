from pathlib import Path

from src.config.settings import settings
from src.ingestion.pdf_parser import extract_pdf


def test_pdf_exists():

    assert settings.pdf_path.exists()


def test_pdf_extraction():

    result = extract_pdf(settings.pdf_path)

    assert "document" in result
    assert "pages" in result

    assert result["document"]["page_count"] > 0
    assert len(result["pages"]) > 0


def test_page_numbers_are_preserved():

    result = extract_pdf(settings.pdf_path)

    page_numbers = [
        page["page_number"]
        for page in result["pages"]
    ]

    assert page_numbers == list(
        range(1, len(page_numbers) + 1)
    )


def test_pages_have_text():

    result = extract_pdf(settings.pdf_path)

    for page in result["pages"]:

        assert isinstance(page["text"], str)
        assert len(page["text"]) > 0