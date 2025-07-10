import io
import re
import unicodedata
from google.cloud import vision_v1 as vision

# List of Indian states/UTs for state matching
INDIAN_STATES = [
    "ANDHRA PRADESH","ARUNACHAL PRADESH","ASSAM","BIHAR","CHHATTISGARH",
    "GOA","GUJARAT","HARYANA","HIMACHAL PRADESH","JHARKHAND","KARNATAKA","KERALA",
    "MADHYA PRADESH","MAHARASHTRA","MANIPUR","MEGHALAYA","MIZORAM","NAGALAND","ODISHA",
    "PUNJAB","RAJASTHAN","SIKKIM","TAMIL NADU","TELANGANA","TRIPURA","UTTAR PRADESH",
    "UTTARAKHAND","WEST BENGAL","ANDAMAN AND NICOBAR ISLANDS","CHANDIGARH","LAKSHADWEEP",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU","DELHI","LADAKH","PUDUCHERRY",
    "JAMMU AND KASHMIR" 
]

STATE_REGEX = re.compile(
    r"\\b(" + "|".join(re.escape(s) for s in INDIAN_STATES) + r")\\b",
    re.IGNORECASE,
)

def run_ocr(image_path: str) -> str:
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")
    return response.full_text_annotation.text if response.full_text_annotation else ""

def classify_category(text: str) -> str:
    if not text:
        return "Unknown"
    text_norm = normalize_ascii(text)

    # ───── Weighbridge ─────
    if (
        ("gross" in text_norm and "tare" in text_norm and "net" in text_norm)
        or "weighbridge" in text_norm
        or "bridge weigh" in text_norm
        or "gross wt" in text_norm
        or "tare wt" in text_norm
        or re.search(r"weigh\s*bridge", text_norm)
    ):
        return "Weighbridge"

    # ───── E-Way Bill ─────
    if (
        ("eway bill" in text_norm or "e-way bill" in text_norm)
        and "generated date" in text_norm
        and "vehicle" in text_norm
        and ("quantity" in text_norm or "qty" in text_norm)
    ):
        return "E Way Bill"

    # ───── Delivery Challan ─────
    if (
        "delivery challan" in text_norm
        or re.search(r"\bdc[\s\-]?no\b", text_norm)
        or ("challan no" in text_norm and "delivery" in text_norm)
    ):
        return "Delivery Challan"

    # ───── LR Copy / Consignment Note ─────
    if (
        "lr copy" in text_norm
        or "lorry receipt" in text_norm
        or "consignment note" in text_norm
        or ("consignor" in text_norm and "consignee" in text_norm)
    ):
        return "LR Copy"

    # ───── Tax Invoice ─────
    if (
        ("tax invoice" in text_norm or re.search(r"invoice[\s\-]?no", text_norm))
        and ("gst" in text_norm or "total" in text_norm or "cgst" in text_norm or "sgst" in text_norm)
        and not any(term in text_norm for term in ["consignor", "consignee", "lr copy", "lorry receipt", "consignment note"])
    ):
        return "Tax Invoice"

    # ───── Fallback ─────
    import logging
    logger = logging.getLogger("ocr_backend")
    logger.warning("❌ Could not classify document. Normalized OCR content:\n" + text_norm[:500])
    return "Unknown"



def normalize_ascii(text: str) -> str:
    replacements = {
        'Το': 'To', 'το': 'to', ' T0': 'To', ' t0': 'to',
        ' Tо': 'To', ' tо': 'to', 'tο': 'to', 't o': 'to',
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def debug_print_lines(text, label="Debugging OCR Lines"):
    print(f"\n🔍 {label}")
    for i, line in enumerate(text.splitlines()):
        print(f"Line {i}: '{line.strip()}'")
