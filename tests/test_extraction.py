from backend.services.document_field_extraction import extract_amount, extract_fields


print("=" * 70)
print("TEST 1 - USD AMOUNT EXTRACTION")
print("=" * 70)

text = """Subtotal: $4,000.00
Discount: $200.00
Tax: $380.00
Total Amount Due: $4,180.00"""

print(text)
print()

print("subtotal =", extract_amount(text, ["subtotal"]))
print("discount =", extract_amount(text, ["discount"]))
print("tax =", extract_amount(text, ["tax"]))
print("total =", extract_amount(text, ["total amount due", "total amount"]))


print()
print("=" * 70)
print("TEST 2 - COMPLETE COMMERCIAL INVOICE")
print("=" * 70)

commercial_invoice = """COMMERCIAL INVOICE
Invoice No: INV-2026-4521
Invoice Date: 15/08/2026
Due Date: 30/08/2026
Seller: Global Trading Ltd
Bill To: ABC Restaurant Inc
Billing Address: Chicago, Illinois
Shipping Address: New York, USA
Subtotal: $4,000.00
Discount: $200.00
Tax: $380.00
Total Amount Due: $4,180.00
Currency: USD
Payment Terms: Net 15"""

print(commercial_invoice)
print()

result = extract_fields(
    "COMMERCIAL_INVOICE",
    commercial_invoice
)


print("EXTRACTION RESULT:")
print(result)