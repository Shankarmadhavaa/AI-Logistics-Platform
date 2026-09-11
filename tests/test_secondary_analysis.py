from backend.services.document_secondary_analysis import analyze_document


def test_invoice_like_unknown_document():
    result = analyze_document(
        """
        Invoice No: INV-1001
        Invoice Date: 15/01/2025
        Subtotal: 1000
        GST: 180
        Total Amount: 1180
        """,
        "OTHER_DOCUMENT",
    )

    assert result["invoice_like"] is True
    assert result["effective_document_type"] == "INVOICE"
    assert result["processing_path"] == "UNIVERSAL_INVOICE"


def test_confirmed_invoice():
    result = analyze_document(
        """
        Invoice No: INV-1001
        Subtotal: 1000
        Total: 1180
        """,
        "COMMERCIAL_INVOICE",
    )

    assert result["invoice_like"] is True
    assert result["effective_document_type"] == "COMMERCIAL_INVOICE"
    assert result["processing_path"] == "UNIVERSAL_INVOICE"
    assert result["manual_review_required"] is False


def test_logistics_document():
    result = analyze_document(
        """
        Proof of Delivery
        POD Number: POD-100
        Tracking Number: TRK-100
        Receiver Signature
        Delivery Date
        """,
        "OTHER_DOCUMENT",
    )

    assert result["effective_document_type"] == "OTHER_LOGISTICS_DOCUMENT"
    assert result["processing_path"] == "LOGISTICS"
    assert result["logistics_context"] is True
    assert result["manual_review_required"] is True


def test_unknown_meaningful_document_requires_review():
    result = analyze_document(
        """
        Company meeting notes
        Project discussion
        Future planning
        """,
        "OTHER_DOCUMENT",
    )

    assert result["processing_path"] == "MANUAL_REVIEW"
    assert result["manual_review_required"] is True


def test_empty_ocr_requires_review():
    result = analyze_document("", "OTHER_DOCUMENT")

    assert result["effective_document_type"] == "UNKNOWN"
    assert result["processing_path"] == "MANUAL_REVIEW"
    assert result["manual_review_required"] is True