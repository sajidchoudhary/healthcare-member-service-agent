from pathlib import Path
from typing import Any

import fitz


def clean_text(text: str) -> str:
    """
    Basic text normalization.

    We intentionally do NOT aggressively modify the text because
    insurance documents contain important formatting, numbering,
    conditions, exclusions and cross-references.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = [line.rstrip() for line in text.split("\n")]

    cleaned_lines = []
    previous_blank = False

    for line in lines:
        if not line.strip():
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
        else:
            cleaned_lines.append(line)
            previous_blank = False

    return "\n".join(cleaned_lines).strip()


def extract_pdf(pdf_path: Path) -> dict[str, Any]:
    """
    Extract page-level information from a PDF.

    Important:
    - preserves page numbers
    - preserves raw text
    - preserves blocks
    - preserves bounding boxes
    - preserves basic font information

    This gives us a foundation for structure-aware chunking later.
    """

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    document = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        raw_text = page.get_text("text")

        blocks = page.get_text("dict")["blocks"]

        page_blocks = []

        for block in blocks:

            if "lines" not in block:
                continue

            block_text_parts = []

            for line in block["lines"]:

                line_text_parts = []

                for span in line["spans"]:

                    span_text = span.get("text", "")

                    if span_text:
                        line_text_parts.append(span_text)

                if line_text_parts:
                    block_text_parts.append("".join(line_text_parts))

            block_text = "\n".join(block_text_parts).strip()

            if not block_text:
                continue

            page_blocks.append(
                {
                    "bbox": list(block["bbox"]),
                    "text": block_text,
                }
            )

        pages.append(
            {
                "page_number": page_number,
                "text": clean_text(raw_text),
                "blocks": page_blocks,
            }
        )

    document.close()

    return {
        "document": {
            "filename": pdf_path.name,
            "page_count": len(pages),
        },
        "pages": pages,
    }