from __future__ import annotations

import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Add project root to Python path
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------

from src.config.settings import settings
from src.ingestion.table_pipeline import process_tables


def main() -> None:
    print("=" * 70)
    print("TABLE PROCESSING PIPELINE")
    print("=" * 70)

    print(f"\nPDF: {settings.pdf_path}")

    # -----------------------------------------------------------------------
    # Validate PDF
    # -----------------------------------------------------------------------

    if not settings.pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {settings.pdf_path}"
        )

    # -----------------------------------------------------------------------
    # Run table pipeline
    # -----------------------------------------------------------------------

    result = process_tables(
        settings.pdf_path
    )

    tables = result["tables"]
    summary = result["classification_summary"]

    # -----------------------------------------------------------------------
    # Display summary
    # -----------------------------------------------------------------------

    print("\n" + "-" * 70)
    print("TABLE SUMMARY")
    print("-" * 70)

    print(f"Total physical tables: {len(tables)}")

    print("\nTable families:")

    for family, count in sorted(summary.items()):
        print(f"  {family}: {count}")

    # -----------------------------------------------------------------------
    # Save normalized tables
    # -----------------------------------------------------------------------

    output_path = (
        settings.processed_data_dir
        / "tables_normalized.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # -----------------------------------------------------------------------
    # Final output
    # -----------------------------------------------------------------------

    print("\n" + "-" * 70)
    print("OUTPUT")
    print("-" * 70)

    print(f"Saved: {output_path}")

    print("\n" + "=" * 70)
    print("TABLE PROCESSING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

