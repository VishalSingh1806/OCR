# # api.py

# import os
# import uuid
# import asyncio

# from fastapi import FastAPI, Request, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import socketio
# from pdf2image import convert_from_path

# # ─── 1) Import your existing OCR + extractor modules ───
# from ocr_utils import run_ocr, classify_category, normalize_ascii
# from delivery_challan import extract_delivery_challan_fields
# from lr_copy import extract_lr_copy_fields
# from tax_invoice import extract_tax_invoice_fields
# from weighbridge import extract_weighbridge_fields
# from e_way_bill import extract_eway_bill_fields

# # ─── 2) (Optional) Set GOOGLE_APPLICATION_CREDENTIALS here ───
# # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vision-api.json"

# # ─── 3) Create folders for uploads and temporary pages ───
# UPLOAD_DIR = "uploads"
# TEMP_DIR = "temp_pages"
# os.makedirs(UPLOAD_DIR, exist_ok=True)
# os.makedirs(TEMP_DIR, exist_ok=True)


# # ─── 4) Initialize Socket.IO + FastAPI ───
# sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
# app = FastAPI()

# # Allow CORS from your React frontend (adjust the origin in production)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],       # e.g. ["http://localhost:5173"]
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Mount the Socket.IO server under the same ASGI app
# socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# # ─── 5) In‐memory queues per connected socket ───
# # Structure: { sid_str: { "queue": [job1, job2, …], "is_processing": False } }
# user_queues = {}


# # ─── 6) Utility: Dispatch to the correct extractor based on category ───
# def extract_fields_for_category(text: str, category: str) -> dict:
#     if category == "Delivery Challan":
#         return extract_delivery_challan_fields(text)
#     elif category == "LR Copy":
#         return extract_lr_copy_fields(text)
#     elif category == "Tax Invoice":
#         return extract_tax_invoice_fields(text)
#     elif category == "Weighbridge":
#         return extract_weighbridge_fields(text)
#     elif category == "E Way Bill":
#         return extract_eway_bill_fields(text)
#     else:
#         return {}  # “Unknown” → no fields


# # ─── 7) Per‐image OCR + extraction job ───
# async def process_image_job(sid: str, job: dict):
#     """
#     job dictionary keys:
#       - file_name: str      (basename of the uploaded file, e.g. "1680.pdf")
#       - image_path: str     (temporary JPEG path on disk)
#       - parent: Optional[str]  (subfolder name, if any—e.g. "WB73B6961  30-1")
#       - pdf: bool           (True if this image came from a PDF page)
#       - page: int           (page number if PDF; 0 if standalone image)
#     """
#     file_name = job["file_name"]
#     image_path = job["image_path"]
#     parent = job.get("parent", None)
#     is_pdf = job.get("pdf", False)
#     page_number = job.get("page", 0)

#     # 7.1) Emit “processing” status
#     print(f"[process_image_job] → socket '{sid}' processing file='{file_name}', parent='{parent}', page={page_number}, pdf={is_pdf}")
#     await sio.emit(
#         "fileStatus",
#         {
#             "fileName": file_name,
#             "status": "processing",
#             "result": None,
#             "parent": parent,
#             "pdf": is_pdf,
#             "page": page_number,
#         },
#         to=sid,
#     )

#     # 7.2) Run OCR, classification, and extraction
#     try:
#         text = run_ocr(image_path)                         # Google Vision → raw text
#         category = classify_category(text.lower())          # classify into one of your categories
#         extracted = extract_fields_for_category(text, category)

#         # ─── INJECT A DEFAULT "Category Confidence" ───
#         # This makes the React UI display the extracted fields by satisfying:
#         #   parseFloat(page.data["Category Confidence"]) * 100 > 80
#         extracted["Category Confidence"] = "1.0"

#         result_data = extracted
#         status_str = "completed"
#         print(f"[process_image_job]   ↪ OCR & extract succeeded for '{file_name}', category='{category}', result_keys={list(extracted.keys())}")
#     except Exception as e:
#         result_data = {"error": str(e)}
#         status_str = "failed"
#         print(f"[process_image_job]   ↪ OCR/extract FAILED for '{file_name}' → {e}")

#     # 7.3) Emit “completed” (or “failed”) with the extracted fields
#     await sio.emit(
#         "fileStatus",
#         {
#             "fileName": file_name,
#             "status": status_str,
#             "result": result_data,
#             "parent": parent,
#             "pdf": is_pdf,
#             "page": page_number,
#         },
#         to=sid,
#     )
#     print(f"[process_image_job]   ↪ Emitted status='{status_str}' for file='{file_name}', page={page_number}")

#     # 7.4) Clean up that temporary JPEG
#     try:
#         if os.path.isfile(image_path):
#             os.remove(image_path)
#     except:
#         pass


# # ─── 8) Process queued jobs for a given socket ID ───
# async def process_user_queue(sid: str):
#     queue_data = user_queues.get(sid, None)
#     if not queue_data or queue_data["is_processing"]:
#         print(f"[process_user_queue] → Nothing to do for sid='{sid}' or already processing.")
#         return

#     queue_data["is_processing"] = True
#     print(f"[process_user_queue] → Starting to process {len(queue_data['queue'])} jobs for sid='{sid}'")

#     while queue_data["queue"]:
#         job = queue_data["queue"].pop(0)
#         print(f"[process_user_queue]    ↪ Dequeued job: {job}")
#         await process_image_job(sid, job)

#     queue_data["is_processing"] = False
#     print(f"[process_user_queue] → Completed all jobs for sid='{sid}'")


# # ─── 9) Socket.IO Event Handlers ───
# @sio.event
# async def connect(sid, environ):
#     # Create an empty queue for this client
#     user_queues[sid] = {"queue": [], "is_processing": False}
#     print(f"[Socket.IO] Connected: {sid}")


# @sio.event
# async def disconnect(sid):
#     # On disconnect, clean up any remaining temp images and remove queue
#     queue_data = user_queues.pop(sid, None)
#     if queue_data:
#         for job in queue_data["queue"]:
#             try:
#                 if os.path.isfile(job["image_path"]):
#                     os.remove(job["image_path"])
#             except:
#                 pass
#     print(f"[Socket.IO] Disconnected: {sid}")


# # ─── 10) HTTP endpoint to accept uploads ───
# @app.post("/extractText")
# async def extract_text(request: Request):
#     """
#     Expects:
#       - A multipart‐form with:
#           • One or more files under key "images"
#           • Zero or more values under "parents[]" (parallel array)
#           • Header "socket-id": the Socket.IO SID (or form‐field "socket_id")
#       - Each “images” item can be a PDF or JPG/PNG.
#       - Returns immediately; results stream back over Socket.IO "fileStatus".
#     """
#     print("======================================")
#     print("[extract_text] → Received new POST /extractText")
#     print("   → Raw headers:", dict(request.headers))

#     # 10.1) Parse the entire form once
#     form = await request.form()
#     print("[extract_text]   ↪ Parsed form keys:", list(form.keys()))

#     # 10.2) Determine socket_id: check “socket_id” or “socket-id” in form, else header
#     socket_id = None
#     if "socket_id" in form:
#         socket_id = form.get("socket_id")
#         print(f"[extract_text]   ↪ Found socket_id in form: '{socket_id}'")
#     elif "socket-id" in form:
#         socket_id = form.get("socket-id")
#         print(f"[extract_text]   ↪ Found 'socket-id' in form: '{socket_id}'")
#     else:
#         socket_id = request.headers.get("socket-id")
#         print(f"[extract_text]   ↪ Fallback to header 'socket-id': '{socket_id}'")

#     if not socket_id or socket_id not in user_queues:
#         print(f"[extract_text]   ↪ ERROR: Missing or invalid socket_id: '{socket_id}'")
#         raise HTTPException(status_code=400, detail="Invalid or missing socket_id")

#     # 10.3) Extract parents[] array (if any)
#     raw_parents = form.getlist("parents[]")  # might be an empty list if none sent
#     print(f"[extract_text]   ↪ parents[] array (length={len(raw_parents)}): {raw_parents}")

#     # 10.4) Extract list of uploaded files under "images"
#     uploads = form.getlist("images")  # each entry is an UploadFile
#     print(f"[extract_text]   ↪ images array (length={len(uploads)}): {[u.filename for u in uploads]}")

#     if len(uploads) == 0:
#         print("[extract_text]   ↪ ERROR: No files found under key 'images'.")
#         raise HTTPException(status_code=400, detail="No files uploaded")

#     # 10.5) Loop over each uploaded file
#     for idx, upload in enumerate(uploads):
#         raw_filename = upload.filename                  # e.g. "WB73B6961  30-1/1680.pdf"
#         clean_name = os.path.basename(raw_filename)     # becomes "1680.pdf"

#         unique_id = str(uuid.uuid4())
#         saved_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{clean_name}")

#         # 10.5.a) Save the raw upload (PDF or image) to disk
#         try:
#             with open(saved_path, "wb") as f:
#                 f.write(await upload.read())
#             print(f"[extract_text]    ↪ Saved '{clean_name}' → '{saved_path}'")
#         except Exception as e:
#             print(f"[extract_text]    ↪ ERROR saving {clean_name}: {e}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Failed to save {clean_name}: {e}"
#             )

#         lower = clean_name.lower()
#         parent = raw_parents[idx] if idx < len(raw_parents) else None
#         print(f"[extract_text]    ↪ Processing file #{idx}: '{clean_name}', parent='{parent}'")

#         # 10.5.b) If it’s a PDF, convert to JPEGs and enqueue one job per page
#         if lower.endswith(".pdf"):
#             try:
#                 pil_pages = convert_from_path(saved_path, dpi=300)
#                 print(f"[extract_text]    ↪ PDF '{clean_name}' converted to {len(pil_pages)} page(s).")
#             except Exception as e:
#                 os.remove(saved_path)
#                 print(f"[extract_text]    ↪ ERROR converting PDF '{clean_name}': {e}")
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"PDF→Image conversion failed for {clean_name}: {e}"
#                 )

#             for page_num, pil_page in enumerate(pil_pages, start=1):
#                 page_filename = f"{unique_id}_{clean_name}_page_{page_num}.jpg"
#                 page_path = os.path.join(TEMP_DIR, page_filename)
#                 pil_page.save(page_path, "JPEG")
#                 print(f"[extract_text]      ↪ Saved page {page_num} → '{page_path}'")

#                 job = {
#                     "file_name": clean_name,
#                     "image_path": page_path,
#                     "parent": parent,
#                     "pdf": True,
#                     "page": page_num,
#                 }
#                 user_queues[socket_id]["queue"].append(job)
#                 print(f"[extract_text]      ↪ Enqueued job: {job}")

#             # Delete the original PDF immediately
#             os.remove(saved_path)
#             print(f"[extract_text]    ↪ Deleted original PDF '{saved_path}'")

#         # 10.5.c) If it’s a JPG/PNG, save it and enqueue a single job
#         elif lower.endswith((".jpg", ".jpeg", ".png")):
#             page_filename = f"{unique_id}_{clean_name}"
#             page_path = os.path.join(TEMP_DIR, page_filename)
#             try:
#                 with open(page_path, "wb") as f:
#                     f.write(await upload.read())
#                 print(f"[extract_text]    ↪ Saved image '{clean_name}' → '{page_path}'")
#             except Exception as e:
#                 print(f"[extract_text]    ↪ ERROR saving image '{clean_name}': {e}")
#                 raise HTTPException(status_code=500, detail=f"Failed to save {clean_name}: {e}")

#             job = {
#                 "file_name": clean_name,
#                 "image_path": page_path,
#                 "parent": parent,
#                 "pdf": False,
#                 "page": 0,
#             }
#             user_queues[socket_id]["queue"].append(job)
#             print(f"[extract_text]    ↪ Enqueued job: {job}")

#         else:
#             # Unsupported file type—delete and return an error
#             os.remove(saved_path)
#             print(f"[extract_text]    ↪ ERROR unsupported file type: '{clean_name}'")
#             raise HTTPException(status_code=400, detail=f"Unsupported file type: {clean_name}")

#     # 10.6) Kick off background processing of this socket's queue
#     print(f"[extract_text]   ↪ Queued total of {len(user_queues[socket_id]['queue'])} job(s) for socket '{socket_id}'")
#     asyncio.create_task(process_user_queue(socket_id))

#     return {"message": "Files are being processed"}


# # ─── 11) Run via UVicorn ───
# # uvicorn api:socket_app --reload --port 8000


import os
import uuid
import shutil
import asyncio
from fastapi import FastAPI, Request, HTTPException, logger
from fastapi.middleware.cors import CORSMiddleware
import socketio
from pdf2image import convert_from_path

# ─── 1) Import OCR & extractor modules ───
from ocr_utils import run_ocr, classify_category, normalize_ascii
from delivery_challan import extract_delivery_challan_fields
from lr_copy import extract_lr_copy_fields
from tax_invoice import extract_tax_invoice_fields
from weighbridge import extract_weighbridge_fields
from e_way_bill import extract_eway_bill_fields

# ─── 2) Setup upload/temp directories ───
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp_pages"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── 3) Initialize FastAPI + Socket.IO ───
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# ─── 4) In-memory queues per client ───
user_queues = {}

# ─── 5) Helper: extract socket ID ───
def _extract_socket_id(form, headers) -> str:
    if "socket_id" in form:
        logger.info(f"Extracted socket_id from form: {form.get('socket_id')}")
        return form.get("socket_id")
    if "socket-id" in form:
        logger.info(f"Extracted socket-id from form: {form.get('socket-id')}")
        return form.get("socket-id")
    return headers.get("socket-id")

# ─── 6) Helper: save upload to disk ───
async def _save_upload(upload) -> tuple:
    raw_name = upload.filename
    clean_name = os.path.basename(raw_name)
    uid = uuid.uuid4().hex
    dest = os.path.join(UPLOAD_DIR, f"{uid}_{clean_name}")
    data = await upload.read()
    with open(dest, "wb") as f:
        f.write(data)
    return dest, clean_name, uid

# ─── 7) Helper: enqueue PDF pages ───
def _enqueue_pdf(clean_name, saved_path, uid, parent, socket_id):
    pages = convert_from_path(saved_path, dpi=300)
    for num, page in enumerate(pages, start=1):
        jpg = f"{uid}_{clean_name}_page_{num}.jpg"
        jpg_path = os.path.join(TEMP_DIR, jpg)
        page.save(jpg_path, "JPEG")
        job = {
            "file_name": clean_name,
            "image_path": jpg_path,
            "parent": parent,
            "pdf": True,
            "page": num,
        }
        user_queues[socket_id]["queue"].append(job)
    os.remove(saved_path)

# ─── 8) Helper: enqueue image file ───
def _enqueue_image(clean_name, saved_path, uid, parent, socket_id):
    dest = os.path.join(TEMP_DIR, f"{uid}_{clean_name}")
    shutil.move(saved_path, dest)
    job = {
        "file_name": clean_name,
        "image_path": dest,
        "parent": parent,
        "pdf": False,
        "page": 0,
    }
    user_queues[socket_id]["queue"].append(job)

# ─── 9) Dispatch to correct extractor ───
def _extract_fields_for_category(text: str, category: str) -> dict:
    if category == "Delivery Challan":
        return extract_delivery_challan_fields(text)
    if category == "LR Copy":
        return extract_lr_copy_fields(text)
    if category == "Tax Invoice":
        return extract_tax_invoice_fields(text)
    if category == "Weighbridge":
        return extract_weighbridge_fields(text)
    if category == "E Way Bill":
        return extract_eway_bill_fields(text)
    return {}

# ─── 10) Per-image OCR + extraction job ───
async def _process_image_job(sid: str, job: dict):
    await sio.emit("fileStatus", {"fileName": job["file_name"], "status": "processing", "result": None,
                                      "parent": job.get("parent"), "pdf": job.get("pdf"), "page": job.get("page")}, to=sid)
    try:
        text = run_ocr(job["image_path"])
        category = classify_category(text)
        extracted = _extract_fields_for_category(text, category)
        extracted["Category Confidence"] = "1.0"
        status = "completed"
        result = extracted
    except Exception as e:
        status = "failed"
        result = {"error": str(e)}
    await sio.emit("fileStatus", {"fileName": job["file_name"], "status": status, "result": result,
                                      "parent": job.get("parent"), "pdf": job.get("pdf"), "page": job.get("page")}, to=sid)
    try:
        os.remove(job["image_path"])
    except:
        pass

# ─── 11) Process queued jobs for a given socket ID ───
async def _process_user_queue(sid: str):
    data = user_queues.get(sid)
    if not data or data["is_processing"]:
        return
    data["is_processing"] = True
    while data["queue"]:
        job = data["queue"].pop(0)
        await _process_image_job(sid, job)
    data["is_processing"] = False

# ─── 12) Socket.IO event handlers ───
@sio.event
async def connect(sid, environ):
    user_queues[sid] = {"queue": [], "is_processing": False}

@sio.event
async def disconnect(sid):
    data = user_queues.pop(sid, None)
    if data:
        for job in data["queue"]:
            try:
                os.remove(job["image_path"])
            except:
                pass

# ─── 13) HTTP endpoint to accept uploads ───
@app.post("/extractText")
async def extract_text(request: Request):
    form = await request.form()
    socket_id = _extract_socket_id(form, request.headers)
    if not socket_id or socket_id not in user_queues:
        raise HTTPException(status_code=400, detail="Invalid or missing socket_id")
    parents = form.getlist("parents[]")
    uploads = form.getlist("images")
    if not uploads:
        raise HTTPException(status_code=400, detail="No files uploaded")

    for idx, upload in enumerate(uploads):
        saved_path, clean_name, uid = await _save_upload(upload)
        parent = parents[idx] if idx < len(parents) else None
        lower = clean_name.lower()

        if lower.endswith(".pdf"):
            try:
                _enqueue_pdf(clean_name, saved_path, uid, parent, socket_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")
        elif lower.endswith((".jpg", ".jpeg", ".png")):
            _enqueue_image(clean_name, saved_path, uid, parent, socket_id)
        else:
            os.remove(saved_path)
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {clean_name}")

    asyncio.create_task(_process_user_queue(socket_id))
    return {"message": "processing_started"}


# uvicorn api:socket_app --reload --port 8000