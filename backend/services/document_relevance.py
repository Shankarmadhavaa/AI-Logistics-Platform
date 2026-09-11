# ============================================================
# UNIVERSAL DOCUMENT RELEVANCE
# ============================================================

SUPPORTED_DOCUMENT_TYPES = {
    # --------------------------------------------------------
    # Universal invoice/document types
    # --------------------------------------------------------

    "INVOICE",
    "GST_INVOICE",
    "TAX_INVOICE",
    "COMMERCIAL_INVOICE",
    "PROFORMA_INVOICE",
    "SALES_INVOICE",
    "PURCHASE_INVOICE",
    "SERVICE_INVOICE",
    "EXPORT_INVOICE",
    "IMPORT_INVOICE",
    "E_INVOICE",
    "CREDIT_NOTE",
    "DEBIT_NOTE",

    # --------------------------------------------------------
    # Logistics-specific document types
    # --------------------------------------------------------

    "POD",
    "LORRY_RECEIPT",
    "E_WAY_BILL",
    "DELIVERY_CHALLAN",
    "WAREHOUSE_DOCUMENT",
    "OTHER_LOGISTICS_DOCUMENT",
}


# ============================================================
# UNIVERSAL DOCUMENT KEYWORDS
# ============================================================

UNIVERSAL_DOCUMENT_KEYWORDS = {
    "invoice",
    "bill",
    "receipt",
    "tax invoice",
    "gst invoice",
    "commercial invoice",
    "proforma invoice",
    "sales invoice",
    "purchase invoice",
    "service invoice",
    "credit note",
    "debit note",
    "statement",
    "delivery",
    "proof of delivery",
    "e-way bill",
    "eway bill",
    "delivery challan",
    "warehouse",
    "lorry receipt",
    "purchase order",
    "packing list",
}


# ============================================================
# LOGISTICS CONTEXT KEYWORDS
# ============================================================

LOGISTICS_KEYWORDS = {
    "transportation",
    "transport",
    "freight",
    "shipment",
    "consignment",
    "carrier",
    "tracking number",
    "tracking",
    "vehicle number",
    "vehicle no",
    "lorry",
    "delivery",
    "logistics",
    "warehouse charges",
    "warehouse service",
    "e-way bill",
    "eway bill",
    "proof of delivery",
    "consignor",
    "consignee",
}


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize OCR text for relevance analysis.
    """

    if not text:
        return ""

    return " ".join(
        text.lower().split()
    )


def contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Safely check whether a complete word/phrase exists.
    """

    if not text or not phrase:
        return False

    text = normalize_text(text)
    phrase = normalize_text(phrase)

    if not text or not phrase:
        return False

    padded_text = f" {text} "
    padded_phrase = f" {phrase} "

    return padded_phrase in padded_text


# ============================================================
# LOGISTICS CONTEXT DETECTION
# ============================================================

def detect_logistics_context(
    text: str,
) -> tuple[bool, list[str]]:
    """
    Detect whether the document contains logistics-related
    terminology.

    This does NOT determine document identity.
    """

    if not text:
        return False, []

    matched_keywords = []

    for keyword in LOGISTICS_KEYWORDS:

        if contains_phrase(
            text,
            keyword,
        ):
            matched_keywords.append(
                keyword
            )

    return (
        len(matched_keywords) > 0,
        matched_keywords,
    )


# ============================================================
# UNIVERSAL DOCUMENT RELEVANCE
# ============================================================

def check_document_relevance(
    extracted_text: str,
    document_type: str | None = None,
) -> dict:
    """
    Determine whether OCR content represents a supported
    document.

    Relevance is intentionally UNIVERSAL.

    A document does not need to be logistics-related to be
    relevant.

    Examples of relevant documents:

        INVOICE
        GST_INVOICE
        COMMERCIAL_INVOICE
        CREDIT_NOTE
        POD
        E_WAY_BILL

    Logistics context is reported separately.
    """

    if not extracted_text or not extracted_text.strip():

        return {
            "relevant": False,
            "document_type": "UNKNOWN",
            "reason": (
                "No meaningful document text detected"
            ),
            "matched_keywords": [],
            "logistics_context": False,
            "manual_review_required": True,
        }

    text = normalize_text(
        extracted_text
    )

    normalized_type = (
        document_type.strip().upper()
        if document_type
        else ""
    )

    # --------------------------------------------------------
    # Detect logistics context independently
    # --------------------------------------------------------

    logistics_context, logistics_keywords = (
        detect_logistics_context(
            text
        )
    )

    # --------------------------------------------------------
    # Strong classification result
    # --------------------------------------------------------

    if normalized_type in SUPPORTED_DOCUMENT_TYPES:

        # OTHER_LOGISTICS_DOCUMENT is a fallback type.
        # It should not automatically become relevant unless
        # actual logistics terminology exists.

        if (
            normalized_type
            == "OTHER_LOGISTICS_DOCUMENT"
            and not logistics_context
        ):
            return {
                "relevant": False,
                "document_type": normalized_type,
                "reason": (
                    "Document could not be confidently "
                    "identified as a supported document"
                ),
                "matched_keywords": [],
                "logistics_context": False,
                "manual_review_required": True,
            }

        return {
            "relevant": True,
            "document_type": normalized_type,
            "reason": (
                "Supported document type detected"
            ),
            "matched_keywords": logistics_keywords,
            "logistics_context": logistics_context,
            "manual_review_required": False,
        }

    # --------------------------------------------------------
    # Classification did not provide a supported type.
    #
    # Check for meaningful document terminology.
    # --------------------------------------------------------

    matched_universal_keywords = [
        keyword
        for keyword in UNIVERSAL_DOCUMENT_KEYWORDS
        if contains_phrase(
            text,
            keyword,
        )
    ]

    if matched_universal_keywords:

        return {
            "relevant": True,
            "document_type": (
                normalized_type
                if normalized_type
                else "UNKNOWN"
            ),
            "reason": (
                "Supported document content detected"
            ),
            "matched_keywords": (
                matched_universal_keywords
            ),
            "logistics_context": logistics_context,
            "manual_review_required": False,
        }

    # --------------------------------------------------------
    # Unknown / insufficient content
    # --------------------------------------------------------

    return {
        "relevant": False,
        "document_type": (
            normalized_type
            if normalized_type
            else "UNKNOWN"
        ),
        "reason": (
            "Document type or supported document content "
            "could not be confidently identified"
        ),
        "matched_keywords": [],
        "logistics_context": logistics_context,
        "manual_review_required": True,
    }
