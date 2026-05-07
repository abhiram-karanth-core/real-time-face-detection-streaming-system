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
# maxsize=10 — if the detection worker falls behind by more than 10 frames,
# new frames are dropped. This is an intentional trade-off: we prefer
# low latency over processing every single frame.
frame_queue: asyncio.Queue[Tuple[str, str]] = asyncio.Queue(maxsize=10)


async def frame_worker(websocket, db, frame_queue) -> None:
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

            # send the annotated frame back to the browser.
            # we prefix with "data:image/jpeg;base64," so the browser can
            # drop it directly into an <img> src attribute.
            await websocket.send_text(f"data:image/jpeg;base64,{annotated_frame}")

        except Exception as exc:

            print(f"[worker] error processing frame: {exc}")

        finally:
            # Always mark the task done so queue.join() works correctly
            frame_queue.task_done()