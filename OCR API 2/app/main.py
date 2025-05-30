from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp
from app.api.routes import router
from app.socket import sio
import asyncio
from app.background_worker import worker_loop

# FastAPI app
fastapi_app = FastAPI(title="OCR Extraction API")

# CORS setup
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fastapi_app.on_event("startup")
async def startup_event():
    asyncio.create_task(worker_loop())


# API routes
fastapi_app.include_router(router)

# Final ASGI app wrapping FastAPI with Socket.IO
app = ASGIApp(sio, other_asgi_app=fastapi_app)
