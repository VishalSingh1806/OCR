from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp
from app.api.routes import router
from app.socket import sio

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

# API routes
fastapi_app.include_router(router)

# Final ASGI app wrapping FastAPI with Socket.IO
app = ASGIApp(sio, other_asgi_app=fastapi_app)
