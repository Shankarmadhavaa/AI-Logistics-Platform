from datetime import datetime

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    content_type: str | None
    file_size_bytes: int
    file_hash: str
    uploaded_at: datetime
    status: str

    # --------------------------------------------------------
    # Document Quality
    # --------------------------------------------------------

    quality_status: str | None = None
    quality_score: int | None = None
    quality_reason: str | None = None

    # --------------------------------------------------------
    # Processing
    # --------------------------------------------------------

    processing_status: str | None = None
    processing_reason: str | None = None

    # --------------------------------------------------------
    # Manual Review
    # --------------------------------------------------------

    manual_review_required: bool = False
    review_status: str | None = None

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    document_type: str | None = None
    classification_confidence: int | None = None
    classification_reason: str | None = None

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    ocr_text: str | None = None

    # --------------------------------------------------------
    # Extraction
    # --------------------------------------------------------

    extracted_fields: dict = Field(
        default_factory=dict
    )

    logistics_fields: dict = Field(
        default_factory=dict
    )

    field_confidence: dict = Field(
        default_factory=dict
    )

    extraction_confidence: int | None = None
    extraction_completeness: int | None = None
    extraction_reason: str | None = None

    processing_path: str | None = None

    invoice_like: bool = False
    invoice_detection_confidence: int | None = None
    secondary_analysis_reason: str | None = None
     
    # --------------------------------------------------------
    # Logistics Context
    # --------------------------------------------------------

    logistics_context: bool = False

    # --------------------------------------------------------
    # Document Relevance
    # --------------------------------------------------------

    relevance: bool | None = None
    relevance_reason: str | None = None

    relevance_matched_keywords: list[str] = Field(
        default_factory=list
    )


class DocumentReviewRequest(BaseModel):
    review_status: str
