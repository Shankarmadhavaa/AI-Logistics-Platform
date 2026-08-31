import json
from pathlib import Path

from backend.schemas.document import DocumentMetadata


# --------------------------------
# Metadata storage location
# --------------------------------

METADATA_DIR = Path("data/metadata")
METADATA_FILE = METADATA_DIR / "documents.json"


# --------------------------------
# Initialize metadata storage
# --------------------------------

def initialize_metadata_storage():
    """
    Create the metadata directory
    and JSON file if they don't exist.
    """

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not METADATA_FILE.exists():
        METADATA_FILE.write_text(
            "[]",
            encoding="utf-8"
        )


# --------------------------------
# Save document metadata
# --------------------------------

def save_document_metadata(
    metadata: DocumentMetadata
):
    """
    Save document metadata to the JSON file.
    """

    initialize_metadata_storage()

    existing_data = json.loads(
        METADATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    existing_data.append(
        metadata.model_dump(
            mode="json"
        )
    )

    METADATA_FILE.write_text(
        json.dumps(
            existing_data,
            indent=4
        ),
        encoding="utf-8"
    )

    return metadata


# --------------------------------
# Get all documents
# --------------------------------

def get_all_documents():
    """
    Return all stored document metadata.
    """

    initialize_metadata_storage()

    return json.loads(
        METADATA_FILE.read_text(
            encoding="utf-8"
        )
    )