import json

from src.config.settings import settings
from src.ingestion.table_extractor import (
    extract_tables,
    validate_tables,
)


def main() -> None:

    print("=" * 70)
    print("TABLE EXTRACTION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Validate PDF
    # ---------------------------------------------------------

    if not settings.pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found:\n"
            f"{settings.pdf_path}\n\n"
            f"Put your PDF inside data/raw/ and name it "
            f"insurance_detail.pdf"
        )

    print(
        f"Input:\n"
        f"{settings.pdf_path}"
    )

    # ---------------------------------------------------------
    # Extract tables
    # ---------------------------------------------------------

    print("\nExtracting tables...")

    result = extract_tables(
        settings.pdf_path
    )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    errors = validate_tables(
        result
    )

    if errors:

        print("\nTABLE VALIDATION ERRORS:")

        for error in errors:
            print(f"  - {error}")

        raise RuntimeError(
            "Table extraction validation failed."
        )

    # ---------------------------------------------------------
    # Save tables
    # ---------------------------------------------------------

    settings.processed_data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        settings.tables_json_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ---------------------------------------------------------
    # Display summary
    # ---------------------------------------------------------

    tables = result["tables"]

    print("\nTable extraction completed.")

    print(
        f"Pages: "
        f"{result['document']['page_count']}"
    )

    print(
        f"Tables found: "
        f"{len(tables)}"
    )

    print(
        f"Output:\n"
        f"{settings.tables_json_path}"
    )

    print("\nDetected tables:")

    for table in tables:

        print(
            f"  {table['table_id']} | "
            f"Page {table['page_number']} | "
            f"{table['source']} | "
            f"{len(table['headers'])} columns | "
            f"{len(table['rows'])} rows"
        )


if __name__ == "__main__":
    main()