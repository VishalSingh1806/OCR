# main.py

import os
import time
from pdf2image import convert_from_path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from ocr_utils import run_ocr, classify_category
from delivery_challan import extract_delivery_challan_fields
from lr_copy import extract_lr_copy_fields
from tax_invoice import extract_tax_invoice_fields
from weighbridge import extract_weighbridge_fields
from e_way_bill import extract_eway_bill_fields

# Path to your Google Vision credentials JSON
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API\vision-api.json"

# Folder where you have PDFs / JPGs / PNGs
FOLDER_PATH = r"C:\Users\visha\Downloads\ocr test\WB73B6961  30-1"


def process_text(text: str, filename: str, start_time: float):
    """
    1) classify_category(text)
    2) call the matching extract_*_fields(...) function
    3) attach Category + Processing Time + print (or send to frontend)
    """
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
        # Unrecognized category → skip
        print(f"\n📄 File: {filename}")
        print(f"❓ Skipped. Unrecognized category: {category}")
        return

    extracted["Category"] = category
    elapsed = round(time.time() - start_time, 2)
    extracted["Processing Time"] = f"{elapsed} seconds"

    # Here we simply print to console. Replace this block with:
    #   socketio.emit("ocr_result", extracted)   # or HTTP push, etc.
    print(f"\n📄 File: {filename}")
    for key, value in extracted.items():
        print(f"{key:<22}: {value}")
    print("-" * 80)


def ocr_and_classify_page(page_image, filename: str, page_idx: int, start_time: float):
    """
    Given a single pdf2image “page”, 
    1) save to disk as temp JPEG
    2) call run_ocr(...)
    3) call process_text(...)
    4) delete temp JPEG
    """
    # 1) write out temp_page_{page_idx}.jpg
    temp_img = os.path.join(FOLDER_PATH, f"temp_page_{page_idx}.jpg")
    page_image.save(temp_img, "JPEG")

    # 2) run OCR on that JPEG
    text = run_ocr(temp_img)

    # 3) delete the JPEG immediately
    try:
        os.remove(temp_img)
    except OSError:
        pass

    # 4) classify + extract + “send to frontend”
    process_text(text, f"{filename} [Page {page_idx}]", start_time)


if __name__ == "__main__":
    # Use a small ThreadPool so that each page is processed concurrently.
    # You can tweak max_workers to suit your machine.
    executor = ThreadPoolExecutor(max_workers=4)

    for filename in os.listdir(FOLDER_PATH):
        path = os.path.join(FOLDER_PATH, filename)
        start_time = time.time()

        if filename.lower().endswith(".pdf"):
            try:
                # 1) Convert entire PDF → a list of PIL pages
                pages = convert_from_path(path, dpi=300)

                # 2) As soon as we get “pages” back, immediately dispatch
                #    each page to its own thread for OCR + classification.
                for i, page in enumerate(pages, start=1):
                    executor.submit(ocr_and_classify_page, page, filename, i, start_time)

            except Exception as e:
                print(f"❌ Failed to process PDF {filename}: {e}")
                continue

        elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
            try:
                # a) Force‐convert the image to RGB and make a one‐page PDF
                img = Image.open(path).convert("RGB")
                temp_pdf = os.path.join(FOLDER_PATH, "temp_image.pdf")
                img.save(temp_pdf, "PDF", resolution=300.0)

                # b) Convert that single‐page PDF → pages[]
                pages = convert_from_path(temp_pdf, dpi=300)

                # c) Dispatch each page to the same thread‐pool
                for i, page in enumerate(pages, start=1):
                    executor.submit(ocr_and_classify_page, page, filename, i, start_time)

                # d) delete the temporary PDF
                os.remove(temp_pdf)

            except Exception as e:
                print(f"❌ Failed to convert/process image {filename}: {e}")
                continue

        else:
            # skip any other file types
            continue

    # ───── Graceful shutdown ─────
    executor.shutdown(wait=True)
    print("✅ All tasks have been dispatched/completed.")
