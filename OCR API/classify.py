import os
import io
import re
import time
from PIL import Image
from pdf2image import convert_from_path
from google.cloud import vision
import unicodedata

# Set your credentials path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API\vision-api.json"

# Folder to scan
FOLDER_PATH = r"C:\Users\visha\Downloads\ocr test"

# Vision API client
client = vision.ImageAnnotatorClient()

def classify_category(text):
    text = text.lower()
    if "delivery challan" in text or "dc no" in text:
        return "Delivery Challan"
    elif "lr copy" in text or "lorry receipt" in text or "consignment note" in text:
        return "LR Copy"
    elif "weighbridge" in text or "nett wt" in text or "gross wt" in text or "tare wt" in text:
        return "Weighbridge"
    elif "tax invoice" in text or "invoice no" in text:
        return "Tax Invoice"
    return "Unknown"

def normalize_ascii(text):
    # Replace known OCR or non-ASCII issues first (before ASCII stripping)
    replacements = {
        'Το': 'To',   # Greek Tau + Omicron
        'το': 'to',
        ' T0': 'To',  # T-zero
        ' t0': 'to',
        ' Tо': 'To',  # Cyrillic o
        ' tо': 'to',
        'tο': 'to',   # mix of Latin t + Greek omicron
        't o': 'to',
    }

    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    # Now normalize and strip accents
    nfkd = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd.encode('ASCII', 'ignore').decode('utf-8')

    return only_ascii.lower().strip()


def run_ocr(image_path):
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    return response.text_annotations[0].description if response.text_annotations else ""

# def extract_consignment_no_near_header(lines):
#     print("\n🔍 Debugging Consignment No Extraction")
#     for i, line in enumerate(lines):
#         print(f"Line {i}: '{line.strip()}'")
#         if "CONSIGNMENT NOTE" in line.upper():
#             print(f"📌 Found 'CONSIGNMENT NOTE' at line {i}")
#             for j in range(1, 5):
#                 if i + j >= len(lines):
#                     continue
#                 current_line = lines[i + j].strip()
#                 print(f"🔎 Checking line {i + j}: '{current_line}'")

#                 # Case 1: No.: 4137 on the same line
#                 match = re.search(r"\bNO\.?\s*[:\-]?\s*([0-9A-Z\-\/]{3,})", current_line, re.IGNORECASE)
#                 if match:
#                     print(f"✅ Found consignment on same line: '{match.group(1)}'")
#                     return match.group(1).strip()
                
#                 # Case 2: No. is alone, next line is value
#                 if "NO" in current_line.upper() and i + j + 1 < len(lines):
#                     next_line = lines[i + j + 1].strip()
#                     print(f"👀 'NO' alone, checking line {i + j + 1}: '{next_line}'")
#                     if re.match(r"^[0-9A-Z\-\/]{3,}$", next_line):
#                         print(f"✅ Found consignment split over lines: '{current_line}' + '{next_line}'")
#                         return next_line
#     print("❌ Consignment No not found")
#     return "Not found"

def extract_consignment_no_using_date_proximity(lines):
    print("\n🔍 Smart Consignment No Extraction via proximity")

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

    print("❌ Consignment number not found near DATE block")
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


def extract_fields(text, category):
    result = {"Category": category}

    def find(pattern, group=1, flags=re.IGNORECASE):
        match = re.search(pattern, text, flags)
        if not match:
            return "Not found"
        
        # Try all matched groups in order
        for g in match.groups():
            if g:
                return g.strip()
        
        return "Not found"


    vehicle_pattern = r"([A-Z]{2}\d{2}[A-Z]{1,3}\s?\d{3,4})"
    date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{1,2}[\s\-]?(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[\s\-]?\d{2,4})"
    quantity_pattern = r"(\d{1,3}(?:,\d{3})*(?:\.\d{1,3})?)\s*(MT|KG|KGS|TONS)"
    weight_pattern = r"net\s*weight[^:\d]*[:\-]?\s*(\d{1,3}\.\d{1,3})"

    if category in ["Delivery Challan"]:
        # Handle multi-line consignee block
        consignee = re.search(r"CONSIGNEEDETAILS\s*([\s\S]{10,200}?)\n[A-Z\s]{5,}", text)
        consignor = re.search(r"CONSIGNORDETAILS\s*([\s\S]{10,200}?)\n[A-Z\s]{5,}", text)
        
        # From/To State from "Place of Dispatch/Delivery"
        dispatch = re.search(r"Place of Dispatch[:\-]?\s*\n?([A-Za-z\s]+)\n?\(([A-Za-z\s]+)\)", text)
        delivery = re.search(r"Place of Delivery[:\-]?\s*\n?([A-Za-z\s]+)\n?\(([A-Za-z\s]+)\)", text)

        # Extract table-based quantity (from SR NO to TOTAL or SPECIAL INSTRUCTIONS)
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
            "No.": find(r"(?:DC\s*No.|Challan\s*No.\.?)[:\-]?\s*([A-Z0-9\-\/]+)"),
            # "Transporter Name": find(r"(?:Mode of Transport|Dispatched through)[:\-]?\s*\n?([A-Za-z\s&]+)"),
            "Transporter Name": consignor.group(1).strip().split('\n')[0] if consignor else "Not found",
            "Qty": qty_val,
            "Consignor": consignor.group(1).strip().split('\n')[0] if consignor else "Not found",
            "Consignee": consignee.group(1).strip().split('\n')[0] if consignee else "Not found",
            "From State": dispatch.group(2).strip() if dispatch else "Not found",
            "To State": delivery.group(2).strip() if delivery else "Not found"
        })
    
    elif category == "LR Copy":
        print("\n🧾 Processing: LR Copy")

        lines = text.splitlines()
        qty_val = "Not found"
        consignment_no = extract_consignment_no_using_date_proximity(lines)
        # consignment_no = extract_consignment_no_near_header(lines)
        date_val = find(r"DATE[:\-]?\s*" + date_pattern)
        transporter = "Not found"

        if re.search(r"BHARAT\s+CARRING\s+AGENT", text):
            transporter = "BHARAT CARRING AGENT"

        consignor, consignee = extract_consignor_consignee_blocks(lines)
        from_state,to_state = extract_states_from_blocks(lines)
        # to_state = extract_states_from_blocks(lines)

        # Quantity logic (unchanged)
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


    elif category == "Weighbridge":
        result.update({
            "Date": find(date_pattern),
            "No.": find(r"(?:No\.?|Ticket No\.?|Slip No\.?)[:\-]?\s*([A-Z0-9\-\/]+)"),
            "Name": find(r"(?:Weighbridge Name|Name)[:\-]?\s*([A-Za-z\s&]{4,})"),
            "State": find(r"State[:\-]?\s*([A-Za-z\s]+)"),
            "Vehicle Number": find(vehicle_pattern),
            "Net Weight (Tons)": find(weight_pattern)
        })

    elif category == "Tax Invoice":
        qty_val = "Not found"

        # Try to extract quantity from the first large float ending with unit (MT/KG/KGS)
        all_quantity_candidates = re.findall(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d{1,3})?)\s*(KGS|KG|MT|TONS)?", text)
        if all_quantity_candidates:
            # Convert and find the largest value (to ignore small rates like 0.20)
            numeric_vals = []
            for val, unit in all_quantity_candidates:
                try:
                    numeric_vals.append(float(val.replace(',', '')))
                except:
                    continue

            if numeric_vals:
                best = max(numeric_vals)
                qty_val = f"{best:,.3f} KGS"

        result.update({
            "Invoice Date": find(r"(?:INVOICE\s*DATE|DATED)[:\-]?\s*" + date_pattern),
            "Invoice Number": find(r"(?:INVOICE\s*NO\.?)[:\-]?\s*([A-Z0-9\-\/]+)"),
            "Quantity": qty_val,
            "Material Name": find(r"(?:MATERIAL\s*NAME|DESCRIPTION)[:\-]?\s*([A-Z\s]+)"),
            "Vehicle Number": find(vehicle_pattern)
        })


    return result



# Process folder
for filename in os.listdir(FOLDER_PATH):
    path = os.path.join(FOLDER_PATH, filename)
    start_time = time.time()

    # If PDF, convert to image
    if filename.lower().endswith(".pdf"):
        try:
            images = convert_from_path(path, dpi=300)
            temp_img = os.path.join(FOLDER_PATH, "temp_page.jpg")
            images[0].save(temp_img, "JPEG")
            text = run_ocr(temp_img)
            os.remove(temp_img)
        except Exception as e:
            print(f"❌ Failed to process PDF {filename}: {e}")
            continue
    elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
        text = run_ocr(path)
    else:
        continue

    category = classify_category(text)
    extracted = extract_fields(text, category)
    extracted["Processing Time"] = f"{round(time.time() - start_time, 2)} seconds"

    print(f"\n📄 File: {filename}")
    for key, value in extracted.items():
        print(f"{key:<22}: {value}")
    print("-" * 80)