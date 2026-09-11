from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.schemas.document import DocumentMetadata

from backend.services.document_metadata import (
    save_document_metadata,
)

from backend.services.document_quality import (
    check_document_quality,
)

from backend.services.document_ocr import (
    extract_text,
)

from backend.services.document_classification import (
    classify_document,
)

from backend.services.document_field_extraction import (
    extract_fields,
)

from backend.services.document_relevance import (
    check_document_relevance,
)

from backend.services.document_processing_decision import (
    make_processing_decision,
)

from backend.utils.document_id import (
    generate_document_id,
)

from backend.utils.duplicate_detection import (
    calculate_file_hash,
    find_duplicate,
)

from backend.core.document_status import (
    UPLOADED,
    PROCESSING,
    DO_NOT_PROCESS,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# DIRECTORIES
# ============================================================

UPLOAD_DIR = Path(
    "data/uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FILE VALIDATION
# ============================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@router.post(
    "/upload",
    response_model=DocumentMetadata,
)
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Upload and process a document.

    Pipeline:

        Upload
        ↓
        File validation
        ↓
        Duplicate detection
        ↓
        Save original
        ↓
        Quality analysis
        ↓
        Blank detection
        ↓
        Preprocessing
        ↓
        Orientation correction
        ↓
        Deskew
        ↓
        OCR enhancement
        ↓
        OCR
        ↓
        Document classification
        ↓
        Field extraction
        ↓
        Relevance analysis
        ↓
        Processing decision
        ↓
        Store complete metadata
    """

    # ========================================================
    # 1. Validate filename
    # ========================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    # ========================================================
    # 2. Validate file extension
    # ========================================================

    original_filename = Path(
        file.filename
    ).name

    file_extension = Path(
        original_filename
    ).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed types: PDF, JPG, JPEG, PNG"
            ),
        )

    # ========================================================
    # 3. Read uploaded file
    # ========================================================

    file_content = await file.read()

    file_size = len(
        file_content
    )

    # ========================================================
    # 4. Validate file size
    # ========================================================

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "File too large. "
                "Maximum allowed size is 10 MB"
            ),
        )

    # ========================================================
    # 5. Calculate SHA-256 hash
    # ========================================================

    file_hash = calculate_file_hash(
        file_content
    )

    # ========================================================
    # 6. Detect exact duplicate
    # ========================================================

    duplicate_file = find_duplicate(
        file_hash=file_hash,
        upload_dir=UPLOAD_DIR,
    )

    if duplicate_file:
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate document detected. "
                f"Existing file: {duplicate_file.name}"
            ),
        )

    # ========================================================
    # 7. Generate document ID
    # ========================================================

    document_id = generate_document_id()

    # ========================================================
    # 8. Create safe storage filename
    # ========================================================

    stored_filename = (
        f"{document_id}{file_extension}"
    )

    file_path = (
        UPLOAD_DIR / stored_filename
    )

    # ========================================================
    # 9. Save original document
    # ========================================================

    with open(
        file_path,
        "wb",
    ) as buffer:
        buffer.write(
            file_content
        )

    # ========================================================
    # 10. Analyze document quality
    # ========================================================

    quality_result = check_document_quality(
        str(file_path)
    )

    # ========================================================
    # 11. Stop invalid / unsupported / blank files
    # ========================================================

    if (
        not quality_result.get(
            "success",
            False,
        )
        or quality_result.get(
            "is_blank",
            False,
        )
        or quality_result.get(
            "quality_status"
        ) in {
            "INVALID",
            "UNSUPPORTED",
        }
    ):

        processing_result = (
            make_processing_decision(
                quality_result=quality_result,
                relevance_result={
                    "relevant": False,
                    "reason": (
                        "Document processing stopped "
                        "during quality validation"
                    ),
                },
            )
        )

        metadata = DocumentMetadata(
            document_id=document_id,
            filename=original_filename,
            content_type=file.content_type,
            file_size_bytes=file_size,
            file_hash=file_hash,
            uploaded_at=datetime.now(),

            status=DO_NOT_PROCESS,

            quality_status=quality_result.get(
                "quality_status"
            ),

            quality_score=quality_result.get(
                "quality_score"
            ),

            quality_reason=quality_result.get(
                "reason"
            ),

            processing_status=processing_result.get(
                "processing_status"
            ),

            processing_reason=processing_result.get(
                "reason"
            ),

            manual_review_required=processing_result.get(
                "manual_review_required",
                True,
            ),

            review_status=(
                "PENDING"
                if processing_result.get(
                    "manual_review_required",
                    True,
                )
                else None
            ),

            document_type=None,

            classification_confidence=None,

            classification_reason=None,

            ocr_text=None,

            extracted_fields={},

            logistics_fields={},

            field_confidence={},

            extraction_confidence=None,

            extraction_completeness=None,

            logistics_context=False,

            extraction_reason=None,

            relevance=False,

            relevance_reason=(
                "Document processing stopped "
                "during quality validation"
            ),

            relevance_matched_keywords=[],
        )

        save_document_metadata(
            metadata
        )

        return metadata

    # ========================================================
    # 12. OCR
    # ========================================================

    ocr_result = extract_text(
        str(file_path)
    )

    # ========================================================
    # 13. Extract OCR text
    # ========================================================

    ocr_text = ocr_result.get(
        "text",
        "",
    )

    # ========================================================
    # 14. Handle OCR failure
    # ========================================================

    if not ocr_result.get(
        "success",
        False,
    ):

        processing_result = {
            "processing_status": DO_NOT_PROCESS,
            "reason": ocr_result.get(
                "reason",
                "OCR failed",
            ),
            "manual_review_required": True,
        }

        metadata = DocumentMetadata(
            document_id=document_id,
            filename=original_filename,
            content_type=file.content_type,
            file_size_bytes=file_size,
            file_hash=file_hash,
            uploaded_at=datetime.now(),

            status=DO_NOT_PROCESS,

            quality_status=quality_result.get(
                "quality_status"
            ),

            quality_score=quality_result.get(
                "quality_score"
            ),

            quality_reason=quality_result.get(
                "reason"
            ),

            processing_status=processing_result[
                "processing_status"
            ],

            processing_reason=processing_result[
                "reason"
            ],

            manual_review_required=True,

            review_status="PENDING",

            document_type=None,

            classification_confidence=None,

            classification_reason=None,

            ocr_text=ocr_text,

            extracted_fields={},

            logistics_fields={},

            field_confidence={},

            extraction_confidence=None,

            extraction_completeness=None,

            logistics_context=False,

            extraction_reason=None,

            relevance=False,

            relevance_reason="OCR failed",

            relevance_matched_keywords=[],
        )

        save_document_metadata(
            metadata
        )

        return metadata

    # ========================================================
    # 15. Classify document
    # ========================================================

    classification_result = classify_document(
        ocr_text
    )

    document_type = classification_result.get(
        "document_type"
    )

    # ========================================================
    # 16. Extract fields
    # ========================================================

    extraction_result = extract_fields(
        document_type=document_type,
        extracted_text=ocr_text,
    )

    # ========================================================
    # 17. Check document relevance
    # ========================================================

    relevance_result = check_document_relevance(
        ocr_text,
        document_type=document_type,
    )

    # ========================================================
    # 18. Make processing decision
    # ========================================================

    processing_result = make_processing_decision(
        quality_result=quality_result,
        relevance_result=relevance_result,
    )

    # ========================================================
    # 19. Determine final document status
    # ========================================================

    final_status = (
        PROCESSING
        if processing_result.get(
            "processing_status"
        ) == PROCESSING
        else DO_NOT_PROCESS
    )

    # ========================================================
    # 20. Store complete metadata
    # ========================================================

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=original_filename,
        content_type=file.content_type,
        file_size_bytes=file_size,
        file_hash=file_hash,
        uploaded_at=datetime.now(),

        status=final_status,

        # ----------------------------------------------------
        # Quality
        # ----------------------------------------------------

        quality_status=quality_result.get(
            "quality_status"
        ),

        quality_score=quality_result.get(
            "quality_score"
        ),

        quality_reason=quality_result.get(
            "reason"
        ),

        # ----------------------------------------------------
        # Processing
        # ----------------------------------------------------

        processing_status=processing_result.get(
            "processing_status"
        ),

        processing_reason=processing_result.get(
            "reason"
        ),

        manual_review_required=processing_result.get(
            "manual_review_required",
            False,
        ),

        review_status=(
            "PENDING"
            if processing_result.get(
                "manual_review_required",
                False,
            )
            else None
        ),

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        document_type=document_type,

        classification_confidence=classification_result.get(
            "confidence"
        ),

        classification_reason=classification_result.get(
            "reason"
        ),

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        ocr_text=ocr_text,

        # ----------------------------------------------------
        # Extraction
        # ----------------------------------------------------

        extracted_fields=extraction_result.get(
            "fields",
            {},
        ),

        logistics_fields=extraction_result.get(
            "logistics_fields",
            {},
        ),

        field_confidence=extraction_result.get(
            "field_confidence",
            {},
        ),

        extraction_confidence=extraction_result.get(
            "extraction_confidence"
        ),

        extraction_completeness=extraction_result.get(
            "extraction_completeness"
        ),

        extraction_reason=extraction_result.get(
            "reason"
        ),

        logistics_context=extraction_result.get(
            "logistics_context",
            False,
        ),

        # ----------------------------------------------------
        # Relevance
        # ----------------------------------------------------

        relevance=relevance_result.get(
            "relevant"
        ),

        relevance_reason=relevance_result.get(
            "reason"
        ),

        relevance_matched_keywords=relevance_result.get(
            "matched_keywords",
            [],
        ),
    )

    # ========================================================
    # 21. Save metadata
    # ========================================================

    save_document_metadata(
        metadata
    )

    return metadata
