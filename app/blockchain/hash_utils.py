import hashlib
import re


def normalize_text(value):
    if value is None:
        return ""

    value = str(value).strip().upper()

    # Replace multiple spaces with a single space
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_date(value):
    if value is None:
        return ""

    return str(value).strip()


def create_canonical_string(
    doc_type,
    doc_number,
    full_name,
    dob,
    gender,
    nationality
):
    canonical_string = (
        f"doc_type={normalize_text(doc_type)}|"
        f"doc_number={normalize_text(doc_number)}|"
        f"full_name={normalize_text(full_name)}|"
        f"dob={normalize_date(dob)}|"
        f"gender={normalize_text(gender)}|"
        f"nationality={normalize_text(nationality)}"
    )

    return canonical_string


def generate_document_hash(
    doc_type,
    doc_number,
    full_name,
    dob,
    gender,
    nationality
):
    canonical_string = create_canonical_string(
        doc_type=doc_type,
        doc_number=doc_number,
        full_name=full_name,
        dob=dob,
        gender=gender,
        nationality=nationality
    )

    document_hash = hashlib.sha256(
        canonical_string.encode("utf-8")
    ).hexdigest()

    return document_hash, canonical_string