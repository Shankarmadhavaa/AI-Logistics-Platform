import re


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize OCR text for classification.

    Converts text to lowercase and normalizes whitespace.
    """

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n+",
        "\n",
        text,
    )

    return text.strip()


def contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Check whether a phrase exists as a meaningful
    sequence of words.

    This prevents substring false positives.

    Example:

        "e invoice" should NOT match:

            "invoice invoice"

    because the first "invoice" ends with the
    letter "e", but it is not a separate word.
    """

    if not text or not phrase:
        return False

    text = normalize_text(text)
    phrase = normalize_text(phrase)

    if not text or not phrase:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(phrase)
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        text,
        re.IGNORECASE,
    ) is not None


def contains_word(
    text: str,
    word: str,
) -> bool:
    """
    Check whether a complete word exists.

    Prevents false positives such as:

        training -> irn
    """

    if not text or not word:
        return False

    text = normalize_text(text)
    word = word.lower().strip()

    if not word:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(word)
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        text,
        re.IGNORECASE,
    ) is not None


def contains_any(
    text: str,
    keywords: list[str],
) -> bool:
    """
    Check whether any supplied word or phrase exists.

    Uses safe word/phrase matching rather than
    raw substring matching.
    """

    if not text or not keywords:
        return False

    return any(
        contains_phrase(text, keyword)
        for keyword in keywords
    )


# ============================================================
# LOGISTICS DOCUMENT CLASSIFICATION
# ============================================================

def classify_logistics_document(
    text: str,
) -> tuple[str | None, int, str]:
    """
    Identify genuine logistics-specific document types.

    Important:

    An invoice containing logistics terminology should
    still be classified as an invoice.

    This function therefore looks for strong document
    identity indicators rather than general logistics words.
    """

    # --------------------------------------------------------
    # Proof of Delivery
    # --------------------------------------------------------

    if (
        contains_phrase(text, "proof of delivery")
        or contains_phrase(text, "delivery proof")
        or contains_word(text, "pod")
    ):
        return (
            "POD",
            95,
            "Proof of delivery indicators detected",
        )

    # --------------------------------------------------------
    # E-Way Bill
    # --------------------------------------------------------

    if (
        contains_phrase(text, "e-way bill")
        or contains_phrase(text, "eway bill")
        or contains_phrase(text, "e way bill")
    ):
        return (
            "E_WAY_BILL",
            95,
            "E-way bill indicators detected",
        )

    # --------------------------------------------------------
    # Lorry Receipt
    # --------------------------------------------------------

    if (
        contains_phrase(text, "lorry receipt")
        or contains_phrase(text, "lorry receipt no")
        or contains_phrase(text, "lr no")
        or contains_phrase(text, "lr number")
    ):
        return (
            "LORRY_RECEIPT",
            95,
            "Lorry receipt indicators detected",
        )

    # --------------------------------------------------------
    # Delivery Challan
    # --------------------------------------------------------

    if contains_phrase(
        text,
        "delivery challan",
    ):
        return (
            "DELIVERY_CHALLAN",
            95,
            "Delivery challan indicators detected",
        )

    # --------------------------------------------------------
    # Warehouse Documents
    #
    # Only classify as warehouse document when there is
    # strong document-specific wording.
    #
    # Do NOT classify an invoice containing:
    #
    #     warehouse charges
    #
    # as WAREHOUSE_DOCUMENT.
    # --------------------------------------------------------

    if (
        contains_phrase(
            text,
            "warehouse receipt",
        )
        or contains_phrase(
            text,
            "warehouse document",
        )
        or contains_phrase(
            text,
            "warehouse receipt number",
        )
    ):
        return (
            "WAREHOUSE_DOCUMENT",
            90,
            "Warehouse document indicators detected",
        )

    return (
        None,
        0,
        "No logistics-specific document indicators detected",
    )


# ============================================================
# INVOICE CLASSIFICATION
# ============================================================

def classify_invoice_type(
    text: str,
) -> tuple[str | None, int, str]:
    """
    Identify the specific invoice type.

    Classification priority:

        Credit Note
        Debit Note
        Explicit E-Invoice
        Proforma Invoice
        Export Invoice
        Import Invoice
        Purchase Invoice
        Sales Invoice
        Service Invoice
        Commercial Invoice
        GST Invoice
        Tax Invoice
        Generic Invoice
        Unknown

    Important rules:

    1. The word "invoice" alone is not enough.
    2. "IRN" alone is not enough to identify an e-invoice.
    3. Explicit "e-invoice" wording is strong evidence.
    4. Multiple e-invoice identifiers can identify an e-invoice.
    """

    text = normalize_text(text)

    if not text:
        return (
            None,
            0,
            "No text available for invoice classification",
        )

    # ========================================================
    # CREDIT NOTE
    # ========================================================

    if (
        contains_phrase(text, "credit note")
        or contains_phrase(text, "credit memo")
    ):
        return (
            "CREDIT_NOTE",
            95,
            "Credit note indicators detected",
        )

    # ========================================================
    # DEBIT NOTE
    # ========================================================

    if (
        contains_phrase(text, "debit note")
        or contains_phrase(text, "debit memo")
    ):
        return (
            "DEBIT_NOTE",
            95,
            "Debit note indicators detected",
        )

    # ========================================================
    # E-INVOICE
    # ========================================================

    explicit_e_invoice = (
        contains_phrase(text, "e-invoice")
        or contains_phrase(text, "e invoice")
    )

    if explicit_e_invoice:
        return (
            "E_INVOICE",
            95,
            "Explicit e-invoice wording detected",
        )

    # --------------------------------------------------------
    # Supporting e-invoice identifiers
    #
    # Do NOT classify based on IRN alone.
    # --------------------------------------------------------

    e_invoice_supporting_indicators = []

    if contains_word(text, "irn"):
        e_invoice_supporting_indicators.append(
            "IRN"
        )

    if contains_phrase(
        text,
        "invoice reference number",
    ):
        e_invoice_supporting_indicators.append(
            "invoice reference number"
        )

    if contains_phrase(
        text,
        "invoice registration number",
    ):
        e_invoice_supporting_indicators.append(
            "invoice registration number"
        )

    if (
        contains_phrase(
            text,
            "acknowledgement number",
        )
        or contains_phrase(
            text,
            "acknowledgment number",
        )
    ):
        e_invoice_supporting_indicators.append(
            "acknowledgement number"
        )

    # --------------------------------------------------------
    # Require at least TWO supporting identifiers.
    # --------------------------------------------------------

    if len(e_invoice_supporting_indicators) >= 2:
        return (
            "E_INVOICE",
            90,
            "Multiple e-invoice identifiers detected: "
            + ", ".join(
                e_invoice_supporting_indicators
            ),
        )

    # ========================================================
    # PROFORMA INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "proforma invoice",
        )
        or contains_phrase(
            text,
            "pro forma invoice",
        )
        or contains_phrase(
            text,
            "proforma",
        )
    ):
        return (
            "PROFORMA_INVOICE",
            95,
            "Proforma invoice indicators detected",
        )

    # ========================================================
    # EXPORT INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "export invoice",
        )
        or contains_phrase(
            text,
            "export commercial invoice",
        )
    ):
        return (
            "EXPORT_INVOICE",
            90,
            "Export invoice indicators detected",
        )

    # ========================================================
    # IMPORT INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "import invoice",
        )
        or contains_phrase(
            text,
            "import commercial invoice",
        )
    ):
        return (
            "IMPORT_INVOICE",
            90,
            "Import invoice indicators detected",
        )

    # ========================================================
    # PURCHASE INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "purchase invoice",
        )
        or contains_phrase(
            text,
            "purchase bill",
        )
    ):
        return (
            "PURCHASE_INVOICE",
            90,
            "Purchase invoice indicators detected",
        )

    # ========================================================
    # SALES INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "sales invoice",
        )
        or contains_phrase(
            text,
            "sales bill",
        )
    ):
        return (
            "SALES_INVOICE",
            90,
            "Sales invoice indicators detected",
        )

    # ========================================================
    # SERVICE INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "service invoice",
        )
        or contains_phrase(
            text,
            "service bill",
        )
    ):
        return (
            "SERVICE_INVOICE",
            90,
            "Service invoice indicators detected",
        )

    # ========================================================
    # COMMERCIAL INVOICE
    # ========================================================

    if (
        contains_phrase(
            text,
            "commercial invoice",
        )
        or contains_phrase(
            text,
            "commercial bill",
        )
    ):
        return (
            "COMMERCIAL_INVOICE",
            90,
            "Commercial invoice indicators detected",
        )

    # ========================================================
    # GST INVOICE
    #
    # Must come before generic TAX INVOICE.
    # ========================================================

    if (
        contains_phrase(
            text,
            "gst tax invoice",
        )
        or contains_phrase(
            text,
            "gst invoice",
        )
    ):
        return (
            "GST_INVOICE",
            95,
            "GST invoice indicators detected",
        )

    # ========================================================
    # TAX INVOICE
    # ========================================================

    if contains_phrase(
        text,
        "tax invoice",
    ):
        return (
            "TAX_INVOICE",
            95,
            "Tax invoice indicators detected",
        )

    # ========================================================
    # GENERIC INVOICE
    # ========================================================

    invoice_indicators = []

    if contains_word(
        text,
        "invoice",
    ):
        invoice_indicators.append(
            "invoice"
        )

    if (
        contains_phrase(
            text,
            "invoice no",
        )
        or contains_phrase(
            text,
            "invoice number",
        )
    ):
        invoice_indicators.append(
            "invoice number"
        )

    if contains_phrase(
        text,
        "bill to",
    ):
        invoice_indicators.append(
            "bill to"
        )

    if contains_phrase(
        text,
        "ship to",
    ):
        invoice_indicators.append(
            "ship to"
        )

    if contains_phrase(
        text,
        "unit price",
    ):
        invoice_indicators.append(
            "unit price"
        )

    if contains_phrase(
        text,
        "subtotal",
    ):
        invoice_indicators.append(
            "subtotal"
        )

    if contains_phrase(
        text,
        "total amount",
    ):
        invoice_indicators.append(
            "total amount"
        )

    if contains_phrase(
        text,
        "amount due",
    ):
        invoice_indicators.append(
            "amount due"
        )

    if contains_phrase(
        text,
        "due date",
    ):
        invoice_indicators.append(
            "due date"
        )

    # --------------------------------------------------------
    # Generic invoice requires multiple indicators.
    # --------------------------------------------------------

    if (
        "invoice" in invoice_indicators
        and len(invoice_indicators) >= 3
    ):
        return (
            "INVOICE",
            85,
            "Multiple invoice indicators detected: "
            + ", ".join(
                invoice_indicators
            ),
        )

    if (
        "invoice" in invoice_indicators
        and len(invoice_indicators) == 2
    ):
        return (
            "INVOICE",
            75,
            "Invoice indicators detected: "
            + ", ".join(
                invoice_indicators
            ),
        )

    return (
        None,
        0,
        "No sufficient invoice indicators detected",
    )

# ============================================================
# UNIVERSAL DOCUMENT CLASSIFICATION
# ============================================================

def classify_document(
    extracted_text: str,
) -> dict:
    """
    Universal document classification engine.

    Architecture:

        Strong logistics document
                  OR
        Invoice document
                  ↓
        Universal document classification

    Logistics context is NOT treated as the same thing
    as document identity.
    """

    text = normalize_text(
        extracted_text
    )

    if not text:
        return {
            "document_type": "OTHER_DOCUMENT",
            "confidence": 0,
            "reason": (
                "No OCR text available "
                "for classification"
            ),
        }

    # --------------------------------------------------------
    # First identify genuine logistics documents.
    #
    # These have strong document identity indicators such as:
    #
    # POD
    # Lorry Receipt
    # E-Way Bill
    # Delivery Challan
    #
    # An invoice containing logistics words should NOT match
    # these unless it clearly identifies itself as that document.
    # --------------------------------------------------------

    logistics_type, logistics_confidence, logistics_reason = (
        classify_logistics_document(
            text
        )
    )

    if logistics_type:
        return {
            "document_type": logistics_type,
            "confidence": logistics_confidence,
            "reason": logistics_reason,
        }

    # --------------------------------------------------------
    # Invoice classification
    # --------------------------------------------------------

    invoice_type, invoice_confidence, invoice_reason = (
        classify_invoice_type(
            text
        )
    )

    if invoice_type:
        return {
            "document_type": invoice_type,
            "confidence": invoice_confidence,
            "reason": invoice_reason,
        }

    # --------------------------------------------------------
    # Unknown / unsupported document
    # --------------------------------------------------------

    return {
        "document_type": "OTHER_DOCUMENT",
        "confidence": 30,
        "reason": (
            "No supported document type "
            "could be confidently identified"
        ),
    }