from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ingestion.table_extractor import extract_tables
from src.ingestion.table_classifier import (
    classify_tables,
    get_classification_summary,
)
from src.ingestion.table_normalizer import normalize_tables


def process_tables(pdf_path: Path) -> dict[str, Any]:
    """
    Run the complete table processing pipeline.

    Pipeline:

        PDF
         ↓
        Physical extraction
         ↓
        Table classification
         ↓
        Semantic normalization

    Returns:
        {
            "document": {...},
            "table_count": 60,
            "tables": [...],
            "classification_summary": {...}
        }

    The original physical extraction is preserved.
    """

    # ------------------------------------------------------------------
    # Step 1: Physical extraction
    # ------------------------------------------------------------------

    extracted_result = extract_tables(pdf_path)

    # extract_tables() returns:
    #
    # {
    #     "document": {...},
    #     "table_count": ...,
    #     "tables": [...]
    # }
    #
    # We only pass the actual table list to the classifier.

    extracted_tables = extracted_result["tables"]

    # ------------------------------------------------------------------
    # Step 2: Classification
    # ------------------------------------------------------------------

    classified_tables = classify_tables(
        extracted_tables
    )

    # ------------------------------------------------------------------
    # Step 3: Semantic normalization
    # ------------------------------------------------------------------

    normalized_tables = normalize_tables(
        classified_tables
    )

    # ------------------------------------------------------------------
    # Step 4: Classification summary
    # ------------------------------------------------------------------

    classification_summary = get_classification_summary(
        normalized_tables
    )

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    return {
        "document": extracted_result["document"],
        "table_count": extracted_result["table_count"],
        "tables": normalized_tables,
        "classification_summary": classification_summary,
    }