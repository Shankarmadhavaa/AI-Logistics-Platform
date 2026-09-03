# --------------------------------
# Logistics document types
# --------------------------------

SUPPORTED_DOCUMENT_TYPES = {
    "POD",
    "INVOICE",
    "LORRY_RECEIPT",
    "E_WAY_BILL",
    "DELIVERY_CHALLAN",
    "WAREHOUSE_DOCUMENT",
    "OTHER_LOGISTICS_DOCUMENT",
}


# --------------------------------
# Check document relevance
# --------------------------------

def check_document_relevance(extracted_text: str) -> dict:
    """
    Check whether extracted document text appears
    relevant to the logistics document processing system.

    This is an initial rule-based implementation.

    Later this can be replaced or enhanced with
    an AI document classification model.
    """

    if not extracted_text or not extracted_text.strip():

        return {
            "relevant": False,
            "document_type": "UNKNOWN",
            "reason": "No meaningful document text detected",
            "manual_review_required": True,
        }

    text = extracted_text.lower()

    # --------------------------------
    # Logistics-related keywords
    # --------------------------------

    logistics_keywords = {
        "invoice",
        "transport",
        "shipment",
        "delivery",
        "consignment",
        "lorry",
        "truck",
        "vehicle",
        "pod",
        "proof of delivery",
        "eway",
        "e-way",
        "challan",
        "warehouse",
        "goods",
        "quantity",
        "destination",
        "consignee",
        "consignor",
        "carrier",
        "freight",
        "tracking",
    }

    matched_keywords = [
        keyword
        for keyword in logistics_keywords
        if keyword in text
    ]

    # --------------------------------
    # No relevant content
    # --------------------------------

    if not matched_keywords:

        return {
            "relevant": False,
            "document_type": "UNKNOWN",
            "reason": "No relevant logistics document content detected",
            "manual_review_required": True,
        }

    # --------------------------------
    # Relevant document detected
    # --------------------------------

    return {
        "relevant": True,
        "document_type": "OTHER_LOGISTICS_DOCUMENT",
        "reason": "Relevant logistics document content detected",
        "matched_keywords": matched_keywords,
        "manual_review_required": False,
    }