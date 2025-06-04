import re
from ocr_utils import debug_print_lines, extract_material_name_from_lines, extract_quantity_from_lines, extract_invoice_number_from_lines



def extract_tax_invoice_fields(text):
    print("\n🧾 Processing: Tax Invoice")

    # debug_print_lines(text, "Tax Invoice: Line-by-Line OCR Output") 
    
    result = {"Category": "Tax Invoice"}

    def find(pattern, flags=re.IGNORECASE):
        match = re.search(pattern, text, flags)
        if not match:
            return "Not found"
        for g in match.groups():
            if g:
                return g.strip()
        return "Not found"

    # Regex patterns
    date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{1,2}[\s\-]?(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[\s\-]?\d{2,4})"
    vehicle_pattern = r"\b([A-Z]{2}\d{2}[A-Z]{1,3}\s?\d{3,4})\b"


    result.update({
        "Invoice Date": find(r"(?:INVOICE\s*DATE|DATED)[:\-]?\s*" + date_pattern),
        "Invoice Number": extract_invoice_number_from_lines(text),
        "Quantity": extract_quantity_from_lines(text),
        "Material Name": extract_material_name_from_lines(text),
        "Vehicle Number": find(vehicle_pattern),
    })

    return result
