from __future__ import annotations

import re
from typing import Any


# ============================================================
# Configuration
# ============================================================

MIN_CHILD_CHARS = 80
MAX_CHILD_CHARS = 1800
TABLE_CHILD_MAX_CHARS = 2200


# ============================================================
# Text utilities
# ============================================================

def clean_text(text: str) -> str:
    """
    Normalize extracted text while preserving paragraph boundaries.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()

        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")

    return "\n".join(lines).strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_paragraphs(text: str) -> list[str]:
    """
    Split section content using paragraph boundaries.

    We intentionally avoid arbitrary fixed-size splitting here.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)

    result = []

    for paragraph in paragraphs:

        paragraph = normalize_whitespace(paragraph)

        if not paragraph:
            continue

        result.append(paragraph)

    return result


def split_long_paragraph(text: str) -> list[str]:
    """
    Split an unusually long paragraph at sentence boundaries.

    This is a safety mechanism, not the primary chunking strategy.
    """

    text = normalize_whitespace(text)

    if len(text) <= MAX_CHILD_CHARS:
        return [text]

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text,
    )

    chunks = []
    current = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if not current:
            current = sentence
            continue

        candidate = f"{current} {sentence}"

        if len(candidate) <= MAX_CHILD_CHARS:
            current = candidate
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    # If a sentence itself is enormous, hard split only as
    # a last-resort safety mechanism.
    final_chunks = []

    for chunk in chunks:

        if len(chunk) <= MAX_CHILD_CHARS:
            final_chunks.append(chunk)
            continue

        for start in range(
            0,
            len(chunk),
            MAX_CHILD_CHARS,
        ):
            final_chunks.append(
                chunk[start:start + MAX_CHILD_CHARS].strip()
            )

    return [
        chunk
        for chunk in final_chunks
        if len(chunk) >= MIN_CHILD_CHARS
    ]


# ============================================================
# Topic / content classification
# ============================================================

def classify_content_type(
    text: str,
    section_title: str = "",
) -> str:

    combined = (
        f"{section_title} {text}"
    ).lower()

    if any(
        term in combined
        for term in [
            "definition",
            "means",
            "shall mean",
            "defined as",
        ]
    ):
        return "definition"

    if any(
        term in combined
        for term in [
            "exclusion",
            "excluded",
            "not covered",
            "not payable",
        ]
    ):
        return "exclusion"

    if any(
        term in combined
        for term in [
            "waiting period",
            "waiting periods",
        ]
    ):
        return "waiting_period"

    if any(
        term in combined
        for term in [
            "eligibility",
            "eligible",
            "eligibility criteria",
        ]
    ):
        return "eligibility"

    if any(
        term in combined
        for term in [
            "claim",
            "claims",
            "claim procedure",
            "claim process",
        ]
    ):
        return "claim"

    if any(
        term in combined
        for term in [
            "hospitalization",
            "hospitalisation",
            "in-patient",
            "inpatient",
            "day care",
        ]
    ):
        return "hospitalization"

    if any(
        term in combined
        for term in [
            "benefit",
            "benefits",
            "coverage",
            "covered",
        ]
    ):
        return "benefit"

    if any(
        term in combined
        for term in [
            "premium",
            "sum insured",
            "co-payment",
            "deductible",
        ]
    ):
        return "policy_term"

    return "policy_clause"


def infer_topic(
    text: str,
    section_title: str = "",
) -> str:

    combined = (
        f"{section_title} {text}"
    ).lower()

    topics = [
        ("waiting_period", [
            "waiting period",
            "waiting periods",
        ]),
        ("exclusions", [
            "exclusion",
            "excluded",
            "not covered",
        ]),
        ("hospitalization", [
            "hospitalization",
            "hospitalisation",
            "in-patient",
            "inpatient",
        ]),
        ("day_care", [
            "day care",
            "day-care",
        ]),
        ("pre_post_hospitalization", [
            "pre-hospitalization",
            "pre hospitalization",
            "post-hospitalization",
            "post hospitalization",
        ]),
        ("maternity", [
            "maternity",
            "pregnancy",
        ]),
        ("cataract", [
            "cataract",
        ]),
        ("organ_transplant", [
            "organ transplant",
            "transplant",
        ]),
        ("ambulance", [
            "ambulance",
        ]),
        ("room_rent", [
            "room rent",
            "room category",
            "icu",
        ]),
        ("claims", [
            "claim",
            "claims",
        ]),
        ("definitions", [
            "definition",
            "means",
            "shall mean",
        ]),
        ("eligibility", [
            "eligibility",
            "eligible",
        ]),
    ]

    for topic, keywords in topics:

        if any(
            keyword in combined
            for keyword in keywords
        ):
            return topic

    return "general_policy"


# ============================================================
# Plan detection
# ============================================================

PLAN_NAMES = [
    "Secure Basic",
    "Secure Elite",
    "Secure Supreme",
    "Secure Complete",
    "Basic",
    "Elite",
    "Supreme",
    "Complete",
]


def detect_plans(text: str) -> list[str]:

    found = []

    for plan in PLAN_NAMES:

        if re.search(
            rf"\b{re.escape(plan)}\b",
            text,
            flags=re.IGNORECASE,
        ):
            found.append(plan)

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(found))


# ============================================================
# Benefit detection
# ============================================================

def detect_benefit(text: str) -> str | None:

    benefit_patterns = [
        "cataract",
        "hysterectomy",
        "ptca",
        "cabg",
        "room rent",
        "icu",
        "ambulance",
        "day care",
        "hospitalization",
        "hospitalisation",
        "pre-hospitalization",
        "post-hospitalization",
        "organ transplant",
        "maternity",
    ]

    lowered = text.lower()

    for benefit in benefit_patterns:

        if benefit in lowered:
            return benefit

    return None


# ============================================================
# Parent chunks
# ============================================================

def make_parent_chunk(
    section: dict[str, Any],
    document_id: str,
) -> dict[str, Any]:

    section_id = section.get(
        "section_id",
        "",
    )

    title = section.get(
        "title",
        "",
    )

    text = clean_text(
        section.get(
            "text",
            "",
        )
    )

    page_start = section.get(
        "page_start"
    )

    page_end = section.get(
        "page_end"
    )

    content_type = classify_content_type(
        text,
        title,
    )

    topic = infer_topic(
        text,
        title,
    )

    plans = detect_plans(
        f"{title}\n{text}"
    )

    parent_id = f"parent_{section_id}"

    return {
        "chunk_id": parent_id,
        "parent_id": None,
        "document_id": document_id,
        "chunk_level": "parent",
        "title": title,
        "section_id": section_id,
        "section_title": title,
        "section_type": section.get(
            "type"
        ),
        "section_level": section.get(
            "level"
        ),
        "content_type": content_type,
        "topic": topic,
        "plan": plans,
        "page_start": page_start,
        "page_end": page_end,
        "line_start": section.get(
            "line_start"
        ),
        "line_end": section.get(
            "line_end"
        ),
        "text": text,
        "char_count": len(text),
        "source": {
            "filename": document_id,
            "page_start": page_start,
            "page_end": page_end,
            "section_id": section_id,
        },
    }


# ============================================================
# Child chunks from textual content
# ============================================================

def make_text_children(
    parent: dict[str, Any],
) -> list[dict[str, Any]]:

    paragraphs = split_paragraphs(
        parent["text"]
    )

    children = []

    child_number = 1

    for paragraph in paragraphs:

        pieces = split_long_paragraph(
            paragraph
        )

        for piece in pieces:

            if len(piece) < MIN_CHILD_CHARS:
                continue

            benefit = detect_benefit(
                piece
            )

            plans = detect_plans(
                piece
            )

            content_type = classify_content_type(
                piece,
                parent["section_title"],
            )

            topic = infer_topic(
                piece,
                parent["section_title"],
            )

            child_id = (
                f"{parent['chunk_id']}"
                f"_child_{child_number:03d}"
            )

            child = {
                "chunk_id": child_id,
                "parent_id": parent["chunk_id"],
                "document_id": parent["document_id"],
                "chunk_level": "child",
                "child_number": child_number,
                "title": parent["section_title"],
                "section_id": parent["section_id"],
                "section_title": parent["section_title"],
                "section_type": parent["section_type"],
                "section_level": parent["section_level"],
                "content_type": content_type,
                "topic": topic,
                "plan": plans,
                "benefit": benefit,
                "page_start": parent["page_start"],
                "page_end": parent["page_end"],
                "text": piece,
                "char_count": len(piece),
                "source": parent["source"],
            }

            children.append(child)

            child_number += 1

    return children


# ============================================================
# Table chunks
# ============================================================

def table_to_retrieval_text(
    table: dict[str, Any],
) -> str:

    table_text = table.get(
        "text",
        "",
    )

    if table_text:
        return normalize_whitespace(
            table_text
        )

    headers = table.get(
        "headers",
        [],
    )

    rows = table.get(
        "rows",
        [],
    )

    parts = []

    if headers:
        parts.append(
            "Columns: "
            + " | ".join(
                normalize_whitespace(str(header))
                for header in headers
            )
        )

    for row in rows:

        values = [
            normalize_whitespace(
                str(value)
            )
            for value in row
        ]

        values = [
            value
            for value in values
            if value
        ]

        if values:
            parts.append(
                " | ".join(values)
            )

    return "\n".join(parts).strip()


def make_table_child(
    table: dict[str, Any],
    parent: dict[str, Any],
    child_number: int,
) -> dict[str, Any]:

    text = table_to_retrieval_text(
        table
    )

    table_page = table.get(
        "page_number",
        parent["page_start"],
    )

    table_id = table.get(
        "table_id"
    )

    plans = detect_plans(
        text
    )

    benefit = detect_benefit(
        text
    )

    child_id = (
        f"{parent['chunk_id']}"
        f"_table_{child_number:03d}"
    )

    return {
        "chunk_id": child_id,
        "parent_id": parent["chunk_id"],
        "document_id": parent["document_id"],
        "chunk_level": "child",
        "child_number": child_number,
        "title": parent["section_title"],
        "section_id": parent["section_id"],
        "section_title": parent["section_title"],
        "section_type": parent["section_type"],
        "section_level": parent["section_level"],
        "content_type": "table",
        "topic": infer_topic(
            text,
            parent["section_title"],
        ),
        "plan": plans,
        "benefit": benefit,
        "page_start": table_page,
        "page_end": table_page,
        "table_id": table_id,
        "table_headers": table.get(
            "headers",
            [],
        ),
        "text": text[:TABLE_CHILD_MAX_CHARS],
        "char_count": min(
            len(text),
            TABLE_CHILD_MAX_CHARS,
        ),
        "source": {
            "filename": parent["document_id"],
            "page_start": table_page,
            "page_end": table_page,
            "section_id": parent["section_id"],
            "table_id": table_id,
        },
    }


# ============================================================
# Section / table relationship
# ============================================================

def tables_for_section(
    section: dict[str, Any],
    tables_data: dict[str, Any],
) -> list[dict[str, Any]]:

    page_start = section.get(
        "page_start"
    )

    page_end = section.get(
        "page_end"
    )

    tables = tables_data.get(
        "tables",
        [],
    )

    matched = []

    for table in tables:

        page_number = table.get(
            "page_number"
        )

        if page_number is None:
            continue

        if (
            page_start is not None
            and page_end is not None
            and page_start <= page_number <= page_end
        ):
            matched.append(table)

    return matched


# ============================================================
# Main parent / child builder
# ============================================================

def build_parent_child_chunks(
    pages_data: dict[str, Any],
    structure_data: dict[str, Any],
    tables_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Build insurance-aware parent and child chunks.

    Parent:
        One logical document section.

    Child:
        Semantic paragraph/sentence unit or a complete table.

    The design intentionally keeps tables separate from prose so
    plan-specific values and numerical limits are not destroyed
    during chunking.
    """

    document = structure_data.get(
        "document",
        {}
    )

    document_id = document.get(
        "filename",
        "insurance_detail.pdf",
    )

    structure = structure_data.get(
        "structure",
        {}
    )

    sections = structure.get(
        "sections",
        []
    )

    if not sections:
        raise ValueError(
            "No document sections found."
        )

    # --------------------------------------------------------
    # Build parents
    # --------------------------------------------------------

    parents = []

    for section in sections:

        text = clean_text(
            section.get(
                "text",
                "",
            )
        )

        # Skip completely empty sections.
        if not text:
            continue

        parent = make_parent_chunk(
            section=section,
            document_id=document_id,
        )

        parents.append(parent)

    # --------------------------------------------------------
    # Build children
    # --------------------------------------------------------

    children = []

    for parent in parents:

        section_children = make_text_children(
            parent
        )

        children.extend(
            section_children
        )

        # Add tables belonging to this section.
        section = {
            "page_start": parent["page_start"],
            "page_end": parent["page_end"],
        }

        section_tables = tables_for_section(
            section=section,
            tables_data=tables_data,
        )

        starting_number = (
            len(section_children) + 1
        )

        for offset, table in enumerate(
            section_tables
        ):

            table_child = make_table_child(
                table=table,
                parent=parent,
                child_number=(
                    starting_number + offset
                ),
            )

            children.append(
                table_child
            )

    # --------------------------------------------------------
    # Ensure every child points to a valid parent
    # --------------------------------------------------------

    parent_ids = {
        parent["chunk_id"]
        for parent in parents
    }

    invalid_children = [
        child["chunk_id"]
        for child in children
        if child["parent_id"]
        not in parent_ids
    ]

    if invalid_children:
        raise ValueError(
            "Invalid child-parent relationships: "
            + ", ".join(
                invalid_children[:10]
            )
        )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return {
        "document": {
            "document_id": document_id,
            "page_count": document.get(
                "page_count"
            ),
        },
        "statistics": {
            "parent_count": len(parents),
            "child_count": len(children),
            "table_child_count": sum(
                1
                for child in children
                if child.get(
                    "content_type"
                ) == "table"
            ),
        },
        "parents": parents,
        "children": children,
    }