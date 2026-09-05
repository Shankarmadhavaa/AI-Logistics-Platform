from datetime import datetime

from pydantic import BaseModel


class DocumentMetadata(BaseModel):

    # --------------------------------
    # Basic document information
    # --------------------------------

    document_id: str

    filename: str

    content_type: str | None

    file_size_bytes: int

    file_hash: str

    uploaded_at: datetime

    status: str

    # --------------------------------
    # Document quality information
    # --------------------------------

    quality_status: str | None = None

    quality_score: int | None = None

    quality_reason: str | None = None

    # --------------------------------
    # Document processing information
    # --------------------------------

    processing_status: str | None = None

    processing_reason: str | None = None

    # --------------------------------
    # Manual review information
    # --------------------------------

    manual_review_required: bool = False

    # --------------------------------
    # Document classification
    # --------------------------------

    document_type: str | None = None

    classification_confidence: int | None = None

    classification_reason: str | None = None

    ocr_text: str | None = None