from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.schemas.document import DocumentMetadata
from backend.services.document_metadata import save_document_metadata
from backend.services.document_quality import check_document_quality
from backend.services.document_ocr import extract_text
from backend.services.document_relevance import check_document_relevance
from backend.services.document_processing_decision import (
    make_processing_decision,
)
from backend.utils.document_id import generate_document_id
from backend.utils.duplicate_detection import (
    calculate_file_hash,
    find_duplicate,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# Where uploaded documents will be stored
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Allowed document types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)):

    # --------------------------------
    # 1. Check filename
    # --------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    file_extension = Path(file.filename).suffix.lower()

    # --------------------------------
    # 2. Check file type
    # --------------------------------

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed types: PDF, JPG, JPEG, PNG",
        )

    # --------------------------------
    # 3. Read file
    # --------------------------------

    file_content = await file.read()

    # --------------------------------
    # 4. Check file size
    # --------------------------------

    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum allowed size is 10 MB",
        )

    # --------------------------------
    # 5. Calculate file hash
    # --------------------------------

    file_hash = calculate_file_hash(file_content)

    # --------------------------------
    # 6. Check for duplicate
    # --------------------------------

    duplicate_file = find_duplicate(
        file_hash=file_hash,
        upload_dir=UPLOAD_DIR,
    )

    if duplicate_file:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate document detected. Existing file: {duplicate_file.name}",
        )

    # --------------------------------
    # 7. Generate document ID
    # --------------------------------

    document_id = generate_document_id()

    # --------------------------------
    # 8. Save file
    # --------------------------------

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # --------------------------------
    # 9. Check document quality
    # --------------------------------

    quality_result = check_document_quality(
        str(file_path)
    )

    # --------------------------------
    # 10. Extract text using OCR
    # --------------------------------

    ocr_result = extract_text(
        str(file_path)
    )

    # --------------------------------
    # 11. Check document relevance
    # --------------------------------

    relevance_result = check_document_relevance(
        ocr_result["text"]
    )

    # --------------------------------
    # 12. Make processing decision
    # --------------------------------

    processing_result = make_processing_decision(
        quality_result=quality_result,
        relevance_result=relevance_result,
    )

    # --------------------------------
    # 13. Create document metadata
    # --------------------------------

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        file_size_bytes=file_size,
        file_hash=file_hash,
        uploaded_at=datetime.now(),
        status="UPLOADED",

        quality_status=quality_result["quality_status"],
        quality_score=quality_result["quality_score"],
        quality_reason=quality_result["reason"],

        processing_status=processing_result["processing_status"],
        processing_reason=processing_result["reason"],

        manual_review_required=processing_result[
            "manual_review_required"
        ],

        document_type=relevance_result["document_type"],
    )

    # --------------------------------
    # 14. Save document metadata
    # --------------------------------

    save_document_metadata(metadata)

    # --------------------------------
    # 15. Return metadata
    # --------------------------------

    return metadata