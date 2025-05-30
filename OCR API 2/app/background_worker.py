import asyncio
import os
import tempfile
import shutil
import time
from pdf2image import convert_from_path
from app.socket import sio, user_queues
from app.services.ocr_utils import run_ocr, classify_category
from app.services.tax_invoice import extract_tax_invoice_fields
from app.services.lr_copy import extract_lr_copy_fields
from app.services.delivery_challan import extract_delivery_challan_fields
from app.services.weighbridge import extract_weighbridge_fields
from app.services.e_way_bill import extract_eway_bill_fields

async def worker_loop():
    while True:
        await trigger_all_queues()
        await asyncio.sleep(0.1)

async def trigger_all_queues():
    for sid, queue_data in list(user_queues.items()):
        if queue_data["isProcessing"] or not queue_data["queue"]:
            continue

        queue_data["isProcessing"] = True
        try:
            while queue_data["queue"]:
                job = queue_data["queue"].pop(0)
                await process_job(sid, job)
        finally:
            queue_data["isProcessing"] = False

async def trigger_queue_processing(sid):
    queue_data = user_queues.get(sid)
    if not queue_data or queue_data["isProcessing"] or not queue_data["queue"]:
        return
    queue_data["isProcessing"] = True
    try:
        while queue_data["queue"]:
            job = queue_data["queue"].pop(0)
            await process_job(sid, job)
    finally:
        queue_data["isProcessing"] = False

async def process_job(sid, job):
    file_name = os.path.basename(job["fileName"])
    parent = job.get("parent")
    is_pdf = job.get("is_pdf", False)

    await sio.emit("fileStatus", {
        "status": "processing",
        "fileName": file_name,
        "parent": parent,
        "pdf": is_pdf,
        "page": job.get("page", 0),
        "result": None
    }, room=sid)

    start_time = time.time()
    try:
        text = run_ocr(job["path"])
        result = process_text(text, file_name, start_time)
        await sio.emit("fileStatus", {
            "status": "completed",
            "fileName": file_name,
            "parent": parent,
            "pdf": is_pdf,
            "page": job.get("page", 0),
            "result": result
        }, room=sid)
    except Exception as e:
        await sio.emit("fileStatus", {
            "status": "failed",
            "fileName": file_name,
            "parent": parent,
            "pdf": is_pdf,
            "page": job.get("page", 0),
            "result": str(e)
        }, room=sid)
    finally:
        try:
            os.remove(job["path"])
        except Exception:
            pass

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
