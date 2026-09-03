from fastapi import APIRouter

from backend.services.document_metadata import get_all_documents


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get("/")
def get_documents():
    """
    Get all uploaded document metadata.
    """

    documents = get_all_documents()

    return {
        "total_documents": len(documents),
        "documents": documents,
    }