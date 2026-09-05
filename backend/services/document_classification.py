from email.mime import text


DOCUMENT_TYPES = {
    "GST_INVOICE",
    "COMMERCIAL_INVOICE",
    "PROFORMA_INVOICE",
    "POD",
    "LORRY_RECEIPT",
    "E_WAY_BILL",
    "DELIVERY_CHALLAN",
    "WAREHOUSE_DOCUMENT",
    "OTHER_LOGISTICS_DOCUMENT",
}


def classify_document(extracted_text: str) -> dict:
    """
    Classify a logistics document based on extracted OCR text.

    This is an initial rule-based classifier.
    It can later be replaced or enhanced with an AI model.
    """

    if not extracted_text or not extracted_text.strip():

        return {
            "document_type": "OTHER_LOGISTICS_DOCUMENT",
            "confidence": 0,
            "reason": "No OCR text available for classification",
        }

    text = extracted_text.lower()

    # --------------------------------
    # GST Invoice
    # --------------------------------

    if (
        "gstin" in text
        and "tax invoice" in text
    ):
        return {
            "document_type": "GST_INVOICE",
            "confidence": 95,
            "reason": "GSTIN and Tax Invoice indicators detected",
        }

    # --------------------------------
    # E-Way Bill
    # --------------------------------

    if (
        "e-way bill" in text
        or "eway bill" in text
        or "e-waybill" in text
    ):
        return {
            "document_type": "E_WAY_BILL",
            "confidence": 95,
            "reason": "E-Way Bill indicators detected",
        }

    # --------------------------------
    # Proof of Delivery
    # --------------------------------

    if (
        "proof of delivery" in text
        or "delivery proof" in text
        or "pod" in text
    ):
        return {
            "document_type": "POD",
            "confidence": 90,
            "reason": "Proof of Delivery indicators detected",
        }

    # --------------------------------
    # Lorry Receipt
    # --------------------------------

    if (
        "lorry receipt" in text
        or "lorry receipt no" in text
        or "lr no" in text
        or "lorry" in text
    ):
        return {
            "document_type": "LORRY_RECEIPT",
            "confidence": 90,
            "reason": "Lorry Receipt indicators detected",
        }

    # --------------------------------
    # Delivery Challan
    # --------------------------------

    if (
        "delivery challan" in text
        or "challan" in text
    ):
        return {
            "document_type": "DELIVERY_CHALLAN",
            "confidence": 90,
            "reason": "Delivery Challan indicators detected",
        }

    # --------------------------------
    # Warehouse Document
    # --------------------------------

    if (
        "warehouse" in text
        or "warehouse receipt" in text
        or "stock receipt" in text
    ):
        return {
            "document_type": "WAREHOUSE_DOCUMENT",
            "confidence": 85,
            "reason": "Warehouse document indicators detected",
        }

# --------------------------------
# Proforma Invoice
# --------------------------------

    if (
    "proforma invoice" in text
    or "proforma" in text
  ):

        return {
        "document_type": "PROFORMA_INVOICE",
        "confidence": 95,
        "reason": "Proforma Invoice indicators detected",
    }

    # --------------------------------
    # Commercial Invoice
    # --------------------------------

    if (
    "commercial invoice" in text
    or "commercial invoice no" in text
    or "commercial invoice number" in text
    ):
       return {
        "document_type": "COMMERCIAL_INVOICE",
        "confidence": 90,
        "reason": "Commercial Invoice indicators detected",
    }


# --------------------------------
# General Invoice
# --------------------------------

    invoice_indicators = [
        "invoice",
    "invoice #",
    "invoice no",
    "invoice number",
    "bill to",
    "ship to",
    "unit price",
    "amount",
    "total",
]

    matched_invoice_indicators = [
    indicator
    for indicator in invoice_indicators
    if indicator in text
]

    if len(matched_invoice_indicators) >= 2:
      return {
        "document_type": "COMMERCIAL_INVOICE",
        "confidence": 80,
        "reason": "Multiple invoice indicators detected",
    }

    # --------------------------------
    # Other logistics document
    # --------------------------------

    return {
        "document_type": "OTHER_LOGISTICS_DOCUMENT",
        "confidence": 50,
        "reason": "Logistics document detected but specific type could not be determined",
    }