import json

from src.config.settings import settings
from src.ingestion.pdf_parser import extract_pdf


def main() -> None:

    print("=" * 70)
    print("PDF INGESTION")
    print("=" * 70)

    print(f"PDF: {settings.pdf_path}")

    if not settings.pdf_path.exists():
        raise FileNotFoundError(
            f"\nPDF not found:\n{settings.pdf_path}\n\n"
            "Put your PDF inside data/raw/ and name it insurance_detail.pdf"
        )

    settings.processed_data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nExtracting PDF...")

    result = extract_pdf(settings.pdf_path)

    with open(
        settings.pages_json_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\nExtraction completed.")

    print(f"Pages: {result['document']['page_count']}")

    print(
        f"Output: {settings.pages_json_path}"
    )

    print("\nPage summary:")

    for page in result["pages"]:

        text = page["text"]

        print(
            f"Page {page['page_number']:>2}: "
            f"{len(text):>6} characters | "
            f"{len(page['blocks']):>3} blocks"
        )


if __name__ == "__main__":
    main()