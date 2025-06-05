# main.py
import os
import time
from pdf2image import convert_from_path
from ocr_utils import run_ocr, classify_category
from delivery_challan import extract_delivery_challan_fields
from lr_copy import extract_lr_copy_fields
from tax_invoice import extract_tax_invoice_fields
from weighbridge import extract_weighbridge_fields
from e_way_bill import extract_eway_bill_fields

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API 3\vision-api.json"

# FOLDER_PATH = r"C:\Users\visha\Downloads\test 4\83"
FOLDER_PATH = r"C:\Users\visha\Downloads\January Movement-20241017T094850Z-001\January Movement\Gujarat\test\WB73B6961  30-1"

def process_text(text, filename, start_time):
    category = classify_category(text)
    if category == "Tax Invoice":
        extracted = extract_tax_invoice_fields(text)
    elif category == "E Way Bill":
        extracted = extract_eway_bill_fields(text)
    elif category == "LR Copy":
        extracted = extract_lr_copy_fields(text)
    elif category == "Delivery Challan":
        extracted = extract_delivery_challan_fields(text)
    elif category == "Weighbridge":
         extracted = extract_weighbridge_fields(text)
    else:
        print(f"\n📄 File: {filename}")
        print(f"❓ Skipped. Unrecognized category: {category}")
        return

    extracted["Category"] = category
    extracted["Processing Time"] = f"{round(time.time() - start_time, 2)} seconds"

    print(f"\n📄 File: {filename}")
    for key, value in extracted.items():
        print(f"{key:<22}: {value}")
    print("-" * 80)

for filename in os.listdir(FOLDER_PATH):
    path = os.path.join(FOLDER_PATH, filename)
    start_time = time.time()

    if filename.lower().endswith(".pdf"):
        try:
            pages = convert_from_path(path, dpi=300)
            if len(pages) > 1:
                for i, page in enumerate(pages):
                    temp_img = os.path.join(FOLDER_PATH, f"temp_page_{i}.jpg")
                    page.save(temp_img, "JPEG")
                    text = run_ocr(temp_img)
                    os.remove(temp_img)
                    process_text(text, f"{filename} [Page {i+1}]", start_time)
            else:
                temp_img = os.path.join(FOLDER_PATH, "temp_page.jpg")
                pages[0].save(temp_img, "JPEG")
                text = run_ocr(temp_img)
                os.remove(temp_img)
                process_text(text, filename, start_time)

        except Exception as e:
            print(f"❌ Failed to process PDF {filename}: {e}")
            continue

    elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
        text = run_ocr(path)
        process_text(text, filename, start_time)

    else:
        continue