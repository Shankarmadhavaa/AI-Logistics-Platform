from backend.core.document_status import (
    PROCESSED,
    DO_NOT_PROCESS,
)


def make_processing_decision(
    quality_result: dict,
    relevance_result: dict,
) -> dict:
    """
    Combine document quality and relevance results
    into one processing decision.
    """

    if quality_result["quality_status"] == DO_NOT_PROCESS:
        return {
            "processing_status": DO_NOT_PROCESS,
            "reason": quality_result["reason"],
            "manual_review_required": True,
        }

    if not relevance_result["relevant"]:
        return {
            "processing_status": DO_NOT_PROCESS,
            "reason": relevance_result["reason"],
            "manual_review_required": True,
        }

    return {
        "processing_status": PROCESSED,
        "reason": "Document passed quality and relevance checks",
        "manual_review_required": False,
    }