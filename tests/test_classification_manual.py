from backend.services.document_classification import (
    classify_invoice_type,
    classify_document,
)


def run_test(name: str, text: str) -> None:
    print("=" * 70)
    print(name)
    print("=" * 70)

    result = classify_invoice_type(text)

    print("Invoice classification:")
    print(result)

    print()


# ============================================================
# TEST 1 — NORMAL INVOICE
# ============================================================

normal_invoice = """
INVOICE
Invoice No: INV-2026-001
Invoice Date: 10/09/2026
Seller: ABC Technologies Pvt Ltd
Bill To: XYZ Solutions Pvt Ltd
Subtotal: 10000.00
Tax: 1800.00
Total Amount: 11800.00
Currency: INR
"""

run_test(
    "TEST 1 — NORMAL INVOICE",
    normal_invoice,
)


# ============================================================
# TEST 2 — E-INVOICE
# ============================================================

e_invoice = """
E-INVOICE
Invoice No: INV-2026-002
IRN: abc123xyz789
Acknowledgement Number: 123456789012
"""

run_test(
    "TEST 2 — E-INVOICE",
    e_invoice,
)


# ============================================================
# TEST 3 — IRN ALONE
# ============================================================

irn_only = """
INVOICE
Invoice No: INV-2026-003
IRN: ABC123
Subtotal: 5000
Total Amount: 5900
"""

run_test(
    "TEST 3 — IRN ALONE",
    irn_only,
)


# ============================================================
# TEST 4 — TRAINING DOCUMENT
# ============================================================

training_document = """
Training document for invoice processing and invoice extraction.
This document explains how invoice data can be extracted.
"""

run_test(
    "TEST 4 — TRAINING DOCUMENT",
    training_document,
)


# ============================================================
# TEST 5 — GST INVOICE
# ============================================================

gst_invoice = """
GST TAX INVOICE
Invoice No: GST-1001
GSTIN: 33ABCDE1234F1Z5
Seller: ABC Technologies
Bill To: XYZ Solutions
Subtotal: 10000
CGST: 900
SGST: 900
Total Amount: 11800
"""

run_test(
    "TEST 5 — GST INVOICE",
    gst_invoice,
)


# ============================================================
# TEST 6 — FULL DOCUMENT CLASSIFIER
# ============================================================

print("=" * 70)
print("TEST 6 — FULL CLASSIFIER")
print("=" * 70)

result = classify_document(normal_invoice)

print(result)
print()


print("=" * 70)
print("CLASSIFICATION TESTS COMPLETED")
print("=" * 70)