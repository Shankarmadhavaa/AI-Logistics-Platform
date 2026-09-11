from backend.services.document_relevance import (
    check_document_relevance,
)


def test_restaurant_invoice_is_relevant():
    text = """
    ABC RESTAURANT INC
    INVOICE
    Invoice No: INV-1001
    Bill To: Customer
    Subtotal: $500.00
    Tax: $50.00
    Total: $550.00
    """

    result = check_document_relevance(
        text,
        document_type="INVOICE",
    )

    assert result["relevant"] is True
    assert result["document_type"] == "INVOICE"
    assert result["logistics_context"] is False
    assert result["manual_review_required"] is False


def test_logistics_invoice_detects_logistics_context():
    text = """
    ABC TRANSPORT
    COMMERCIAL INVOICE
    Invoice No: INV-2001
    Freight: $1500
    Transportation charges: $1500
    Tracking Number: TRK12345
    Vehicle Number: TN01AB1234
    Total: $1500
    """

    result = check_document_relevance(
        text,
        document_type="COMMERCIAL_INVOICE",
    )

    assert result["relevant"] is True
    assert result["document_type"] == "COMMERCIAL_INVOICE"
    assert result["logistics_context"] is True
    assert result["manual_review_required"] is False


def test_pod_is_relevant():
    text = """
    PROOF OF DELIVERY
    POD Number: POD12345
    Consignee: ABC Company
    Delivery Date: 15/08/2026
    """

    result = check_document_relevance(
        text,
        document_type="POD",
    )

    assert result["relevant"] is True
    assert result["document_type"] == "POD"
    assert result["logistics_context"] is True
    assert result["manual_review_required"] is False


def test_unknown_document_requires_manual_review():
    text = """
    Hello
    Welcome
    This is a random document.
    """

    result = check_document_relevance(
        text,
        document_type="OTHER_DOCUMENT",
    )

    assert result["relevant"] is False
    assert result["manual_review_required"] is True


def test_empty_ocr_requires_manual_review():
    result = check_document_relevance(
        "",
        document_type="OTHER_DOCUMENT",
    )

    assert result["relevant"] is False
    assert result["manual_review_required"] is True
