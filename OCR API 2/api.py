import os
import uuid
import shutil
import asyncio
from fastapi import FastAPI, Request, HTTPException, UploadFile
import logging
from fastapi.middleware.cors import CORSMiddleware
import socketio
from pdf2image import convert_from_path
from google.cloud import vision

from ocr_utils import classify_category
from modules.weighbridge import extract_weighbridge_fields
from modules.tax_invoice import extract_tax_invoice_fields
from modules.delivery_challan import extract_delivery_challan_fields
from modules.lr_copy import extract_lr_copy_fields
from modules.e_way_bill import extract_e_way_bill_fields

UPLOAD_DIR = "uploads"
TEMP_DIR = "temp_pages"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

logger = logging.getLogger("ocr_backend")
logger.setLevel(logging.INFO)  # or DEBUG if needed
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
logger.addHandler(console)


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

user_queues = {}
vision_client = vision.ImageAnnotatorClient()

def _extract_socket_id(form, headers):
    return form.get("socket_id") or form.get("socket-id") or headers.get("socket-id")

async def _save_upload(upload):
    clean_name = os.path.basename(upload.filename)
    uid = uuid.uuid4().hex
    dest = os.path.join(UPLOAD_DIR, f"{uid}_{clean_name}")
    data = await upload.read()
    with open(dest, "wb") as f:
        f.write(data)
    return dest, clean_name, uid

def _enqueue_pdf(clean_name, saved_path, uid, parent, socket_id):
    pages = convert_from_path(saved_path, dpi=300)
    for num, page in enumerate(pages, 1):
        jpg_path = os.path.join(TEMP_DIR, f"{uid}_{clean_name}_page_{num}.jpg")
        page.save(jpg_path, "JPEG")
        user_queues[socket_id]["queue"].append({
            "file_name": clean_name,
            "image_path": jpg_path,
            "parent": parent,
            "pdf": True,
            "page": num
        })
    os.remove(saved_path)

def _enqueue_image(clean_name, saved_path, uid, parent, socket_id):
    dest = os.path.join(TEMP_DIR, f"{uid}_{clean_name}")
    shutil.move(saved_path, dest)
    user_queues[socket_id]["queue"].append({
        "file_name": clean_name,
        "image_path": dest,
        "parent": parent,
        "pdf": False,
        "page": 0
    })

def _route_to_extractor(category: str, image_path: str):
    if category == "Weighbridge":
        return extract_weighbridge_fields([image_path])
    if category == "Tax Invoice":
        return extract_tax_invoice_fields([image_path])
    if category == "Delivery Challan":
        return extract_delivery_challan_fields([image_path])
    if category == "LR Copy":
        return extract_lr_copy_fields([image_path])
    if category == "E Way Bill":
        return extract_e_way_bill_fields([image_path])
    return {"error": f"Unsupported category: {category}"}

async def _process_image_job(sid, job):
    await sio.emit("fileStatus", {
        "fileName": job["file_name"], "status": "processing", "result": None,
        "parent": job["parent"], "pdf": job["pdf"], "page": job["page"]
    }, to=sid)

    try:
        with open(job["image_path"], "rb") as f:
            image_bytes = f.read()
        image = vision.Image(content=image_bytes)
        ocr_text = vision_client.document_text_detection(image=image).full_text_annotation.text

        # Debug OCR lines and normalized form
        # from ocr_utils import debug_print_lines, normalize_ascii
        # debug_print_lines(ocr_text, f"OCR Text for {job['file_name']}")
        # logger.info(f"🔡 Normalized OCR: {normalize_ascii(ocr_text)}")

        # Category detection
        category = classify_category(ocr_text)
        logger.info(f"📂 Detected Category: {category} for file {job['file_name']}")
        
        fields = _route_to_extractor(category, job["image_path"])
        result = {**fields, "Category": category, "Category Confidence": "1.0"}
        status = "completed"

    except Exception as e:
        import traceback
        traceback.print_exc()
        status = "failed"
        result = {"error": str(e)}

    await sio.emit("fileStatus", {
        "fileName": job["file_name"], "status": status, "result": result,
        "parent": job["parent"], "pdf": job["pdf"], "page": job["page"]
    }, to=sid)

    try:
        os.remove(job["image_path"])
    except:
        pass


async def _process_user_queue(sid):
    data = user_queues.get(sid)
    if not data or data["is_processing"]:
        return
    data["is_processing"] = True
    while data["queue"]:
        await _process_image_job(sid, data["queue"].pop(0))
    data["is_processing"] = False

@sio.event
def connect(sid, environ):
    user_queues[sid] = {"queue": [], "is_processing": False}

@sio.event
def disconnect(sid):
    data = user_queues.pop(sid, None)
    if data:
        for job in data["queue"]:
            try:
                os.remove(job["image_path"])
            except:
                pass

@app.post("/extractText")
async def extract_text(request: Request):
    form = await request.form()
    socket_id = _extract_socket_id(form, request.headers)
    if not socket_id or socket_id not in user_queues:
        raise HTTPException(status_code=400, detail="Invalid or missing socket_id")
    uploads = form.getlist("images")
    parents = form.getlist("parents[]")
    if not uploads:
        raise HTTPException(status_code=400, detail="No files uploaded")

    for idx, upload in enumerate(uploads):
        saved_path, clean_name, uid = await _save_upload(upload)
        parent = parents[idx] if idx < len(parents) else None
        lower = clean_name.lower()
        if lower.endswith(".pdf"):
            _enqueue_pdf(clean_name, saved_path, uid, parent, socket_id)
        elif lower.endswith((".jpg", ".jpeg", ".png")):
            _enqueue_image(clean_name, saved_path, uid, parent, socket_id)
        else:
            os.remove(saved_path)
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {clean_name}")

    asyncio.create_task(_process_user_queue(socket_id))
    return {"message": "processing_started"}