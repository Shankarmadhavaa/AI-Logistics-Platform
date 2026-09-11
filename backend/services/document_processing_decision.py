from backend.core.document_status import (
    DO_NOT_PROCESS,
    PROCESSING,
)


def make_processing_decision(
    quality_result: dict,
    relevance_result: dict,
) -> dict:
    """
    Decide whether a document should continue through the
    processing pipeline.

    Important architecture rule:

    Document quality does NOT automatically reject a
    non-blank document.

    Blurry, dark, light, rotated, tilted, or partially
    readable documents may still continue to OCR.

    The main stop conditions are:

        1. Quality analysis failed
        2. Document is completely blank
        3. Document is invalid/unsupported
        4. OCR/relevance does not provide enough information
           and manual review is required
    """

    # ========================================================
    # QUALITY ANALYSIS FAILURE
    # ========================================================

    if not quality_result.get(
        "success",
        False,
    ):

        return {
            "processing_status": DO_NOT_PROCESS,
            "reason": quality_result.get(
                "reason",
                "Document quality analysis failed",
            ),
            "manual_review_required": True,
        }

    # ========================================================
    # COMPLETELY BLANK DOCUMENT
    # ========================================================

    if quality_result.get(
        "is_blank",
        False,
    ):

        return {
            "processing_status": DO_NOT_PROCESS,
            "reason": quality_result.get(
                "reason",
                "Document appears to be completely blank",
            ),
            "manual_review_required": True,
        }

    # ========================================================
    # INVALID / UNSUPPORTED FILE
    # ========================================================

    if quality_result.get(
        "quality_status"
    ) in {
        "INVALID",
        "UNSUPPORTED",
    }:

        return {
            "processing_status": DO_NOT_PROCESS,
            "reason": quality_result.get(
                "reason",
                "Document cannot be processed",
            ),
            "manual_review_required": True,
        }

    # ========================================================
    # RELEVANCE
    # ========================================================

    if not relevance_result.get(
        "relevant",
        False,
    ):

        return {
            "processing_status": DO_NOT_PROCESS,
            "reason": relevance_result.get(
                "reason",
                "Document requires manual review",
            ),
            "manual_review_required": True,
        }

    # ========================================================
    # DOCUMENT CAN CONTINUE
    # ========================================================

    return {
        "processing_status": PROCESSING,
        "reason": (
            "Document contains meaningful supported "
            "content and can continue processing"
        ),
        "manual_review_required": False,
    }
