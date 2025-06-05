import re
from ocr_utils import normalize_ascii, debug_print_lines, STATE_REGEX

def extract_eway_bill_fields(text):
    print("\n🧾 Processing: E-Way Bill")
    lines = text.splitlines()
    # debug_print_lines(text, "E-Way Bill: Line-by-Line OCR Output")
    result = {"Category": "E Way Bill"}

    def find(pattern, flags=re.IGNORECASE):
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else "Not found"

    # Vehicle Number: Look for exact pattern across lines
    vehicle_number = "Not found"
    for line in lines:
        match = re.search(r"\b([A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4})\b", line)
        if match:
            vehicle_number = match.group(1)
            break
    result["Vehicle Number"] = vehicle_number


    # E-Way Bill No.: Look for 12–15 digit number near "Transporter Doc" or in general
    eway_no = "Not found"
    for i, line in enumerate(lines):
        if "eway bill" in line.lower() or "transporter doc" in line.lower():
            for j in range(i, i + 3):
                if j < len(lines):
                    match = re.search(r"\b\d{10,15}\b", lines[j])
                    if match:
                        eway_no = match.group()
                        break
        if eway_no != "Not found":
            break
    result["No."] = eway_no


    # 3️⃣ Generated & Valid Dates
    result["Generated Date"] = find(r"Generated\s+Date[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
    result["Valid Upto"] = find(r"Valid\s+Upto[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")

    # Quantity: Search after 'Quantity' label with flexible distance and unit parsing
    qty = "Not found"
    for i, line in enumerate(lines):
        if "quantity" in line.lower():
            # Look ahead up to 5 lines for value and unit
            for j in range(i + 1, min(i + 6, len(lines))):
                num_match = re.search(r"\b\d{3,6}(?:\.\d+)?\b", lines[j])
                unit_match = re.search(r"\b(KGS|KG|MT|TONS?)\b", lines[j], re.IGNORECASE)

                # If value is in one line and unit in next, combine them
                if num_match and j + 1 < len(lines):
                    unit_next = re.search(r"\b(KGS|KG|MT|TONS?)\b", lines[j + 1], re.IGNORECASE)
                    if unit_next:
                        qty = f"{float(num_match.group()):,.2f} {unit_next.group().upper()}"
                        break

                if num_match and unit_match:
                    qty = f"{float(num_match.group()):,.2f} {unit_match.group().upper()}"
                    break
            if qty != "Not found":
                break
    result["Qty"] = qty



    # 5️⃣ From State / To State
    result["From State"] = "Not found"
    result["To State"] = "Not found"
    for i, line in enumerate(lines):
        norm = normalize_ascii(line)
        if "dispatch from" in norm:
            for j in range(i, i + 5):
                if j < len(lines):
                    match = STATE_REGEX.search(lines[j])
                    if match:
                        result["From State"] = match.group(1).title()
                        break
        if "ship to" in norm:
            for j in range(i, i + 5):
                if j < len(lines):
                    match = STATE_REGEX.search(lines[j])
                    if match:
                        result["To State"] = match.group(1).title()
                        break

    # 6️⃣ Material name / Plastic Category
    material_line = find(r"Product\s+Name\s+&\s+Desc[^\n]*\n\s*([A-Z\s&]+)")
    if material_line and material_line != "Not found":
        material_clean = material_line.strip().title()
        result["Categorisation of Plastic Waste"] = "PET" if "pet" in material_clean.lower() else material_clean
    else:
        # fallback — scan HSN/product area
        for line in lines:
            if "waste" in line.lower() or "plastic" in line.lower():
                result["Categorisation of Plastic Waste"] = line.strip().title()
                break
        else:
            result["Categorisation of Plastic Waste"] = "Not found"

    return result
