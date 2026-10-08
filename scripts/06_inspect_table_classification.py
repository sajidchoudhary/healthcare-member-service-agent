from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Add project root to Python path
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config.settings import settings
from src.ingestion.table_extractor import extract_tables
from src.ingestion.table_classifier import classify_table


def main() -> None:
    print("=" * 80)
    print("TABLE CLASSIFICATION INSPECTION")
    print("=" * 80)

    result = extract_tables(settings.pdf_path)

    tables = result["tables"]

    print(f"\nTotal tables: {len(tables)}")

    # -----------------------------------------------------------------------
    # Inspect every table
    # -----------------------------------------------------------------------

    for table in tables:
        table_index = table.get("table_index")
        page_number = table.get("page_number", "?")

        headers = table.get("headers", [])
        rows = table.get("rows", [])

        family = classify_table(table)

        print("\n" + "-" * 80)
        print(
            f"TABLE {table_index} | "
            f"PAGE {page_number} | "
            f"FAMILY: {family}"
        )
        print("-" * 80)

        print("\nHEADERS:")
        for index, header in enumerate(headers):
            print(f"  [{index}] {header}")

        print("\nROWS:")

        for row_index, row in enumerate(rows[:5]):
            print(f"  Row {row_index}:")
            for column_index, value in enumerate(row):
                print(
                    f"    [{column_index}] "
                    f"{str(value)[:300]}"
                )

        if len(rows) > 5:
            print(
                f"  ... {len(rows) - 5} additional rows"
            )


if __name__ == "__main__":
    main()