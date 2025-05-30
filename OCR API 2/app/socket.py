import socketio

# Add this at the top
user_queues = {}


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # or set to your frontend origin in production
)


@sio.event
async def connect(sid, environ):
    print(f"✅ Socket connected: {sid}")
    user_queues[sid] = {"queue": [], "isProcessing": False}

@sio.event
async def disconnect(sid):
    print(f"❌ Socket disconnected: {sid}")
    user_queues.pop(sid, None)
