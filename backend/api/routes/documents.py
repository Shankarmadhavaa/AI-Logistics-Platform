from fastapi import APIRouter

from fastapi import APIRouter, HTTPException

from backend.services.document_metadata import (
    get_all_documents,
    get_document_by_id,
)


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

@router.get("/{document_id}")
def get_document(document_id: str):
    """
    Get metadata for one document by document ID.
    """

    document = get_document_by_id(
        document_id
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document