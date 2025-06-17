import io
from google.cloud import vision_v1 as vision
import re
import unicodedata
from PIL import Image

# Common reference list of Indian state and union territory names
INDIAN_STATES = ["ANDHRA PRADESH","ARUNACHAL PRADESH","ASSAM","BIHAR","CHHATTISGARH",
    "GOA","GUJARAT","HARYANA","HIMACHAL PRADESH","JHARKHAND","KARNATAKA","KERALA",
    "MADHYA PRADESH","MAHARASHTRA","MANIPUR","MEGHALAYA","MIZORAM","NAGALAND","ODISHA",
    "PUNJAB","RAJASTHAN","SIKKIM","TAMIL NADU","TELANGANA","TRIPURA","UTTAR PRADESH",
    "UTTARAKHAND","WEST BENGAL","ANDAMAN AND NICOBAR ISLANDS","CHANDIGARH","LAKSHADWEEP",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU","DELHI","LADAKH","PUDUCHERRY",
    "JAMMU AND KASHMIR" 
]

# Regex pattern to match any of the above state names as whole words
STATE_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in INDIAN_STATES) + r")\b",
    re.IGNORECASE,
)

def run_ocr(image_path: str) -> str:
    """
    Opens the image at `image_path`, calls Vision’s document_text_detection(),
    and returns the full-page text. Raises an exception if Vision returns an error.
    """
    client = vision.ImageAnnotatorClient()

    # Load the image bytes
    with io.open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    # Directly request DOCUMENT_TEXT_DETECTION (no need to build AnnotateImageRequest manually)
    response = client.document_text_detection(image=image)
    if response.error.message:
        # If Vision returned an error, propagate it
        raise RuntimeError(f"Vision API error: {response.error.message}")

    # Return the full detected text (or empty string if none)
    return (
        response.full_text_annotation.text
        if response.full_text_annotation and response.full_text_annotation.text
        else ""
    )


# def classify_category(text):
#     text = text.lower()

#     # Strong pattern for E-Way Bill — multiple keywords must exist
#     if (
#         ("eway bill" in text or "e-way bill" in text) and
#         "generated date" in text and
#         "vehicle" in text and
#         "quantity" in text
#         ):
#         return "E Way Bill"
#     elif "delivery challan" in text or "dc no" in text:
#         return "Delivery Challan"
#     elif "lr copy" in text or "lorry receipt" in text or "consignment note" in text:
#         return "LR Copy"
#     elif (
#         "weighbridge" in text or 
#         "nett wt" in text or "gross wt" in text or "tare wt" in text or
#         "total net weight" in text or "mwb madarsa" in text or
#         ("net" in text and "weight" in text)
#     ):
#         return "Weighbridge"
#     elif "tax invoice" in text or "invoice no" in text:
#         return "Tax Invoice"
#     return "Unknown"

def classify_category(raw_text: str) -> str:
    """
    Examines the entire OCR output (raw_text), normalizes it, and then
    returns one of:
      - "E Way Bill"
      - "Delivery Challan"
      - "LR Copy"
      - "Weighbridge"
      - "Tax Invoice"
      - "Unknown"
    """
    if not raw_text:
        return "Unknown"

    text_norm = normalize_ascii(raw_text)

    # 1) E-Way Bill: requires multiple distinct keywords
    if (
        ("eway bill" in text_norm or "e-way bill" in text_norm)
        and "generated date" in text_norm
        and "vehicle" in text_norm
        and "quantity" in text_norm
    ):
        return "E Way Bill"

    # 2) Delivery Challan
    if "delivery challan" in text_norm or "dc no" in text_norm:
        return "Delivery Challan"

    # 3) LR Copy / Lorry Receipt
    if "lr copy" in text_norm or "lorry receipt" in text_norm or "consignment note" in text_norm:
        return "LR Copy"

    # 4) Weighbridge: 
    #    • If the page has BOTH “gross wt” and “tare wt” (unique to weighbridge slips),
    #      OR if there is an explicit “weigh bridge” header (e.g. “ajanta weigh bridge”).
    #    • We deliberately do NOT rely on the generic “net wt” check,
    #      because “net weight” also appears on LR Copy and Tax Invoice.
    if (
        ("gross wt" in text_norm and "tare wt" in text_norm)
        or re.search(r"weigh\s*bridge", text_norm)
    ):
        return "Weighbridge"

    # 5) Tax Invoice
    if "tax invoice" in text_norm or "invoice no" in text_norm:
        return "Tax Invoice"

    return "Unknown"

# def normalize_ascii(text):
#     # Replace known OCR or non-ASCII issues first (before ASCII stripping)
#     replacements = {
#         'Το': 'To',   # Greek Tau + Omicron
#         'το': 'to',
#         ' T0': 'To',  # T-zero
#         ' t0': 'to',
#         ' Tо': 'To',  # Cyrillic o
#         ' tо': 'to',
#         'tο': 'to',   # mix of Latin t + Greek omicron
#         't o': 'to',
#     }

#     for wrong, right in replacements.items():
#         text = text.replace(wrong, right)

#     # Now normalize and strip accents
#     nfkd = unicodedata.normalize('NFKD', text)
#     only_ascii = nfkd.encode('ASCII', 'ignore').decode('utf-8')

#     return only_ascii.lower().strip()


def normalize_ascii(text: str) -> str:
    """
    1) Replace a few common OCR “look-alikes” (Greek/Cyrillic) for “to” or “To”.
    2) Strip out any remaining non-ASCII accents/characters.
    3) Lowercase + trim whitespace.
    """
    replacements = {
        'Το': 'To',   # Greek Tau + Omicron → Latin “To”
        'το': 'to',
        ' T0': 'To',  # T + zero → “To”
        ' t0': 'to',
        ' Tо': 'To',  # Cyrillic o → Latin “o”
        ' tо': 'to',
        'tο': 'to',   # mixed Latin ‘t’ + Greek omicron
        't o': 'to',
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    nfkd = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd.encode('ASCII', 'ignore').decode('utf-8')
    return only_ascii.lower().strip()


def extract_consignment_no_using_date_proximity(lines):
    # print("\n🔍 Smart Consignment No Extraction via proximity")

    date_index = -1
    # Step 1: locate the line containing the Date
    for i, line in enumerate(lines):
        if re.search(r"\bDATE[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", line):
            date_index = i
            print(f"📆 Found date line at {i}: '{line.strip()}'")
            break

    # Step 2: Look 5–6 lines above the date for a number that looks like LR No
    if date_index > 0:
        for j in range(date_index - 1, max(date_index - 10, -1), -1):
            if re.match(r"^\s*[0-9]{3,6}\s*$", lines[j].strip()):
                print(f"✅ Found consignment number at line {j}: '{lines[j].strip()}'")
                return lines[j].strip()

    # print("❌ Consignment number not found near DATE block")
    return "Not found"


def extract_consignor_consignee_blocks(lines):
    consignor, consignee = "Not found", "Not found"

    for i, line in enumerate(lines):
        if line.strip().lower() == "consignor" and i + 1 < len(lines):
            consignor = lines[i + 1].strip()

        elif line.strip().lower() == "consignee" and i + 1 < len(lines):
            consignee = lines[i + 1].strip()

    return consignor, consignee



def extract_states_from_blocks(lines):
    from_state, to_state = "Not found", "Not found"

    for i, line in enumerate(lines):
        clean_line = normalize_ascii(line)

        # print(f"🔍 At line {i}, cleaned line: '{clean_line}'")  # Log every line for debugging

        if clean_line == "from" and i + 2 < len(lines):
            # print(f"📍 Found 'From' at line {i}: {line.strip()}")
            # print(f"   Checking line {i+2} for state: {lines[i+2].strip()}")
            match = re.search(r"\(([^)]+)\)", lines[i + 2])
            if match:
                from_state = match.group(1).strip()

        elif re.fullmatch(r"to", clean_line.strip()) and i + 2 < len(lines):
            # print(f"📍 Found 'To' at line {i}: {line.strip()}")
            # print(f"   Checking line {i+2} for state: {lines[i+2].strip()}")
            match = re.search(r"\(([^)]+)\)", lines[i + 2])
            if match:
                to_state = match.group(1).strip()


    return from_state, to_state

def debug_print_lines(text, label="Debugging OCR Lines"):
    print(f"\n🔍 {label}")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        print(f"Line {i}: '{line.strip()}'")


def extract_material_name_from_lines(text):
    lines = text.splitlines()
    material = "Not found"
    material_keywords = ["plastic", "scrap", "bottle", "waste", "granule", "flake", "fiber", "film"]

    for i, line in enumerate(lines):
        clean = line.strip().lower()
        
        # Case 1: "1 Material Name" pattern
        match = re.match(r"^\d+\s+([A-Z\s\-]+)$", line.strip(), re.IGNORECASE)
        if match:
            possible = match.group(1).strip().title()
            if any(k in possible.lower() for k in material_keywords):
                return possible

        # Case 2: after 'Description of Goods'
        if "description of goods" in clean and i+1 < len(lines):
            next_line = lines[i+1].strip()
            if re.match(r"^\d+\s+[A-Z\s\-]+$", next_line, re.IGNORECASE):
                possible = " ".join(next_line.split()[1:]).strip().title()
                if any(k in possible.lower() for k in material_keywords):
                    return possible

        # Case 3: fallback loop to catch material-like content
        if any(k in clean for k in material_keywords) and len(clean) < 40:
            material = line.strip().title()

    return material

def extract_quantity_from_lines(text):
    lines = text.splitlines()
    quantity = "Not found"
    pattern = re.compile(r"(\d{1,3}(?:,\d{3})*(?:\.\d{1,3})?)\s*(KGS|KG|MT|TONS?)", re.IGNORECASE)

    candidates = []

    for i, line in enumerate(lines):
        if any(k in line.upper() for k in ["QUANTITY", "QTY", "KGS", "KG", "TONS", "MT"]):
            matches = pattern.findall(line)
            for match in matches:
                val, unit = match
                try:
                    float_val = float(val.replace(",", ""))
                    candidates.append((float_val, unit.upper()))
                except:
                    continue

        # Also check 2 lines after material (if we detect 'Description of Goods')
        if "description of goods" in line.lower() and i + 2 < len(lines):
            for offset in range(1, 3):
                nearby = lines[i + offset]
                matches = pattern.findall(nearby)
                for match in matches:
                    val, unit = match
                    try:
                        float_val = float(val.replace(",", ""))
                        candidates.append((float_val, unit.upper()))
                    except:
                        continue

    # Select best candidate
    if candidates:
        best = max(candidates, key=lambda x: x[0])
        quantity = f"{best[0]:,.3f} {best[1]}"

    return quantity


def extract_invoice_number_from_lines(text):
    lines = text.splitlines()
    invoice_number = "Not found"

    invoice_format = re.compile(r"\b[A-Z]{1,3}[-/]?\d{2,6}(?:[-/]\d{2,4})?\b", re.IGNORECASE)
    simple_number = re.compile(r"\b\d{3,6}\b")

    def looks_like_date(s):
        return re.search(r"\b(?:\d{1,2}[/-])?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[/-]?\d{2,4}\b", s, re.IGNORECASE)

    def is_noise(s):
        return any(x in s.lower() for x in ["eway", "gst", "phone", "dated", "bill no", "invoice date", "authorised", "sign", "amount"])

    # STEP 1: Look near "Invoice No."
    for i, line in enumerate(lines):
        if "invoice no" in normalize_ascii(line):
            for j in range(i + 1, min(i + 4, len(lines))):
                target = normalize_ascii(lines[j])
                if looks_like_date(target) or is_noise(target):
                    continue
                if invoice_format.search(target):
                    return invoice_format.search(target).group().strip()
                if simple_number.fullmatch(target.strip()):
                    return target.strip()

    # STEP 2: Check 'Dispatch Doc No.', 'Reference No.' as fallbacks
    for i, line in enumerate(lines):
        if "dispatch doc no" in normalize_ascii(line) or "reference no" in normalize_ascii(line):
            for j in range(i + 1, min(i + 3, len(lines))):
                val = normalize_ascii(lines[j]).strip()
                if simple_number.fullmatch(val) and not looks_like_date(val) and not is_noise(val):
                    return val

    # STEP 3: Full scan fallback
    for line in lines:
        norm = normalize_ascii(line)
        if is_noise(norm) or looks_like_date(norm):
            continue
        match = invoice_format.search(norm)
        if match:
            return match.group().strip()

    return invoice_number
