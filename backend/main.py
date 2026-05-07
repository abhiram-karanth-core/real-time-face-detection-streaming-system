import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_db, get_roi_by_session
from worker import frame_worker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:

    await init_db()
    yield

app = FastAPI(title="MegaAI Face Detection API", lifespan=lifespan)


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/stream")
async def stream(
    websocket: WebSocket,
    session_id: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):

    await websocket.accept()

    try:
        if session_id:
            uuid.UUID(session_id)
        else:
            session_id = str(uuid.uuid4())
    except ValueError:
        session_id = str(uuid.uuid4())

    # Each connection gets its own private queue so frames from different
    # browser sessions are never mixed together.
    local_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
    worker_task = asyncio.create_task(frame_worker(websocket, db, local_queue))

    try:
        while True:
            frame_b64 = await websocket.receive_text()

            # Adaptive frame drop: if the queue is full, silently skip this frame.
            # This keeps latency low - the browser sees the newest possible frame
            # rather than a frames-old result.
            if local_queue.full():
                continue

            await local_queue.put((frame_b64, session_id))

    except WebSocketDisconnect:

        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass  


@app.get("/roi")
async def get_roi(
    session_id: str = Query(..., description="UUID of the streaming session"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all bounding boxes detected during a session, ordered by time.
    Example: GET /roi?session_id=<uuid>
    """
    try:
        uuid.UUID(session_id)  # validate format before hitting the DB
    except ValueError:
        raise HTTPException(status_code=422, detail="session_id must be a valid UUID")

    rows = await get_roi_by_session(db, session_id)
    return {"session_id": session_id, "count": len(rows), "roi": rows}

@app.get("/health")
async def health():
    """Returns 200 OK. Docker Compose and any load balancer can poll this."""
    return {"status": "ok"}