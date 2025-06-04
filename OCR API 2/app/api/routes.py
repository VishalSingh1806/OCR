import os
import shutil
import tempfile
import logging

from fastapi import APIRouter, UploadFile, File, Request, Form
from pdf2image import convert_from_path

from app.socket import sio, user_queues
from app.background_worker import trigger_queue_processing

router = APIRouter()

# ──────────────────────────────────────────────────────────────────────────────
# Configure logging for this module
# ──────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Make sure your GOOGLE_APPLICATION_CREDENTIALS is correct for Vision API
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API 2\app\services\vision-api.json"


@router.post("/extractText")
async def extract_text(
    request: Request,
    images: list[UploadFile] = File(...),
    parents: list[str] = Form(None),  # FastAPI will only fill this if the field is exactly "parents"
):
    """
    1) Extract socket_id (either from header or from a form‐field named "socket_id").
    2) Re‐read the entire form to catch any "parents[]" entries if the browser sent them.
    3) Normalize whitespace in each parent name so that "WB73B6961  30-1" ➝ "WB73B6961 30-1".
    4) Enqueue each page (for PDFs) or each image into the background queue.
    5) Return immediately; later, the background worker will emit per‐page results over Socket.IO.
    """

    # ──────────────────────────────────────────────────────────────────────────────
    # 1) Extract socket_id
    # ──────────────────────────────────────────────────────────────────────────────
    socket_id = request.headers.get("socket-id")
    if not socket_id:
        form_data = await request.form()
        socket_id = form_data.get("socket_id")

    logger.debug(f"Received /extractText call. Raw header socket-id: {request.headers.get('socket-id')!r}")
    logger.debug(f"Resolved socket_id from header or form: {socket_id!r}")

    # ──────────────────────────────────────────────────────────────────────────────
    # 2) Validate socket_id
    # ──────────────────────────────────────────────────────────────────────────────
    if not socket_id or socket_id not in user_queues:
        logger.warning(f"extract_text: Missing or invalid socket_id: {socket_id!r}")
        return {"error": "Socket ID is required or not connected"}

    # ──────────────────────────────────────────────────────────────────────────────
    # 3) If `parents` wasn’t auto‐filled by FastAPI, explicitly look for "parents[]" in the raw form
    # ──────────────────────────────────────────────────────────────────────────────
    form_data = await request.form()  # read entire form, so we can do form_data.getlist("parents[]")
    if (not parents or len(parents) == 0) and "parents[]" in form_data:
        try:
            parents = form_data.getlist("parents[]")
        except Exception:
            # In rare cases fall back to scanning multi_items()
            raw = [(k, v) for (k, v) in form_data.multi_items() if k == "parents[]"]
            parents = [v for (k, v) in raw]

    has_parents = parents is not None and len(parents) > 0
    logger.debug(f"Has parents? {has_parents}. Parents list: {parents!r}")

    queue = user_queues[socket_id]["queue"]
    logger.debug(f"Current queue length before appending: {len(queue)}")

    # ──────────────────────────────────────────────────────────────────────────────
    # 4) Process each uploaded file (PDF or image)
    # ──────────────────────────────────────────────────────────────────────────────
    for i, uploaded_file in enumerate(images):
        file_name = os.path.basename(uploaded_file.filename)

        # ──────────────────────────────────────────────────────────────────────────
        # 4a) Normalize whitespace in the incoming parent name
        #    (collapse any run of multiple spaces → single space, then strip edges)
        # ──────────────────────────────────────────────────────────────────────────
        raw_parent = parents[i] if (has_parents and i < len(parents)) else None
        if raw_parent is not None:
            # e.g. "WB73B6961  30-1" → "WB73B6961 30-1"
            parent = " ".join(raw_parent.strip().split())
        else:
            parent = None

        is_pdf = file_name.lower().endswith(".pdf")
        logger.debug(f"Processing uploaded file #{i}: file_name={file_name!r}, parent={parent!r}, is_pdf={is_pdf}")

        # ──────────────────────────────────────────────────────────────────────────
        # 4b) Save the UploadFile to a temporary file
        # ──────────────────────────────────────────────────────────────────────────
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as tmp:
                shutil.copyfileobj(uploaded_file.file, tmp)
                tmp_path = tmp.name
            logger.debug(f"Saved '{file_name}' to temporary path '{tmp_path}'")
        except Exception as e:
            logger.error(f"Error saving uploaded file '{file_name}' to temp: {e}", exc_info=True)
            # Emit a failure event right away and skip enqueueing
            await sio.emit(
                "fileStatus",
                {
                    "status": "failed",
                    "fileName": file_name,
                    "parent": parent,
                    "pdf": is_pdf,
                    "page": 0,
                    "result": f"Failed to write temp file: {str(e)}",
                },
                room=socket_id,
            )
            continue

        # ──────────────────────────────────────────────────────────────────────────
        # 4c) If it's a PDF, convert each page → JPEG and enqueue one job per page
        # ──────────────────────────────────────────────────────────────────────────
        if is_pdf:
            try:
                logger.debug(f"Starting PDF→JPEG conversion for '{file_name}' at '{tmp_path}'")
                # pages = convert_from_path(tmp_path, dpi=300)
                try:
                    pages = convert_from_path(tmp_path, dpi=300)
                except Exception as e:
                    # Emit a “failed” event for all pages
                    await sio.emit("fileStatus", {
                        "status": "failed",
                        "fileName": file_name,
                        "parent": parent,
                        "pdf": True,
                        "page": 0,
                        "result": f"PDF→Image conversion error: {str(e)}"
                    }, room=socket_id)
                    continue

                logger.info(f"Converted PDF '{file_name}' into {len(pages)} page-images")

                for idx, page in enumerate(pages):
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                        page.save(temp_img.name, "JPEG")
                        page_path = temp_img.name
                    logger.debug(
                        f"  PDF '{file_name}', page {idx+1}: saved JPEG to '{page_path}'"
                    )

                    job = {
                        "fileName": file_name,
                        "parent": parent,
                        "is_pdf": True,
                        "page": idx + 1,
                        "path": page_path,
                    }
                    queue.append(job)
                    logger.debug(f"  Enqueued job for PDF page: {job}")

                # Delete the original PDF temp
                try:
                    os.remove(tmp_path)
                    logger.debug(f"Deleted temporary PDF file '{tmp_path}'")
                except Exception as rm_err:
                    logger.warning(f"Failed to delete temp PDF '{tmp_path}': {rm_err}")

            except Exception as e:
                logger.exception(f"PDF conversion failed for '{file_name}': {e}")
                await sio.emit(
                    "fileStatus",
                    {
                        "status": "failed",
                        "fileName": file_name,
                        "parent": parent,
                        "pdf": True,
                        "page": 0,
                        "result": f"PDF conversion error: {str(e)}",
                    },
                    room=socket_id,
                )
        else:
            # ──────────────────────────────────────────────────────────────────────────
            # 4d) Non‐PDF (image): just enqueue a single‐image job
            # ──────────────────────────────────────────────────────────────────────────
            job = {
                "fileName": file_name,
                "parent": parent,
                "is_pdf": False,
                "page": 0,
                "path": tmp_path,
            }
            queue.append(job)
            logger.debug(f"Enqueued image job: {job}")

    # ──────────────────────────────────────────────────────────────────────────────
    # 5) Trigger the background worker
    # ──────────────────────────────────────────────────────────────────────────────
    logger.info(f"Finished enqueuing {len(images)} items. Queue length is now {len(queue)}")
    logger.debug(f"Triggering background processing for socket_id '{socket_id}'")
    await trigger_queue_processing(socket_id)
    logger.info(f"trigger_queue_processing returned for socket_id '{socket_id}'")

    return {"message": "Files are being processed"}
