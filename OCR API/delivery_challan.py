# extractors/delivery_challan.py
import re
from ocr_utils import debug_print_lines

def extract_delivery_challan_fields(text):
    # debug_print_lines(text, "Delivery Challan: Line-by-Line OCR Output")
    result = {}

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

    consignee = re.search(r"CONSIGNEEDETAILS\s*([\s\S]{10,200}?)\n[A-Z\s]{5,}", text)
    consignor = re.search(r"CONSIGNORDETAILS\s*([\s\S]{10,200}?)\n[A-Z\s]{5,}", text)

    dispatch = re.search(r"Place of Dispatch[:\-]?\s*\n?([A-Za-z\s]+)\n?\(([A-Za-z\s]+)\)", text)
    delivery = re.search(r"Place of Delivery[:\-]?\s*\n?([A-Za-z\s]+)\n?\(([A-Za-z\s]+)\)", text)

    qty_val = "Not found"
    table_match = re.search(r"SR[\s\n]+NO[\s\S]{20,800}?(?:TOTAL|SPECIAL INSTRUCTIONS)", text, re.IGNORECASE)
    if table_match:
        table_block = table_match.group(0)
        quantities = re.findall(r"\b(\d{1,3}\.\d{1,3})\b", table_block)
        total_qty = sum(float(q) for q in quantities)
        if quantities:
            qty_val = f"{total_qty:.3f} MT"

    result.update({
        "Vehicle Number": find(vehicle_pattern),
        "Date": find(r"(?:Dated:|Date:)[:\-]?\s*" + date_pattern),
        "No.": find(r"(?:DC\s*No.|Challan\s*No\.?)[:\-]?\s*([A-Z0-9\-\/]+)"),
        "Transporter Name": consignor.group(1).strip().split('\n')[0] if consignor else "Not found",
        "Qty": qty_val,
        "Consignor": consignor.group(1).strip().split('\n')[0] if consignor else "Not found",
        "Consignee": consignee.group(1).strip().split('\n')[0] if consignee else "Not found",
        "From State": dispatch.group(2).strip() if dispatch else "Not found",
        "To State": delivery.group(2).strip() if delivery else "Not found"
    })

    return result
