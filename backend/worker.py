import asyncio
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from detection import process_frame
from database import store_roi

# the queue sits between the WebSocket receiver (producer) and the
# detection logic (consumer).

# why a queue at all?
#   Receiving frames from the browser is very fast (network I/O).
#   Running mediapipe detection is slower (CPU work).
#   Without a queue, a slow detection would block the WebSocket receiver
#   from reading the next frame, causing the browser to stall.
#   The queue decouples them: the receiver keeps running and drops frames
#   when the queue is full rather than blocking.
#



async def frame_worker(db, frame_queue, broadcast_callback) -> None:
    """
    Consumes frames from frame_queue indefinitely.
    Runs as a background asyncio Task for the lifetime of the WebSocket connection.
    """
    while True:
        # await here yields control to the event loop until a frame is available.
        # This never blocks the thread - other coroutines keep running.
        frame_b64, session_id = await frame_queue.get()

        try:
            # process_frame is CPU-bound (mediapipe + Pillow).
            # asyncio.to_thread() offloads it to the default thread-pool executor
            # so it doesn't block the event loop.
            # each thread gets its own MediaPipe detector via threading.local()
            # in detection.py, making concurrent streams thread-safe.
            annotated_frame, roi = await asyncio.to_thread(process_frame, frame_b64)

            if roi:
                await store_roi(db, session_id, roi)

        except Exception as exc:
            # one bad frame shouldn't kill the session - log and move to next frame
            print(f"[worker] error processing frame: {exc}")
            frame_queue.task_done()
            continue

        try:
            # send the annotated frame back to the browser via the output endpoint.
            await broadcast_callback(session_id, f"data:image/jpeg;base64,{annotated_frame}")
        except Exception:
            # client disconnected — no point continuing, exit the worker loop
            frame_queue.task_done()
            break

        # Always mark the task done so queue.join() works correctly
        frame_queue.task_done()