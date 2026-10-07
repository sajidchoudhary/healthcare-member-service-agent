import json

from src.config.settings import settings
from src.ingestion.document_structure import (
    build_document_structure,
    validate_document_structure,
)


def main() -> None:

    print("=" * 70)
    print("DOCUMENT STRUCTURE + CHUNK PREPARATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Load PDF extraction
    # ---------------------------------------------------------

    if not settings.pages_json_path.exists():
        raise FileNotFoundError(
            f"pages.json not found:\n"
            f"{settings.pages_json_path}\n\n"
            f"Run the PDF parser first."
        )

    print(
        f"Input:\n"
        f"{settings.pages_json_path}"
    )

    with open(
        settings.pages_json_path,
        "r",
        encoding="utf-8",
    ) as file:
        pages_data = json.load(file)

    # ---------------------------------------------------------
    # Detect document structure
    # ---------------------------------------------------------

    print("\nDetecting document structure...")

    structure = build_document_structure(
        pages_data
    )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    errors = validate_document_structure(
        structure
    )

    if errors:

        print("\nSTRUCTURE VALIDATION ERRORS:")

        for error in errors:
            print(f"  - {error}")

        raise RuntimeError(
            "Document structure validation failed."
        )

    # ---------------------------------------------------------
    # Save structure
    # ---------------------------------------------------------

    settings.processed_data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        settings.document_structure_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            structure,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ---------------------------------------------------------
    # Display detected structure
    # ---------------------------------------------------------

    sections = structure["structure"]["sections"]

    print("\nStructure created successfully.")

    print(
        f"Document: "
        f"{structure['document']['filename']}"
    )

    print(
        f"Pages: "
        f"{structure['document']['page_count']}"
    )

    print(
        f"Sections detected: "
        f"{len(sections)}"
    )

    print("\nDetected sections:")

    for section in sections:

        indent = "  " * section["level"]

        print(
            f"{indent}"
            f"[L{section['level']}] "
            f"{section['title']} "
            f"(pages "
            f"{section['page_start']}-"
            f"{section['page_end']})"
        )

    print(
        f"\nStructure output:\n"
        f"{settings.document_structure_path}"
    )

    print("\nNext stage:")
    print("Create insurance-specific parent/child chunks.")


if __name__ == "__main__":
    main()