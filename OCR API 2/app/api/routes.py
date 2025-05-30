from app.socket import sio, user_queues
from fastapi import APIRouter, UploadFile, File, Request, Form
import os
import shutil
import tempfile
from pdf2image import convert_from_path
from app.background_worker import trigger_queue_processing

router = APIRouter()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\OCR with Vision\OCR API 2\app\services\vision-api.json"

@router.post("/extractText")
async def extract_text(
    request: Request,
    images: list[UploadFile] = File(...),
    parents: list[str] = Form(None)
):
    socket_id = request.headers.get("socket-id")
    if not socket_id:
        form_data = await request.form()
        socket_id = form_data.get("socket_id")

    if not socket_id or socket_id not in user_queues:
        return {"error": "Socket ID is required or not connected"}

    has_parents = parents is not None and len(parents) > 0
    queue = user_queues[socket_id]["queue"]

    for i, uploaded_file in enumerate(images):
        file_name = os.path.basename(uploaded_file.filename)
        parent = parents[i] if has_parents and i < len(parents) else None
        is_pdf = file_name.lower().endswith(".pdf")

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as tmp:
            shutil.copyfileobj(uploaded_file.file, tmp)
            tmp_path = tmp.name

        if is_pdf:
            try:
                pages = convert_from_path(tmp_path, dpi=300)
                for idx, page in enumerate(pages):
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                        page.save(temp_img.name, "JPEG")
                        queue.append({
                            "fileName": file_name,
                            "parent": parent,
                            "is_pdf": True,
                            "page": idx + 1,
                            "path": temp_img.name
                        })
                os.remove(tmp_path)
            except Exception as e:
                await sio.emit("fileStatus", {
                    "status": "failed",
                    "fileName": file_name,
                    "parent": parent,
                    "pdf": True,
                    "page": 0,
                    "result": str(e)
                }, room=socket_id)
        else:
            queue.append({
                "fileName": file_name,
                "parent": parent,
                "is_pdf": False,
                "page": 0,
                "path": tmp_path
            })
    await trigger_queue_processing(socket_id)
    return {"message": "Files are being processed"}
