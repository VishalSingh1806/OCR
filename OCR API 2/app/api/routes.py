from app.socket import sio
from fastapi import APIRouter, UploadFile, File, Request, Form
from app.services.ocr_utils import run_ocr, classify_category
from app.services.tax_invoice import extract_tax_invoice_fields
from app.services.lr_copy import extract_lr_copy_fields
from app.services.delivery_challan import extract_delivery_challan_fields
from app.services.weighbridge import extract_weighbridge_fields
from app.services.e_way_bill import extract_eway_bill_fields
import os
import time
import shutil
import tempfile
from pdf2image import convert_from_path

router = APIRouter()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API 2\app\services\vision-api.json"

@router.post("/extractText")
async def extract_text(
    request: Request,
    images: list[UploadFile] = File(...),
    socket_id: str = Form(None)
):
    for uploaded_file in images:
        file_name = uploaded_file.filename
        is_pdf = file_name.lower().endswith(".pdf")

        # 📡 Emit file-level processing start
        await sio.emit("fileStatus", {
            "status": "processing",
            "fileName": file_name,
            "parent": None,
            "pdf": is_pdf,
            "page": 0,
            "result": None
        }, to=socket_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as tmp:
            shutil.copyfileobj(uploaded_file.file, tmp)
            tmp_path = tmp.name

        start_time = time.time()

        if is_pdf:
            try:
                pages = convert_from_path(tmp_path, dpi=300)

                for i, page in enumerate(pages):
                    page_number = i + 1
                    await sio.emit("fileStatus", {
                        "status": "processing",
                        "fileName": file_name,
                        "parent": None,
                        "pdf": True,
                        "page": page_number,
                        "result": None
                    }, to=socket_id)

                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                        temp_img_path = temp_img.name

                    page.save(temp_img_path, "JPEG")
                    text = run_ocr(temp_img_path)
                    os.remove(temp_img_path)

                    result = process_text(text, f"{file_name} [Page {page_number}]", start_time)

                    await sio.emit("fileStatus", {
                        "status": "completed",
                        "fileName": file_name,
                        "parent": None,
                        "pdf": True,
                        "page": page_number,
                        "result": result
                    }, to=socket_id)

            except Exception as e:
                await sio.emit("fileStatus", {
                    "status": "failed",
                    "fileName": file_name,
                    "parent": None,
                    "pdf": True,
                    "page": 0,
                    "result": str(e)
                }, to=socket_id)

        else:
            try:
                text = run_ocr(tmp_path)
                result = process_text(text, file_name, start_time)

                await sio.emit("fileStatus", {
                    "status": "completed",
                    "fileName": file_name,
                    "parent": None,
                    "pdf": False,
                    "page": 0,
                    "result": result
                }, to=socket_id)

            except Exception as e:
                await sio.emit("fileStatus", {
                    "status": "failed",
                    "fileName": file_name,
                    "parent": None,
                    "pdf": False,
                    "page": 0,
                    "result": str(e)
                }, to=socket_id)

        os.remove(tmp_path)

    return {"message": "Files are being processed"}



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
        return {"file": filename, "error": f"Unrecognized category: {category}"}

    extracted["Category"] = category
    extracted["Processing Time"] = f"{round(time.time() - start_time, 2)} seconds"
    return extracted
