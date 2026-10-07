import re
from typing import Any


# ---------------------------------------------------------
# Heading patterns
# ---------------------------------------------------------

PART_PATTERN = re.compile(
    r"^\s*(PART\s+[IVXLCDM]+(?:\s*[-:.]?\s*.*)?)$",
    re.IGNORECASE,
)

SECTION_PATTERN = re.compile(
    r"^\s*(SECTION\s+[IVXLCDM0-9]+(?:\s*[-:.]?\s*.*)?)$",
    re.IGNORECASE,
)

ANNEXURE_PATTERN = re.compile(
    r"^\s*(ANNEXURE\s+[A-Z0-9IVXLCDM]+(?:\s*[-:.]?\s*.*)?)$",
    re.IGNORECASE,
)

NUMBERED_HEADING_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+){0,4})[\s.)-]+(.+?)\s*$"
)

LETTER_HEADING_PATTERN = re.compile(
    r"^\s*([A-Z])[\s.)-]+(.+?)\s*$"
)

ROMAN_HEADING_PATTERN = re.compile(
    r"^\s*([IVXLCDM]+)[\s.)-]+(.+?)\s*$"
)


# ---------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------

def normalize_line(line: str) -> str:
    """Normalize whitespace without destroying meaningful text."""

    line = line.replace("\u00a0", " ")
    line = re.sub(r"[ \t]+", " ", line)

    return line.strip()


def is_uppercase_heading(text: str) -> bool:
    """
    Detect headings that are mostly uppercase.

    Example:
        WAITING PERIOD
        EXCLUSIONS
        CLAIM PROCEDURE
    """

    letters = [c for c in text if c.isalpha()]

    if len(letters) < 4:
        return False

    uppercase_count = sum(c.isupper() for c in letters)

    return uppercase_count / len(letters) >= 0.80


def looks_like_heading(text: str) -> bool:
    """
    Conservative heading detector.

    We deliberately avoid treating every short line as a heading.
    """

    text = normalize_line(text)

    if not text:
        return False

    if len(text) > 180:
        return False

    if text.endswith((".", ",", ";", ":")):
        return False

    if PART_PATTERN.match(text):
        return True

    if SECTION_PATTERN.match(text):
        return True

    if ANNEXURE_PATTERN.match(text):
        return True

    if NUMBERED_HEADING_PATTERN.match(text):
        return True

    if is_uppercase_heading(text):
        return True

    return False


def heading_level(text: str) -> int:
    """
    Determine hierarchy level.

    Lower number = higher in hierarchy.
    """

    text = normalize_line(text)

    if PART_PATTERN.match(text):
        return 1

    if SECTION_PATTERN.match(text):
        return 2

    if ANNEXURE_PATTERN.match(text):
        return 2

    match = NUMBERED_HEADING_PATTERN.match(text)

    if match:
        number = match.group(1)

        depth = number.count(".") + 1

        return min(depth + 2, 6)

    if ROMAN_HEADING_PATTERN.match(text):
        return 3

    if LETTER_HEADING_PATTERN.match(text):
        return 4

    if is_uppercase_heading(text):
        return 3

    return 6


def classify_heading(text: str) -> str:
    """Classify a detected heading."""

    text = normalize_line(text)

    if PART_PATTERN.match(text):
        return "part"

    if SECTION_PATTERN.match(text):
        return "section"

    if ANNEXURE_PATTERN.match(text):
        return "annexure"

    if NUMBERED_HEADING_PATTERN.match(text):
        return "numbered_section"

    if is_uppercase_heading(text):
        return "heading"

    return "subsection"


def make_section_id(
    counter: int,
    heading: str,
) -> str:

    slug = heading.lower()

    slug = re.sub(
        r"[^a-z0-9]+",
        "_",
        slug,
    )

    slug = slug.strip("_")

    return f"section_{counter}_{slug[:80]}"


# ---------------------------------------------------------
# Main structure builder
# ---------------------------------------------------------

def build_document_structure(
    pages_data: dict[str, Any],
) -> dict[str, Any]:

    pages = pages_data.get("pages", [])

    sections = []

    current_section = None

    section_counter = 0

    hierarchy_stack: list[dict[str, Any]] = []

    for page in pages:

        page_number = page["page_number"]

        text = page.get("text", "")

        lines = text.splitlines()

        for line_index, raw_line in enumerate(lines):

            line = normalize_line(raw_line)

            if not line:
                continue

            if looks_like_heading(line):

                level = heading_level(line)

                section_type = classify_heading(line)

                section_counter += 1

                section_id = make_section_id(
                    section_counter,
                    line,
                )

                # Remove hierarchy levels that are
                # deeper/equal to current heading.
                while (
                    hierarchy_stack
                    and hierarchy_stack[-1]["level"] >= level
                ):
                    hierarchy_stack.pop()

                parent_id = (
                    hierarchy_stack[-1]["section_id"]
                    if hierarchy_stack
                    else None
                )

                section = {
                    "section_id": section_id,
                    "title": line,
                    "type": section_type,
                    "level": level,
                    "parent_id": parent_id,
                    "page_start": page_number,
                    "page_end": page_number,
                    "line_start": line_index,
                    "line_end": line_index,
                    "text": "",
                }

                sections.append(section)

                hierarchy_stack.append(
                    {
                        "section_id": section_id,
                        "level": level,
                    }
                )

                current_section = section

                continue

            # -------------------------------------------------
            # Normal content
            # -------------------------------------------------

            if current_section is not None:

                if current_section["text"]:
                    current_section["text"] += "\n"

                current_section["text"] += line

                current_section["page_end"] = page_number
                current_section["line_end"] = line_index

            else:
                # Content before the first detected heading.
                # Keep it instead of silently losing it.
                if not sections or sections[0]["type"] != "document_intro":

                    section_counter += 1

                    intro = {
                        "section_id": "document_intro",
                        "title": "Document Introduction",
                        "type": "document_intro",
                        "level": 0,
                        "parent_id": None,
                        "page_start": page_number,
                        "page_end": page_number,
                        "line_start": line_index,
                        "line_end": line_index,
                        "text": line,
                    }

                    sections.insert(0, intro)

                    current_section = intro

                else:

                    intro = sections[0]

                    intro["text"] += "\n" + line
                    intro["page_end"] = page_number
                    intro["line_end"] = line_index

    # ---------------------------------------------------------
    # Document metadata
    # ---------------------------------------------------------

    document = pages_data.get("document", {})

    return {
        "document": {
            "filename": document.get("filename"),
            "page_count": document.get("page_count", len(pages)),
        },
        "structure": {
            "section_count": len(sections),
            "sections": sections,
        },
    }


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_document_structure(
    structure: dict[str, Any],
) -> list[str]:

    errors = []

    document = structure.get("document")

    if not document:
        errors.append("Missing document metadata.")

    structure_data = structure.get("structure")

    if not structure_data:
        errors.append("Missing structure metadata.")

        return errors

    sections = structure_data.get("sections", [])

    if not sections:
        errors.append("No sections detected.")

        return errors

    section_ids = {
        section["section_id"]
        for section in sections
    }

    for section in sections:

        if not section.get("section_id"):
            errors.append("Section missing section_id.")

        if not section.get("title"):
            errors.append(
                f"Section {section.get('section_id')} "
                "has no title."
            )

        if section.get("page_start", 0) <= 0:
            errors.append(
                f"Invalid page_start for "
                f"{section.get('section_id')}."
            )

        if section.get("page_end", 0) < section.get("page_start", 0):
            errors.append(
                f"Invalid page range for "
                f"{section.get('section_id')}."
            )

        parent_id = section.get("parent_id")

        if parent_id and parent_id not in section_ids:
            errors.append(
                f"Invalid parent_id '{parent_id}' "
                f"for {section.get('section_id')}."
            )

    return errors