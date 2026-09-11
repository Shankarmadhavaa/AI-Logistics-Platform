from backend.services.document_processing_decision import (
    make_processing_decision,
)


def test_good_quality_supported_document_is_processed():

    quality = {
        "success": True,
        "is_blank": False,
        "quality_status": "GOOD",
    }

    relevance = {
        "relevant": True,
        "reason": "Supported document type detected",
    }

    result = make_processing_decision(
        quality,
        relevance,
    )

    assert result["processing_status"] == "PROCESSING"
    assert result["manual_review_required"] is False


def test_low_quality_readable_document_is_not_rejected():

    quality = {
        "success": True,
        "is_blank": False,
        "quality_status": "LOW",
        "reason": "Document is blurry",
    }

    relevance = {
        "relevant": True,
        "reason": "Supported document type detected",
    }

    result = make_processing_decision(
        quality,
        relevance,
    )

    assert result["processing_status"] == "PROCESSING"
    assert result["manual_review_required"] is False


def test_blank_document_is_not_processed():

    quality = {
        "success": True,
        "is_blank": True,
        "quality_status": "BLANK",
        "reason": "Document appears to be completely blank",
    }

    relevance = {
        "relevant": True,
        "reason": "Supported document type detected",
    }

    result = make_processing_decision(
        quality,
        relevance,
    )

    assert result["processing_status"] == "DO_NOT_PROCESS"
    assert result["manual_review_required"] is True


def test_unknown_document_requires_manual_review():

    quality = {
        "success": True,
        "is_blank": False,
        "quality_status": "GOOD",
    }

    relevance = {
        "relevant": False,
        "reason": "Document type could not be confidently identified",
    }

    result = make_processing_decision(
        quality,
        relevance,
    )

    assert result["processing_status"] == "DO_NOT_PROCESS"
    assert result["manual_review_required"] is True


def test_quality_analysis_failure_stops_processing():

    quality = {
        "success": False,
        "is_blank": False,
        "quality_status": "INVALID",
        "reason": "Quality analysis failed",
    }

    relevance = {
        "relevant": True,
        "reason": "Supported document type detected",
    }

    result = make_processing_decision(
        quality,
        relevance,
    )

    assert result["processing_status"] == "DO_NOT_PROCESS"
    assert result["manual_review_required"] is True
