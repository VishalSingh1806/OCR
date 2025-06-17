# main.py

import os
import shutil
import time
import uuid
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from pdf2image import convert_from_path
from PIL import Image

import socketio

# ─────────────── SETUP FASTAPI + SOCKET.IO ───────────────
#
# This example uses python-socketio with ASGI integration.
# In your actual startup, you might do something like:
#
#   sio = socketio.AsyncServer(async_mode="asgi")
#   app = FastAPI()
#   app_mount = socketio.ASGIApp(sio, app)
#
# Here we’ll sketch it in one file for clarity.

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
# Mount the Socket.IO ASGI handler on the same FastAPI app
app = socketio.ASGIApp(sio, app)


# ─────────────── IMPORT YOUR OCR / CLASSIFICATION / EXTRACTORS ───────────────

from ocr_utils import run_ocr, classify_category
from delivery_challan import extract_delivery_challan_fields
from lr_copy import extract_lr_copy_fields
from tax_invoice import extract_tax_invoice_fields
from weighbridge import extract_weighbridge_fields
from e_way_bill import extract_eway_bill_fields

# ─────────────── CONFIG ───────────────

# Make sure GOOGLE_APPLICATION_CREDENTIALS is set to your Vision JSON key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API\vision-api.json"

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
TEMP_DIR   = os.path.join(os.getcwd(), "temp_pages")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ─────────────── HELPER: select extractor based on category ───────────────

def extract_fields_for(text: str) -> dict:
    """
    Decide which extractor to call based on classify_category(text),
    then return a dict of extracted fields.
    """
    category = classify_category(text)

    if category == "Tax Invoice":
        fields = extract_tax_invoice_fields(text)
    elif category == "E Way Bill":
        fields = extract_eway_bill_fields(text)
    elif category == "LR Copy":
        fields = extract_lr_copy_fields(text)
    elif category == "Delivery Challan":
        fields = extract_delivery_challan_fields(text)
    elif category == "Weighbridge":
        fields = extract_weighbridge_fields(text)
    else:
        # Unrecognized
        return {"Category": category}

    fields["Category"] = category
    return fields


# ─────────────── BACKGROUND TASK: OCR + CLASSIFY + EMIT ───────────────

async def handle_single_page(
    jpeg_path: str,
    original_filename: str,
    page_index: int,
    start_time: float,
    parent_id: str,
    socket_id: str
):
    """
    1) call run_ocr(...) on jpeg_path
    2) run classify_category + appropriate extractor
    3) emit via Socket.IO to the client’s room=<socket_id>
    4) delete the temp JPEG
    """
    try:
        # 1) OCR
        text = run_ocr(jpeg_path)

        # 2) extract fields
        result = extract_fields_for(text)

        # 3) add metadata
        elapsed = round(time.time() - start_time, 2)
        result["Processing Time"] = f"{elapsed} seconds"
        result["Filename"] = f"{original_filename} [Page {page_index}]"
        result["Page"] = page_index
        result["ParentID"] = parent_id

        # 4) emit back to the front end immediately
        #    The front end should listen on event name "page_processed"
        await sio.emit(
            "page_processed",
            result,
            room=socket_id
        )
    except Exception as e:
        # In case something breaks, emit an error message back
        await sio.emit(
            "page_error",
            {
                "error": str(e),
                "Filename": f"{original_filename} [Page {page_index}]",
                "Page": page_index,
                "ParentID": parent_id
            },
            room=socket_id
        )
    finally:
        # 5) delete the temp JPEG
        try:
            os.remove(jpeg_path)
        except OSError:
            pass


# ─────────────── FASTAPI ROUTE: /extractText ───────────────

@app.post("/extractText")
async def extract_text(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    parents: List[str] = Form(...),
    socket_id: str = Header(None, alias="socket-id")
):
    """
    - `images`: a list of PDF/JPG/PNG files
    - `parents[]`: a list of parent IDs (one per file)
    - `socket-id` header: the client’s Socket.IO session ID, so we know where to emit
    """

    if socket_id is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing `socket-id` header"}
        )

    # Loop through each uploaded file + its matching parent ID
    for upload_file, parent_id in zip(images, parents):
        # 1) Save the raw upload to disk
        unique_name = f"{uuid.uuid4()}_{upload_file.filename}"
        disk_path = os.path.join(UPLOAD_DIR, unique_name)

        with open(disk_path, "wb") as f:
            contents = await upload_file.read()
            f.write(contents)

        # 2) Immediately convert that file to pages (if PDF) or force-RGB→PDF→pages if image
        start_time = time.time()
        ext = upload_file.filename.lower()

        try:
            if ext.endswith(".pdf"):
                # Convert PDF → list of PIL pages
                pil_pages = convert_from_path(disk_path, dpi=300)

            elif ext.endswith((".jpg", ".jpeg", ".png")):
                # Force image → RGB, crudely wrap in a temp one‐page PDF
                img = Image.open(disk_path).convert("RGB")
                temp_pdf = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_temp.pdf")
                img.save(temp_pdf, "PDF", resolution=300.0)

                pil_pages = convert_from_path(temp_pdf, dpi=300)

                # Delete our temp PDF wrapper
                try:
                    os.remove(temp_pdf)
                except OSError:
                    pass
            else:
                # Skip unsupported file type
                await sio.emit(
                    "page_error",
                    {
                        "error": f"Unsupported file type: {upload_file.filename}",
                        "Filename": upload_file.filename,
                        "ParentID": parent_id
                    },
                    room=socket_id
                )
                continue

            # 3) As soon as we have each `pil_pages[i]`, schedule a background task to:
            #      a) save page_i → temp JPEG
            #      b) run_ocr(temp JPEG) → classify + extract → emit
            for i, page in enumerate(pil_pages, start=1):
                # a) Save page_i as a JPEG
                jpeg_name = f"{uuid.uuid4()}_{upload_file.filename}_page_{i}.jpg"
                jpeg_path = os.path.join(TEMP_DIR, jpeg_name)
                page.save(jpeg_path, "JPEG")

                # b) Kick off a background task for that single page
                background_tasks.add_task(
                    handle_single_page,
                    jpeg_path,
                    upload_file.filename,
                    i,
                    start_time,
                    parent_id,
                    socket_id
                )

        except Exception as e:
            # If conversion fails, emit error immediately
            await sio.emit(
                "page_error",
                {
                    "error": f"Failed to convert/process {upload_file.filename}: {e}",
                    "Filename": upload_file.filename,
                    "ParentID": parent_id
                },
                room=socket_id
            )
            continue

        finally:
            # 4) Delete the original upload ASAP (we only needed it for PDF→pages)
            try:
                os.remove(disk_path)
            except OSError:
                pass

    # 5) Return 200 immediately – every page is now “in flight” processing
    return JSONResponse(status_code=200, content={"status": "processing_started"})


# ─────────────── SOCKET.IO EVENT: CLIENT CONNECT/DISCONNECT ───────────────

@sio.event
async def connect(sid, environ):
    # Optionally log: a client has connected
    print(f"Socket.IO client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Socket.IO client disconnected: {sid}")
