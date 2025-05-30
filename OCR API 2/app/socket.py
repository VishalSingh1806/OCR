import socketio


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # or set to your frontend origin in production
)


@sio.event
async def connect(sid, environ):
    print(f"✅ Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"❌ Socket disconnected: {sid}")
