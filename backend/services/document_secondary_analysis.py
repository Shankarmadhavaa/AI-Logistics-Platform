"""
Secondary document analysis.

This service runs after OCR and primary classification but before
field extraction.

Its purpose is to detect meaningful document intent when the primary
classifier is uncertain or too broad.

Main responsibilities:
- Detect invoice-like documents independently of primary classification.
- Detect logistics context independently.
- Determine the effective document type used by downstream extraction.
- Determine the processing path.
- Mark uncertain cases for manual review.
"""

from __future__ import annotations

import re


INVOICE_CORE_KEYWORDS = {
    "invoice",
    "tax invoice",
    "commercial invoice",
    "proforma invoice",
    "credit note",
    "debit note",
    "bill to",
    "invoice no",
    "invoice number",
    "invoice date",
}


INVOICE_STRUCTURE_KEYWORDS = {
    "subtotal",
    "sub total",
    "tax",
    "gst",
    "vat",
    "igst",
    "cgst",
    "sgst",
    "total",
    "total amount",
    "amount due",
    "balance due",
    "due date",
    "payment terms",
    "unit price",
    "unit cost",
    "quantity",
    "description",
    "item",
    "items",
    "price",
    "currency",
    "amount",
    "rate",
    "buyer",
    "seller",
    "customer",
    "supplier",
    "billing address",
    "shipping address",
    "ship to",
    "bill to",
}


LOGISTICS_KEYWORDS = {
    "pod",
    "proof of delivery",
    "delivery receipt",
    "lorry receipt",
    "lr number",
    "lr no",
    "lorry receipt number",
    "e-way bill",
    "eway bill",
    "eway",
    "delivery challan",
    "consignment",
    "shipment",
    "tracking number",
    "tracking no",
    "awb",
    "air waybill",
    "waybill",
    "vehicle number",
    "vehicle no",
    "transporter",
    "transport",
    "dispatch",
    "delivery",
    "receiver",
    "consignee",
    "consignor",
    "freight",
    "goods",
    "quantity",
    "package",
    "packages",
}


KNOWN_INVOICE_TYPES = {
    "INVOICE",
    "COMMERCIAL_INVOICE",
    "SALES_INVOICE",
    "PURCHASE_INVOICE",
    "SERVICE_INVOICE",
    "TAX_INVOICE",
    "GST_INVOICE",
    "PROFORMA_INVOICE",
    "CREDIT_NOTE",
    "DEBIT_NOTE",
    "EXPORT_INVOICE",
    "IMPORT_INVOICE",
    "E_INVOICE",
}


KNOWN_LOGISTICS_TYPES = {
    "POD",
    "LORRY_RECEIPT",
    "E_WAY_BILL",
    "DELIVERY_CHALLAN",
    "WAREHOUSE_DOCUMENT",
    "OTHER_LOGISTICS_DOCUMENT",
}


def normalize_text(text: str) -> str:
    """Normalize OCR text for matching."""
    if not text:
        return ""

    text = text.lower()
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_phrase(text: str, phrase: str) -> bool:
    """Safely check whether a phrase exists in normalized text."""
    if not text or not phrase:
        return False

    phrase = phrase.lower().strip()

    if " " in phrase or "-" in phrase:
        return phrase in text

    return bool(re.search(rf"\b{re.escape(phrase)}\b", text))


def matched_keywords(text: str, keywords: set[str]) -> list[str]:
    """Return matched keywords in stable order."""
    matches = []

    for keyword in sorted(keywords):
        if contains_phrase(text, keyword):
            matches.append(keyword)

    return matches


def detect_logistics_context(text: str) -> tuple[bool, list[str]]:
    """
    Detect logistics context independently of the primary classifier.

    Quantity, delivery, shipment, receiver, freight, etc. are useful
    context indicators, but invoice identity remains separate.
    """
    matches = matched_keywords(text, LOGISTICS_KEYWORDS)

    return bool(matches), matches


def detect_invoice_like(
    text: str,
    primary_document_type: str | None = None,
) -> dict:
    """
    Detect whether OCR content looks like an invoice.

    The detector deliberately avoids treating a single word such as
    'invoice' as sufficient evidence.

    Scoring:
    - Core invoice identity signals are weighted strongly.
    - Structural invoice signals provide supporting evidence.
    - A known invoice classification is treated as confirmed.
    """

    normalized = normalize_text(text)

    if not normalized:
        return {
            "invoice_like": False,
            "invoice_detection_confidence": 0,
            "invoice_detection_reason": "No OCR text available",
            "invoice_matched_keywords": [],
        }

    primary_type = (primary_document_type or "").upper().strip()

    if primary_type in KNOWN_INVOICE_TYPES:
        matches = matched_keywords(
            normalized,
            INVOICE_CORE_KEYWORDS | INVOICE_STRUCTURE_KEYWORDS,
        )

        return {
            "invoice_like": True,
            "invoice_detection_confidence": 100,
            "invoice_detection_reason": (
                f"Primary classifier identified {primary_type} as an invoice type"
            ),
            "invoice_matched_keywords": matches,
        }

    core_matches = matched_keywords(normalized, INVOICE_CORE_KEYWORDS)
    structure_matches = matched_keywords(
        normalized,
        INVOICE_STRUCTURE_KEYWORDS,
    )

    score = 0

    # Strong identity evidence.
    if core_matches:
        score += min(len(core_matches) * 25, 60)

    # Structural evidence.
    score += min(len(structure_matches) * 8, 40)

    # Strongest common invoice combinations.
    has_invoice_word = contains_phrase(normalized, "invoice")
    has_total = (
        contains_phrase(normalized, "total")
        or contains_phrase(normalized, "total amount")
        or contains_phrase(normalized, "amount due")
    )
    has_tax = (
        contains_phrase(normalized, "tax")
        or contains_phrase(normalized, "gst")
        or contains_phrase(normalized, "vat")
    )
    has_money_structure = (
        contains_phrase(normalized, "subtotal")
        or contains_phrase(normalized, "unit price")
        or contains_phrase(normalized, "amount")
        or contains_phrase(normalized, "currency")
    )

    # Invoice + total is meaningful.
    if has_invoice_word and has_total:
        score += 20

    # Invoice + tax is meaningful.
    if has_invoice_word and has_tax:
        score += 15

    # Invoice + monetary structure is meaningful.
    if has_invoice_word and has_money_structure:
        score += 15

    # Cap the result.
    confidence = min(score, 100)

    # Strong invoice identity.
    if (
        has_invoice_word
        and (
            has_total
            or has_tax
            or has_money_structure
        )
        and len(structure_matches) >= 2
    ):
        invoice_like = True
        confidence = max(confidence, 85)
        reason = (
            "OCR contains invoice identity and multiple invoice "
            "financial/structural indicators"
        )

    # Explicit invoice labels with supporting structure.
    elif len(core_matches) >= 2 and len(structure_matches) >= 2:
        invoice_like = True
        confidence = max(confidence, 80)
        reason = (
            "OCR contains multiple invoice identity and structural indicators"
        )

    # Moderate evidence: process but require review.
    elif has_invoice_word and len(structure_matches) >= 1:
        invoice_like = True
        confidence = max(confidence, 65)
        reason = (
            "OCR contains invoice terminology with limited supporting evidence"
        )

    else:
        invoice_like = False
        reason = "OCR does not contain sufficient invoice evidence"

    return {
        "invoice_like": invoice_like,
        "invoice_detection_confidence": confidence,
        "invoice_detection_reason": reason,
        "invoice_matched_keywords": (
            core_matches + structure_matches
        ),
    }


def analyze_document(
    extracted_text: str,
    primary_document_type: str | None = None,
) -> dict:
    """
    Perform secondary analysis and determine the downstream route.
    """

    normalized = normalize_text(extracted_text)

    if not normalized:
        return {
            "effective_document_type": "UNKNOWN",
            "processing_path": "MANUAL_REVIEW",
            "invoice_like": False,
            "invoice_detection_confidence": 0,
            "invoice_detection_reason": "No OCR text available",
            "invoice_matched_keywords": [],
            "logistics_context": False,
            "logistics_matched_keywords": [],
            "manual_review_required": True,
            "secondary_analysis_reason": (
                "No meaningful OCR content was available for routing"
            ),
        }

    primary_type = (primary_document_type or "UNKNOWN").upper().strip()

    invoice_result = detect_invoice_like(
        normalized,
        primary_document_type=primary_type,
    )

    logistics_context, logistics_matches = detect_logistics_context(
        normalized
    )

    # Confirmed invoice always goes through the universal invoice engine.
    if primary_type in KNOWN_INVOICE_TYPES:
        return {
            "effective_document_type": primary_type,
            "processing_path": "UNIVERSAL_INVOICE",
            **invoice_result,
            "logistics_context": logistics_context,
            "logistics_matched_keywords": logistics_matches,
            "manual_review_required": False,
            "secondary_analysis_reason": (
                "Confirmed invoice classification; routed to universal "
                "invoice extraction"
            ),
        }

    # Invoice-like content can override a weak OTHER_DOCUMENT classification.
    if invoice_result["invoice_like"]:
        confidence = invoice_result["invoice_detection_confidence"]

        # High confidence: route to invoice processing.
        # Moderate confidence: route there but require human review.
        requires_review = confidence < 80

        return {
            "effective_document_type": "INVOICE",
            "processing_path": "UNIVERSAL_INVOICE",
            **invoice_result,
            "logistics_context": logistics_context,
            "logistics_matched_keywords": logistics_matches,
            "manual_review_required": requires_review,
            "secondary_analysis_reason": (
                "Secondary analysis detected invoice-like content and "
                "overrode an uncertain primary classification"
            ),
        }

    # Confirmed logistics document.
    if primary_type in KNOWN_LOGISTICS_TYPES:
        return {
            "effective_document_type": primary_type,
            "processing_path": "LOGISTICS",
            **invoice_result,
            "logistics_context": True,
            "logistics_matched_keywords": logistics_matches,
            "manual_review_required": (
                primary_type == "OTHER_LOGISTICS_DOCUMENT"
            ),
            "secondary_analysis_reason": (
                "Document routed through logistics processing"
            ),
        }

    # Meaningful logistics context with uncertain primary classification.
    if logistics_context:
        return {
            "effective_document_type": "OTHER_LOGISTICS_DOCUMENT",
            "processing_path": "LOGISTICS",
            **invoice_result,
            "logistics_context": True,
            "logistics_matched_keywords": logistics_matches,
            "manual_review_required": True,
            "secondary_analysis_reason": (
                "Meaningful logistics context detected but document type "
                "could not be confidently classified"
            ),
        }

    # Anything meaningful but uncertain goes to manual review instead of
    # silently being treated as irrelevant.
    return {
        "effective_document_type": primary_type or "UNKNOWN",
        "processing_path": "MANUAL_REVIEW",
        **invoice_result,
        "logistics_context": False,
        "logistics_matched_keywords": [],
        "manual_review_required": True,
        "secondary_analysis_reason": (
            "Document contains OCR content but its business type could "
            "not be confidently determined"
        ),
    }