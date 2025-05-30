import re
from app.services.ocr_utils import (normalize_ascii,
                       extract_consignor_consignee_blocks,
                       extract_states_from_blocks,
                       extract_consignment_no_using_date_proximity,
                       debug_print_lines
)
def extract_lr_copy_fields(text):
    print("\n🦾 Processing: LR Copy")

    lines = [normalize_ascii(line) for line in text.splitlines()]
    result = {"Category": "LR Copy"}

    # debug_print_lines(text, "LR Copy: Line-by-Line OCR Output")

    def find(pattern, group=1, flags=re.IGNORECASE):
        match = re.search(pattern, text, flags)
        if not match:
            return "Not found"
        for g in match.groups():
            if g:
                return g.strip()
        return "Not found"

    vehicle_pattern = r"([A-Z]{2}\d{2}[A-Z]{1,3}\s?\d{3,4})"
    date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{1,2}[\s\-]?(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[\s\-]?\d{2,4})"

    consignment_no = extract_consignment_no_using_date_proximity(lines)
    date_val = find(r"DATE[:\-]?\s*" + date_pattern)
    transporter = "BHARAT CARRING AGENT" if "bharat carring agent" in normalize_ascii(text).lower() else "Not found"
    consignor, consignee = extract_consignor_consignee_blocks(lines)
    from_state, to_state = extract_states_from_blocks(lines)

    qty_val = "Not found"
    table_match = re.search(r"PLASTIC SCRAP[\s\S]{0,300}?(?:TOTAL|VALUE|LR TYPE)", text, re.IGNORECASE)
    if table_match:
        table_block = table_match.group(0)
        quantities = re.findall(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d{1,3}))\b", table_block)
        numeric_vals = [float(q.replace(',', '')) for q in quantities]
        if numeric_vals:
            qty_val = f"{max(numeric_vals):,.3f} MT"

        print("📄 Consignment No.:", consignment_no)
        print("📮 Consignor:", consignor)
        print("📬 Consignee:", consignee)
        print("📍 From State:", from_state)
        print("📍 To State:", to_state)

    result.update({
        "Vehicle Number": find(vehicle_pattern),
        "Date": date_val,
        "No.": consignment_no,
        "Transporter Name": transporter,
        "Qty": qty_val,
        "Consignor": consignor,
        "Consignee": consignee,
        "From State": from_state,
        "To State": to_state
    })

    return result
