import json
from src.config.settings import settings
from src.chunking.parent_child import build_parent_child_chunks


def main() -> None:
    print("=" * 70)
    print("INSURANCE PARENT / CHILD CHUNKING")
    print("=" * 70)
    # ---------------------------------------------------------
    # Validate required inputs
    # ---------------------------------------------------------

    required_files = [
        settings.pages_json_path,
        settings.document_structure_path,
        settings.tables_json_path,
    ]

    for file_path in required_files:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required input file not found:\n"
                f"{file_path}"
            )

    print("\nInputs:")

    print(
        f"  Pages:\n"
        f"    {settings.pages_json_path}"
    )

    print(
        f"  Structure:\n"
        f"    {settings.document_structure_path}"
    )

    print(
        f"  Tables:\n"
        f"    {settings.tables_json_path}"
    )

    # ---------------------------------------------------------
    # Load processed data
    # ---------------------------------------------------------

    with open(
        settings.pages_json_path,
        "r",
        encoding="utf-8",
    ) as file:

        pages_data = json.load(file)

    with open(
        settings.document_structure_path,
        "r",
        encoding="utf-8",
    ) as file:

        structure_data = json.load(file)

    with open(
        settings.tables_json_path,
        "r",
        encoding="utf-8",
    ) as file:

        tables_data = json.load(file)

    # ---------------------------------------------------------
    # Build parent / child chunks
    # ---------------------------------------------------------

    print("\nBuilding insurance-aware parent/child chunks...")

    result = build_parent_child_chunks(
        pages_data=pages_data,
        structure_data=structure_data,
        tables_data=tables_data,
    )

    # ---------------------------------------------------------
    # Validate result
    # ---------------------------------------------------------

    if "parents" not in result:
        raise RuntimeError(
            "Chunking result does not contain 'parents'."
        )

    if "children" not in result:
        raise RuntimeError(
            "Chunking result does not contain 'children'."
        )

    parents = result["parents"]
    children = result["children"]

    if not parents:
        raise RuntimeError(
            "No parent chunks were created."
        )

    if not children:
        raise RuntimeError(
            "No child chunks were created."
        )

    # ---------------------------------------------------------
    # Save parent chunks
    # ---------------------------------------------------------

    parent_chunks_path = (
        settings.processed_data_dir.parent
        / "chunks"
        / "parent_chunks.json"
    )

    child_chunks_path = (
        settings.processed_data_dir.parent
        / "chunks"
        / "child_chunks.json"
    )

    parent_chunks_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        parent_chunks_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "parents": parents
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ---------------------------------------------------------
    # Save child chunks
    # ---------------------------------------------------------

    with open(
        child_chunks_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "children": children
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ---------------------------------------------------------
    # Display summary
    # ---------------------------------------------------------

    print("\nChunking completed successfully.")

    print(
        f"\nParent chunks: "
        f"{len(parents)}"
    )

    print(
        f"Child chunks: "
        f"{len(children)}"
    )

    print(
        f"\nParent chunks output:\n"
        f"{parent_chunks_path}"
    )

    print(
        f"\nChild chunks output:\n"
        f"{child_chunks_path}"
    )

    # ---------------------------------------------------------
    # Show sample chunks
    # ---------------------------------------------------------

    print("\nSample parent chunk:")

    parent = parents[0]

    print(
        f"  ID: {parent.get('chunk_id')}"
    )

    print(
        f"  Title: {parent.get('title')}"
    )

    print(
        f"  Pages: "
        f"{parent.get('page_start')}-"
        f"{parent.get('page_end')}"
    )

    print(
        f"  Content type: "
        f"{parent.get('content_type')}"
    )

    print("\nSample child chunk:")

    child = children[0]

    print(
        f"  ID: {child.get('chunk_id')}"
    )

    print(
        f"  Parent ID: "
        f"{child.get('parent_id')}"
    )

    print(
        f"  Pages: "
        f"{child.get('page_start')}-"
        f"{child.get('page_end')}"
    )

    print(
        f"  Content type: "
        f"{child.get('content_type')}"
    )


if __name__ == "__main__":
    main()