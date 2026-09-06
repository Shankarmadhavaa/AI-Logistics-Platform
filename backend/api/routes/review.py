from fastapi import APIRouter, HTTPException

from backend.schemas.document import DocumentReviewRequest
from backend.services.document_metadata import (
    get_all_documents,
    update_document_review_status,
)

router = APIRouter(
    prefix="/documents",
    tags=["Document Review"],
)


@router.get("/review-required")
def get_documents_for_review():
    """
    Get all documents that require manual review.
    """

    documents = get_all_documents()

    review_documents = [
        document
        for document in documents
        if document.get("manual_review_required") is True
        and document.get("review_status") == "PENDING"
    ]

    return {
        "total_documents": len(review_documents),
        "documents": review_documents,
    }


@router.put("/{document_id}/review")
def update_document_review(
    document_id: str,
    review_request: DocumentReviewRequest,
):
    """
    Approve or reject a document requiring manual review.
    """

    if review_request.review_status not in {
        "APPROVED",
        "REJECTED",
    }:
        raise HTTPException(
            status_code=400,
            detail="Review status must be APPROVED or REJECTED",
        )

    updated_document = update_document_review_status(
        document_id=document_id,
        review_status=review_request.review_status,
    )

    if updated_document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return updated_document