import re


DATE_PATTERN = (
    r"("
    r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    r"|"
    r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}"
    r"|"
    r"[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}"
    r")"
)


# ============================================================
# SUPPORTED DOCUMENT TYPES
# ============================================================

INVOICE_DOCUMENT_TYPES = {
    "INVOICE",
    "GST_INVOICE",
    "TAX_INVOICE",
    "E_INVOICE",
    "PROFORMA_INVOICE",
    "COMMERCIAL_INVOICE",
    "EXPORT_INVOICE",
    "IMPORT_INVOICE",
    "PURCHASE_INVOICE",
    "SALES_INVOICE",
    "SERVICE_INVOICE",
    "CREDIT_NOTE",
    "DEBIT_NOTE",
}


LOGISTICS_DOCUMENT_TYPES = {
    "POD",
    "LORRY_RECEIPT",
    "E_WAY_BILL",
    "DELIVERY_CHALLAN",
    "WAREHOUSE_DOCUMENT",
}


# ============================================================
# BASIC TEXT HELPERS
# ============================================================

def clean_value(
    value: str | None,
) -> str | None:
    """
    Clean an extracted value.
    """

    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    value = re.sub(
        r"[ \t]+",
        " ",
        value,
    )

    return value.strip()


def normalize_text(
    text: str,
) -> str:
    """
    Normalize OCR text while preserving line structure.
    """

    if not text:
        return ""

    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    lines = []

    for line in text.split("\n"):
        line = re.sub(
            r"[ \t]+",
            " ",
            line,
        )

        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def normalized_lower(
    text: str,
) -> str:
    """
    Return normalized lowercase text.
    """

    return normalize_text(text).lower()


def contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Safe phrase matching.
    """

    if not text or not phrase:
        return False

    text = normalized_lower(text)
    phrase = phrase.lower().strip()

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


# ============================================================
# GENERIC REGEX EXTRACTION
# ============================================================

def extract_by_patterns(
    text: str,
    patterns: list[str],
) -> str | None:
    """
    Try multiple regex patterns and return the first
    valid extracted value.
    """

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = clean_value(
                match.group(1)
            )

            if value:
                return value

    return None


# ============================================================
# INVOICE NUMBER
# ============================================================

def extract_invoice_number(
    text: str,
) -> str | None:
    """Extract an invoice number without confusing nearby date/label text."""
    if not text:
        return None

    lines = normalize_text(text).split("\n")
    invalid_values = {
        "DATE", "DUE", "TOTAL", "AMOUNT", "NO", "NUMBER",
        "ISSUE", "ISSUE DATE", "DUE DATE", "TERMS", "REFERENCE",
        "NAME", "BILL TO", "SHIP TO",
    }

    label_patterns = [
        r"^invoice\s*(?:number|no\.?|#)\s*[:#\-]?\s*(.*)$",
        r"^bill\s*(?:number|no\.?|#)\s*[:#\-]?\s*(.*)$",
    ]

    for i, line in enumerate(lines):
        clean_line = clean_value(line) or ""
        for pattern in label_patterns:
            match = re.match(pattern, clean_line, re.IGNORECASE)
            if not match:
                continue

            candidate = clean_value(match.group(1))
            if candidate and candidate.upper() not in invalid_values:
                if not re.fullmatch(DATE_PATTERN, candidate, re.IGNORECASE):
                    return candidate

            for nxt in lines[i + 1:i + 5]:
                candidate = clean_value(nxt)
                if not candidate:
                    continue
                if candidate.upper() in invalid_values:
                    continue
                if re.fullmatch(DATE_PATTERN, candidate, re.IGNORECASE):
                    continue
                if _is_metadata_line(candidate):
                    continue
                if re.fullmatch(
                    r"[A-Za-z0-9][A-Za-z0-9/_\-.]{2,}",
                    candidate,
                ) and re.search(r"\d", candidate):
                    return candidate

    # OCR may place the number directly after "Invoice".
    for line in lines:
        match = re.match(
            r"^invoice\s+([A-Za-z0-9][A-Za-z0-9/_\-.]{2,})$",
            line,
            re.IGNORECASE,
        )
        if match:
            candidate = match.group(1)
            if candidate.upper() not in invalid_values:
                return candidate

    # Last-resort fallback: reference numbers are often the invoice number.
    reference = extract_reference_number(text)
    if reference:
        return reference

    return None

def extract_date_after_labels(
    text: str,
    labels: list[str],
) -> str | None:

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    pattern = (
        rf"(?:{label_pattern})"
        rf"\s*[:#\-]?\s*"
        rf"{DATE_PATTERN}"
    )

    return extract_by_patterns(
        text,
        [pattern],
    )

def extract_invoice_date(
    text: str,
) -> str | None:
    """
    Extract invoice/document issue date.
    """

    return extract_date_after_labels(
        text,
        [
            "invoice date",
            "bill date",
            "issue date",
            "document date",
            "lr date",
            "lorry receipt date",
            "eway bill date",
            "e-way bill date",
            "challan date",
        ],
    )

def extract_due_date(
    text: str,
) -> str | None:

    return extract_date_after_labels(
        text,
        [
            "due date",
            "payment due",
            "payment due date",
        ],
    )


# ============================================================
# GSTIN
# ============================================================

def extract_gstin(
    text: str,
) -> str | None:

    pattern = (
        r"\b"
        r"\d{2}"
        r"[A-Z]{5}"
        r"\d{4}"
        r"[A-Z]"
        r"[A-Z0-9]"
        r"Z"
        r"[A-Z0-9]"
        r"\b"
    )

    match = re.search(
        pattern,
        text.upper(),
    )

    if match:
        return match.group(0)

    return None


def extract_seller_gstin(
    text: str,
) -> str | None:

    value = extract_by_patterns(
        text,
        [
            r"\bseller\s+gstin\s*[:#\-]?\s*([0-9A-Z]{15})",
            r"\bsupplier\s+gstin\s*[:#\-]?\s*([0-9A-Z]{15})",
            r"\bvendor\s+gstin\s*[:#\-]?\s*([0-9A-Z]{15})",
        ],
    )

    if value:
        return value.upper()

    return extract_gstin(text)


def extract_buyer_gstin(
    text: str,
) -> str | None:

    value = extract_by_patterns(
        text,
        [
            r"\bbuyer\s+gstin\s*[:#\-]?\s*([0-9A-Z]{15})",
            r"\bbuyer\s+gst\s*[:#\-]?\s*([0-9A-Z]{15})",
            r"\bconsignee\s+gstin\s*[:#\-]?\s*([0-9A-Z]{15})",
        ],
    )

    if value:
        return value.upper()

    return None


# ============================================================
# PAN
# ============================================================

def extract_pan(
    text: str,
) -> str | None:

    pattern = r"\b[A-Z]{5}\d{4}[A-Z]\b"

    match = re.search(
        pattern,
        text.upper(),
    )

    if match:
        return match.group(0)

    return None


def extract_seller_pan(
    text: str,
) -> str | None:

    value = extract_by_patterns(
        text,
        [
            r"\bseller\s+pan\s*[:#\-]?\s*([A-Z]{5}\d{4}[A-Z])",
            r"\bsupplier\s+pan\s*[:#\-]?\s*([A-Z]{5}\d{4}[A-Z])",
        ],
    )

    if value:
        return value.upper()

    return None


def extract_buyer_pan(
    text: str,
) -> str | None:

    value = extract_by_patterns(
        text,
        [
            r"\bbuyer\s+pan\s*[:#\-]?\s*([A-Z]{5}\d{4}[A-Z])",
            r"\bcustomer\s+pan\s*[:#\-]?\s*([A-Z]{5}\d{4}[A-Z])",
        ],
    )

    if value:
        return value.upper()

    return None


# ============================================================
# SELLER / BUYER
# ============================================================

def extract_buyer_name(text: str) -> str | None:
    """Extract buyer/customer/consignee name without returning section labels."""
    lines = normalize_text(text).split("\n")
    explicit = [
        r"^\s*(?:customer\s+name|buyer\s+name)\s*[:#\-]\s*(.+)$",
        r"^\s*(?:customer|buyer)\s*[:#\-]\s*(.+)$",
        r"^\s*consignee\s*[:#\-]\s*(.+)$",
        r"^\s*billed\s+to\s*[:#\-]\s*(.+)$",
    ]
    for line in lines:
        for pattern in explicit:
            m=re.match(pattern,line,re.I)
            if m:
                v=clean_value(m.group(1))
                if v and v.lower() not in {"bill to","ship to"} and not _is_metadata_line(v): return v
    for i,line in enumerate(lines):
        if line.lower().strip()=="bill to":
            j=i+1
            if j<len(lines) and lines[j].lower().strip()=="ship to": j+=1
            if j<len(lines):
                v=clean_value(lines[j])
                if v and not _is_metadata_line(v): return v
    for i,line in enumerate(lines):
        if line.lower().strip() in {"bill to","billed to","customer","buyer","consignee"}:
            for nxt in lines[i+1:i+4]:
                v=clean_value(nxt)
                if v and v.lower() not in {"bill to","ship to"} and not _is_metadata_line(v): return v
    return None


def _is_metadata_line(value: str) -> bool:
    lower=value.lower().strip()
    return lower in {"invoice","invoice no.","invoice number","invoice date","due date","terms","reference","bill to","ship to","item & description","qty","rate","amount","subtotal","sub total","tax","tax rate","total","balance due","terms & conditions"}

def extract_seller_name(
    text: str,
) -> str | None:
    """
    Extract seller/supplier/vendor name.

    Uses explicit labels first.

    If no explicit seller label exists, attempts to identify
    the company name from the document header while avoiding
    known invoice metadata fields.
    """

    patterns = [
        r"\bseller\s+name\s*[:\-]?\s*([^\n]+)",
        r"\bsupplier\s+name\s*[:\-]?\s*([^\n]+)",
        r"\bvendor\s+name\s*[:\-]?\s*([^\n]+)",
        r"\bbilled\s+by\s*[:\-]?\s*([^\n]+)",
        r"\bseller\s*[:\-]\s*([^\n]+)",
        r"\bsupplier\s*[:\-]\s*([^\n]+)",
        r"\bvendor\s*[:\-]\s*([^\n]+)",
        r"\bfrom\s*[:\-]\s*([^\n]+)",
    ]

    value = extract_by_patterns(
        text,
        patterns,
    )

    if value:
        return value

    # --------------------------------------------------------
    # Header-based fallback
    # --------------------------------------------------------

    lines = normalize_text(
        text
    ).split("\n")

    ignored_exact = {
    "invoice",
    "tax invoice",
    "gst invoice",
    "gst tax invoice",
    "commercial invoice",
    "proforma invoice",
    "pro forma invoice",
    "sales invoice",
    "purchase invoice",
    "service invoice",
    "export invoice",
    "import invoice",
    "restaurant invoice",
    "retail invoice",
    "retail bill",
    "sales bill",
    "purchase bill",
    "service bill",
    "bill to",
    "ship to",
    }

    ignored_prefixes = (
        "gstin:",
        "gstin ",
        "invoice no",
        "invoice number",
        "invoice date",
        "bill date",
        "issue date",
        "due date",
        "reference:",
        "reference ",
        "ref:",
        "ref ",
        "po number",
        "po no",
        "payment terms",
        "subtotal",
        "discount",
        "tax",
        "cgst",
        "sgst",
        "igst",
        "vat",
        "total",
        "amount due",
        "total amount",
    )

    # Look at the first several meaningful lines.
    for line in lines[:8]:

        candidate = clean_value(
        line
        )

        if not candidate:
            continue

        lower_candidate = candidate.lower()

        if (
        " invoice" in lower_candidate
        or lower_candidate.endswith(" invoice")
        or lower_candidate.startswith("invoice ")
        ):
            continue

        if lower_candidate in ignored_exact:
            continue

        if any(
        lower_candidate.startswith(prefix)
        for prefix in ignored_prefixes
        ):
            continue
        
        # Avoid selecting obvious metadata/date lines.
        if re.search(
            r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",
            candidate,
        ):
            continue

        # Avoid selecting lines that are clearly identifiers.
        if re.fullmatch(
            r"[A-Z0-9]{15}",
            candidate.upper(),
        ):
            continue

        # A reasonable company/person name candidate.
        if len(candidate) >= 3:
            return candidate

    return None

# ============================================================
# ADDRESS
# ============================================================

def extract_address_after_label(
    text: str,
    labels: list[str],
) -> str | None:

    lines = normalize_text(text).split("\n")

    label_set = {
        label.lower()
        for label in labels
    }

    for index, line in enumerate(lines):

        lower_line = line.lower().strip()

        matched = False

        for label in label_set:
            if lower_line.startswith(label):
                matched = True
                break

        if not matched:
            continue

        # Address on same line after colon.
        if ":" in line:
            after_colon = line.split(
                ":",
                1,
            )[1].strip()

            if after_colon:
                return after_colon

        # Otherwise collect the next one or two lines.
        values = []

        for next_index in range(
            index + 1,
            min(index + 3, len(lines)),
        ):
            candidate = clean_value(
                lines[next_index]
            )

            if not candidate:
                continue

            if candidate.lower() in {
                "invoice",
                "invoice no.",
                "invoice number",
                "date",
                "due date",
            }:
                break

            values.append(candidate)

        if values:
            return ", ".join(values)

    return None


def extract_billing_address(text: str) -> str | None:
    """Extract billing address, including flattened two-column OCR."""
    lines=normalize_text(text).split("\n")
    value=extract_address_after_label(text,["billing address","bill to address"])
    if value: return value
    for i,line in enumerate(lines):
        if line.lower().strip()=="bill to" and i+1<len(lines) and lines[i+1].lower().strip()=="ship to":
            return _extract_flattened_address(lines,i+2)
    return None

def extract_shipping_address(text: str) -> str | None:
    """Extract shipping address, including flattened two-column OCR."""
    lines=normalize_text(text).split("\n")
    value=extract_address_after_label(text,["shipping address","ship to address","delivery address"])
    if value: return value
    for i,line in enumerate(lines):
        if line.lower().strip()=="bill to" and i+1<len(lines) and lines[i+1].lower().strip()=="ship to":
            return _extract_flattened_address(lines,i+2)
    return None


def _extract_flattened_address(lines: list[str], start: int) -> str | None:
    values=[]
    stop={"#","item & description","qty","rate","amount","subtotal","sub total","tax rate","tax","total","balance due","terms & conditions"}
    for line in lines[start:start+10]:
        v=clean_value(line)
        if not v: continue
        low=v.lower()
        if low in stop: break
        if _is_metadata_line(v): continue
        if v not in values: values.append(v)
    buyer=extract_buyer_name("\n".join(lines))
    if buyer and values and values[0].lower()==buyer.lower(): values=values[1:]
    return ", ".join(values[:5]) if values else None

# ============================================================

# REFERENCES
# ============================================================

def extract_po_number(text: str) -> str | None:
    """Extract PO only when an explicit PO/purchase-order label is present."""
    lines=normalize_text(text).split("\n")
    same_line=[
        r"^\s*po\s*(?:number|no\.?|#)\s*[:#\-]\s*([A-Z0-9][A-Z0-9/_\-.]{2,})\s*$",
        r"^\s*purchase\s+order\s*(?:number|no\.?|#)\s*[:#\-]\s*([A-Z0-9][A-Z0-9/_\-.]{2,})\s*$",
        r"^\s*(?:po|purchase\s+order)\s*[:#]\s*([A-Z0-9][A-Z0-9/_\-.]{2,})\s*$",
    ]
    for line in lines:
        for pat in same_line:
            m=re.match(pat,line,re.I)
            if m:
                v=clean_value(m.group(1))
                if v and v.upper() not in {"NUMBER","NO","DATE","TOTAL","AMOUNT"}: return v
    label=re.compile(r"^\s*(?:po\s*(?:number|no\.?|#)?|purchase\s+order\s*(?:number|no\.?|#)?)\s*[:#\-]?\s*$",re.I)
    for i,line in enumerate(lines[:-1]):
        if label.match(line):
            v=clean_value(lines[i+1])
            if v and not _is_metadata_line(v) and re.fullmatch(r"[A-Z0-9][A-Z0-9/_\-.]{2,}",v,re.I): return v
    return None

def extract_reference_number(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\breference\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9/_\-.]{2,})",
            r"\bref\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9/_\-.]{2,})",
        ],
    )


# ============================================================
# CURRENCY
# ============================================================

def extract_currency(text: str) -> str | None:
    """Extract an explicit currency code or common currency symbol."""
    if not text:
        return None

    explicit_patterns = [
        (r"\bINR\b", "INR"), (r"\bUSD\b", "USD"),
        (r"\bEUR\b", "EUR"), (r"\bGBP\b", "GBP"),
        (r"\bAUD\b", "AUD"), (r"\bCAD\b", "CAD"),
        (r"\bSGD\b", "SGD"), (r"\bAED\b", "AED"),
        (r"\bNZD\b", "NZD"), (r"\bJPY\b", "JPY"),
    ]
    for pattern, currency in explicit_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return currency

    symbol_patterns = [
        (r"₹|â‚¹", "INR"), (r"\$", "USD"),
        (r"€|â‚¬", "EUR"), (r"£|Â£", "GBP"),
    ]
    for pattern, currency in symbol_patterns:
        if re.search(pattern, text):
            return currency

    return None

def _extract_money_value(value: str | None) -> str | None:
    """Extract a numeric amount from one OCR line."""
    if not value:
        return None
    value = clean_value(value)
    if not value:
        return None
    match = re.fullmatch(
        rf"(?:[$€£₹]|â‚¹|â‚¬|Â£)?\s*([\d][\d,]*(?:\.\d{{1,2}})?)",
        value,
        re.IGNORECASE,
    )
    return clean_value(match.group(1)) if match else None


def _label_matches_line(line: str, label: str) -> bool:
    """Match a label while allowing OCR punctuation and currency suffixes."""
    normalized_line = re.sub(
        r"\s+", " ", (clean_value(line) or "").lower()
    ).strip()
    normalized_label = re.sub(
        r"\s+", " ", (clean_value(label) or "").lower()
    ).strip()

    if normalized_line == normalized_label:
        return True

    line_base = re.sub(r"[:#\-]+$", "", normalized_line).strip()
    label_base = re.sub(r"[:#\-]+$", "", normalized_label).strip()

    if line_base == label_base:
        return True

    # Example: "Total (AUD):" should match label "total".
    if re.fullmatch(
        rf"{re.escape(label_base)}(?:\s*\([a-z]{{3}}\))?",
        line_base,
        re.IGNORECASE,
    ):
        return True

    return False

MONEY_VALUE_PATTERN = r"(?:[$€£₹]|â‚¹|â‚¬|Â£)?\s*([\d][\d,]*(?:\.\d{1,2})?)"


def extract_amount(text: str, labels: list[str]) -> str | None:
    """Extract a monetary value from a label on the same or nearby OCR line."""
    if not text or not labels:
        return None

    lines = normalize_text(text).split("\n")
    ordered_labels = sorted(labels, key=len, reverse=True)

    for index, line in enumerate(lines):
        clean_line = clean_value(line) or ""

        # Same-line: "Subtotal: $2,100.00"
        for label in ordered_labels:
            match = re.match(
                rf"^\s*{re.escape(label)}"
                rf"(?:\s*\([A-Z]{{3}}\))?"
                rf"\s*[:#\-]?\s*{MONEY_VALUE_PATTERN}\s*$",
                clean_line,
                re.IGNORECASE,
            )
            if match:
                return clean_value(match.group(1))

        # Separate-line: "Subtotal:" / "$2,100.00"
        if any(_label_matches_line(clean_line, label) for label in ordered_labels):
            for next_index in range(index + 1, min(index + 4, len(lines))):
                candidate = clean_value(lines[next_index])
                if not candidate:
                    continue

                amount = _extract_money_value(candidate)
                if amount:
                    return amount

                if _is_metadata_line(candidate):
                    break

    return None

def extract_subtotal(text: str) -> str | None:
    return extract_amount(text, ["subtotal", "sub total"])


def extract_discount(text: str) -> str | None:
    return extract_amount(text, ["discount amount", "discount"])


def extract_tax(text: str) -> str | None:
    """Extract directly stated tax amounts, including multiple GST/VAT lines."""
    if not text:
        return None

    lines = normalize_text(text).split("\n")
    amounts = []

    # Explicit generic tax labels.
    generic = extract_amount(text, ["tax amount", "tax", "vat"])
    if generic:
        return generic

    # GST/VAT lines such as:
    # GST 10% from $100.00
    # $10.00
    for i, line in enumerate(lines):
        clean_line = clean_value(line) or ""
        if not re.search(r"\b(?:gst|vat|sales\s+tax)\b", clean_line, re.IGNORECASE):
            continue

        for nxt in lines[i + 1:i + 3]:
            amount = _extract_money_value(clean_value(nxt))
            if amount:
                amounts.append(amount)
                break

    if not amounts:
        return None

    total = sum(_parse_amount(value) or 0 for value in amounts)
    return f"{total:.2f}"

def extract_cgst(text: str) -> str | None:
    return extract_amount(text, ["cgst amount", "cgst"])


def extract_sgst(text: str) -> str | None:
    return extract_amount(text, ["sgst amount", "sgst"])


def extract_igst(text: str) -> str | None:
    return extract_amount(text, ["igst amount", "igst"])


def extract_vat(text: str) -> str | None:
    return extract_amount(text, ["vat amount", "vat"])


def extract_total_amount(text: str) -> str | None:
    """Extract actual total; exact label matching prevents Sub Total confusion."""
    return extract_amount(
        text,
        ["total amount due", "grand total", "net payable", "amount due", "total due", "balance due", "total"],
    )


# ============================================================
# TAX RATE / DERIVED TAX
# ============================================================

def extract_tax_rate(text: str) -> str | None:
    """Extract one or more tax rates from common invoice tax descriptions."""
    if not text:
        return None

    lines = normalize_text(text).split("\n")
    rates = []

    for i, line in enumerate(lines):
        clean_line = clean_value(line) or ""

        match = re.match(
            r"^tax\s+rate\s*[:#\-]?\s*(\d+(?:\.\d+)?)\s*%$",
            clean_line,
            re.IGNORECASE,
        )
        if match:
            rates.append(f"{match.group(1)}%")
            continue

        if clean_line.lower() == "tax rate":
            for nxt in lines[i + 1:i + 4]:
                value = clean_value(nxt)
                rate_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", value or "")
                if rate_match:
                    rates.append(f"{rate_match.group(1)}%")
                    break

        for rate_match in re.finditer(
            r"\b(?:gst|vat|sales\s+tax|tax)\s*"
            r"(\d+(?:\.\d+)?)\s*%",
            clean_line,
            re.IGNORECASE,
        ):
            rates.append(f"{rate_match.group(1)}%")

    unique_rates = list(dict.fromkeys(rates))
    return ", ".join(unique_rates) if unique_rates else None

def _parse_amount(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.]", "", value)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def calculate_tax_from_rate(subtotal: str | None, tax_rate: str | None) -> str | None:
    """Calculate tax only when both subtotal and tax rate are available."""
    base = _parse_amount(subtotal)
    if base is None or not tax_rate:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", tax_rate)
    if not match:
        return None
    return f"{base * float(match.group(1)) / 100:.2f}"


# ============================================================
# PAYMENT TERMS
# ============================================================

def extract_payment_terms(text: str) -> str | None:
    patterns = [
        r"\bpayment\s+terms?\s*[:\-]?\s*([^\n]+)",
        r"\bterms?\s+of\s+payment\s*[:\-]?\s*([^\n]+)",
        r"\bpayment\s+condition\s*[:\-]?\s*([^\n]+)",
    ]
    return extract_by_patterns(text, patterns)


# ============================================================
# LOGISTICS CONTEXT
# ============================================================

LOGISTICS_CONTEXT_KEYWORDS = {
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
}


def detect_logistics_context(
    document_type: str,
    text: str,
) -> bool:
    """
    Determine whether logistics extraction should run.

    Logistics document types automatically qualify.

    Invoices require meaningful logistics context.
    """

    if document_type in LOGISTICS_DOCUMENT_TYPES:
        return True

    if document_type not in INVOICE_DOCUMENT_TYPES:
        return False

    matched_count = 0

    for keyword in LOGISTICS_CONTEXT_KEYWORDS:

        if contains_phrase(
            text,
            keyword,
        ):
            matched_count += 1

    # Two logistics indicators provide reasonable
    # context for logistics-specific extraction.
    return matched_count >= 2


# ============================================================
# LOGISTICS FIELD EXTRACTION
# ============================================================

def extract_lr_number(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\blr\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9/_\-.]{2,})",
            r"\blorry\s+receipt\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9/_\-.]{2,})",
        ],
    )


def extract_vehicle_number(
    text: str,
) -> str | None:

    pattern = (
        r"\b"
        r"(?:vehicle\s*(?:number|no\.?)?|truck\s*(?:number|no\.?)?)"
        r"\s*[:#\-]?\s*"
        r"([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,3}\s*\d{3,4})"
    )

    value = extract_by_patterns(
        text,
        [pattern],
    )

    if value:
        return re.sub(
            r"\s+",
            "",
            value.upper(),
        )

    # Fallback for standard Indian vehicle format.
    match = re.search(
        r"\b[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,4}\b",
        text.upper(),
    )

    if match:
        return match.group(0)

    return None


def extract_consignor(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\bconsignor\s*[:\-]?\s*([^\n]+)",
            r"\bshipper\s*[:\-]?\s*([^\n]+)",
        ],
    )


def extract_consignee(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\bconsignee\s*[:\-]?\s*([^\n]+)",
            r"\breceiver\s*[:\-]?\s*([^\n]+)",
        ],
    )


def extract_carrier(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\bcarrier\s*[:\-]?\s*([^\n]+)",
            r"\btransporter\s*[:\-]?\s*([^\n]+)",
            r"\blogistics\s+provider\s*[:\-]?\s*([^\n]+)",
        ],
    )


def extract_tracking_number(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\btracking\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9/_\-.]{4,})",
            r"\btracking\s+id\s*[:#\-]?\s*([A-Z0-9/_\-.]{4,})",
        ],
    )


def extract_shipment_number(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\bshipment\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9/_\-.]{3,})",
            r"\bshipment\s+id\s*[:#\-]?\s*([A-Z0-9/_\-.]{3,})",
        ],
    )


def extract_eway_bill_number(
    text: str,
) -> str | None:

    return extract_by_patterns(
        text,
        [
            r"\be[\-\s]?way\s+bill\s*(?:number|no\.?|#)?\s*[:#\-]?\s*(\d{8,20})",
        ],
    )


def extract_delivery_date(
    text: str,
) -> str | None:

    return extract_date_after_labels(
        text,
        [
            "delivery date",
            "delivered date",
        ],
    )


# ============================================================
# FIELD CONFIDENCE
# ============================================================

def calculate_field_confidence(
    fields: dict,
) -> dict:
    """
    Assign a basic confidence score to each extracted field.

    This is an extraction-confidence estimate, not an OCR
    probability. Later this can be replaced by model-level
    confidence from the OCR/NER engine.
    """

    confidence = {}

    for field_name, value in fields.items():

        if value is None:
            confidence[field_name] = 0

        elif isinstance(value, str):

            length = len(value.strip())

            if length >= 5:
                confidence[field_name] = 90
            else:
                confidence[field_name] = 75

        else:
            confidence[field_name] = 70

    return confidence


# ============================================================
# EXTRACTION COMPLETENESS
# ============================================================

def calculate_extraction_completeness(
    fields: dict,
    document_type: str,
) -> int:
    """
    Calculate how many expected fields were successfully
    extracted.

    This is not document quality.

    It measures extraction completeness only.
    """

    if document_type in INVOICE_DOCUMENT_TYPES:

        required_fields = [
            "invoice_number",
            "invoice_date",
            "seller_name",
            "buyer_name",
            "subtotal",
            "tax",
            "total_amount",
        ]

    elif document_type == "POD":

        required_fields = [
            "delivery_date",
            "consignee",
        ]

    elif document_type == "LORRY_RECEIPT":

        required_fields = [
            "lr_number",
            "consignor",
            "consignee",
            "vehicle_number",
        ]

    elif document_type == "E_WAY_BILL":

        required_fields = [
            "eway_bill_number",
            "consignor",
            "consignee",
            "vehicle_number",
        ]

    else:

        required_fields = []

    if not required_fields:
        return 0

    extracted_count = 0

    for field_name in required_fields:
        if field_name == "tax":
            # A tax amount may be directly extracted or calculated from
            # an explicit tax rate when the invoice does not print the
            # tax amount separately.
            if fields.get("tax") or fields.get("calculated_tax") or fields.get("tax_rate"):
                extracted_count += 1
        elif fields.get(field_name):
            extracted_count += 1

    return round(
        extracted_count
        / len(required_fields)
        * 100
    )


# ============================================================
# UNIVERSAL INVOICE EXTRACTION
# ============================================================

def extract_invoice_fields(text: str) -> dict:
    """Extract invoice fields with conservative tax handling."""
    subtotal=extract_subtotal(text)
    tax=extract_tax(text)
    tax_rate=extract_tax_rate(text)
    calculated_tax=calculate_tax_from_rate(subtotal,tax_rate) if tax is None else None
    return {
        "invoice_number": extract_invoice_number(text),
        "invoice_date": extract_invoice_date(text),
        "due_date": extract_due_date(text),
        "seller_name": extract_seller_name(text),
        "buyer_name": extract_buyer_name(text),
        "billing_address": extract_billing_address(text),
        "shipping_address": extract_shipping_address(text),
        "seller_gstin": extract_seller_gstin(text),
        "buyer_gstin": extract_buyer_gstin(text),
        "seller_pan": extract_seller_pan(text),
        "buyer_pan": extract_buyer_pan(text),
        "po_number": extract_po_number(text),
        "reference_number": extract_reference_number(text),
        "currency": extract_currency(text),
        "subtotal": subtotal,
        "discount": extract_discount(text),
        "tax": tax,
        "tax_rate": tax_rate,
        "calculated_tax": calculated_tax,
        "cgst": extract_cgst(text),
        "sgst": extract_sgst(text),
        "igst": extract_igst(text),
        "vat": extract_vat(text),
        "total_amount": extract_total_amount(text),
        "payment_terms": extract_payment_terms(text),
    }

# ============================================================
# LOGISTICS EXTRACTION
# ============================================================

def extract_logistics_fields(
    text: str,
) -> dict:

    return {
        "lr_number": extract_lr_number(text),
        "vehicle_number": extract_vehicle_number(text),
        "consignor": extract_consignor(text),
        "consignee": extract_consignee(text),
        "carrier": extract_carrier(text),
        "tracking_number": extract_tracking_number(text),
        "shipment_number": extract_shipment_number(text),
        "eway_bill_number": extract_eway_bill_number(text),
        "delivery_date": extract_delivery_date(text),
    }


# ============================================================
# DOCUMENT-SPECIFIC EXTRACTION
# ============================================================

def extract_non_invoice_fields(
    document_type: str,
    text: str,
) -> dict:

    if document_type == "POD":

        return {
            "delivery_date": extract_delivery_date(text),
            "consignee": extract_consignee(text),
            "receiver_name": extract_buyer_name(text),
        }

    if document_type == "LORRY_RECEIPT":

        return {
            "lr_number": extract_lr_number(text),
            "lr_date": extract_invoice_date(text),
            "consignor": extract_consignor(text),
            "consignee": extract_consignee(text),
            "vehicle_number": extract_vehicle_number(text),
            "carrier": extract_carrier(text),
        }

    if document_type == "E_WAY_BILL":

        return {
            "eway_bill_number": extract_eway_bill_number(text),
            "eway_bill_date": extract_invoice_date(text),
            "consignor": extract_consignor(text),
            "consignee": extract_consignee(text),
            "vehicle_number": extract_vehicle_number(text),
        }

    if document_type == "DELIVERY_CHALLAN":

        return {
            "challan_number": extract_by_patterns(
                text,
                [
                    r"\bchallan\s*(?:number|no\.?|#)?\s*[:#\-]?\s*([A-Z0-9/_\-.]{3,})",
                ],
            ),
            "challan_date": extract_invoice_date(text),
            "consignor": extract_consignor(text),
            "consignee": extract_consignee(text),
        }

    if document_type == "WAREHOUSE_DOCUMENT":

        return {
            "document_number": extract_by_patterns(
                text,
                [
                    r"\bdocument\s*(?:number|no\.?|#)\s*[:#\-]?\s*([A-Z0-9/_\-.]{3,})",
                ],
            ),
            "document_date": extract_invoice_date(text),
            "warehouse_name": extract_by_patterns(
                text,
                [
                    r"\bwarehouse\s*(?:name)?\s*[:\-]?\s*([^\n]+)",
                ],
            ),
        }

    return {}


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_fields(
    document_type: str,
    extracted_text: str,
) -> dict:
    """
    Main document field extraction entry point.

    Returns:

        success
        fields
        logistics_fields
        field_confidence
        extraction_confidence
        extraction_completeness
        logistics_context
        reason
    """

    if not extracted_text or not extracted_text.strip():

        return {
            "success": False,
            "fields": {},
            "logistics_fields": {},
            "field_confidence": {},
            "extraction_confidence": 0,
            "extraction_completeness": 0,
            "logistics_context": False,
            "reason": (
                "No OCR text available "
                "for field extraction"
            ),
        }

    text = normalize_text(
        extracted_text
    )

    # --------------------------------------------------------
    # Universal invoice extraction
    # --------------------------------------------------------

    if document_type in INVOICE_DOCUMENT_TYPES:

        fields = extract_invoice_fields(
            text
        )

    else:

        fields = extract_non_invoice_fields(
            document_type,
            text,
        )

    # --------------------------------------------------------
    # Logistics context
    # --------------------------------------------------------

    logistics_context = detect_logistics_context(
        document_type,
        text,
    )

    # --------------------------------------------------------
    # Logistics fields
    # --------------------------------------------------------

    if logistics_context:

        logistics_fields = extract_logistics_fields(
            text
        )

    else:

        logistics_fields = {}

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    field_confidence = {}

    field_confidence.update(
        calculate_field_confidence(
            fields
        )
    )

    for field_name, value in logistics_fields.items():

        if value is None:
            field_confidence[
                field_name
            ] = 0

        else:
            field_confidence[
                field_name
            ] = 90

    # --------------------------------------------------------
    # Completeness
    # --------------------------------------------------------

    extraction_completeness = (
        calculate_extraction_completeness(
            fields,
            document_type,
        )
    )

    # --------------------------------------------------------
    # Overall extraction confidence
    # --------------------------------------------------------

    extracted_values = [
        confidence
        for confidence in field_confidence.values()
        if confidence > 0
    ]

    if extracted_values:

        extraction_confidence = round(
            sum(extracted_values)
            / len(extracted_values)
        )

    else:

        extraction_confidence = 0

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    extracted_count = sum(
        1
        for value in (
            list(fields.values())
            + list(logistics_fields.values())
        )
        if value
    )

    if extracted_count == 0:

        reason = (
            "Document classified successfully, "
            "but no structured fields could be extracted"
        )

    else:

        reason = (
            f"Extracted {extracted_count} "
            f"structured field(s)"
        )

    return {
        "success": True,
        "fields": fields,
        "logistics_fields": logistics_fields,
        "field_confidence": field_confidence,
        "extraction_confidence": extraction_confidence,
        "extraction_completeness": extraction_completeness,
        "logistics_context": logistics_context,
        "reason": reason,
    }