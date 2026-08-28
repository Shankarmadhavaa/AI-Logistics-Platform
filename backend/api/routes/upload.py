from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException


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


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    # --------------------------------
    # 1. Check filename
    # --------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    # Get file extension
    file_extension = Path(file.filename).suffix.lower()

    # --------------------------------
    # 2. Check file type
    # --------------------------------

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed types: PDF, JPG, JPEG, PNG"
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
            detail="File too large. Maximum allowed size is 10 MB"
        )

    # --------------------------------
    # 5. Save file
    # --------------------------------

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # --------------------------------
    # 6. Return response
    # --------------------------------

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size_bytes": file_size,
        "message": "Document uploaded successfully",
        "path": str(file_path),
    }