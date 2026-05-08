import os
import uuid
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, distinct

from models import Base, ROIData


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/face_detection"
)

ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)

engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    import asyncio
    for attempt in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database ready.")
            return
        except Exception as e:
            print(f"Waiting for database... (attempt {attempt + 1}/10)")
            await asyncio.sleep(3)
    raise RuntimeError("Could not connect to database after 10 attempts.")


async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields a DB session and closes it when the
    request/WebSocket handler finishes, even on exceptions.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def store_roi(session: AsyncSession, session_id: str, roi: Dict[str, Any]) -> None:
    """Insert one ROI row. Called by the frame worker after each detection."""
    record = ROIData(
        session_id=uuid.UUID(session_id),
        frame_id=uuid.UUID(roi["frame_id"]),
        x=roi["x"],
        y=roi["y"],
        width=roi["width"],
        height=roi["height"],
        confidence=roi.get("confidence"),
    )
    session.add(record)
    await session.commit()


async def get_roi_by_session(session: AsyncSession, session_id: str) -> List[Dict[str, Any]]:
    """Return all ROI rows for a session, ordered oldest-first."""
    result = await session.execute(
        select(ROIData)
        .where(ROIData.session_id == uuid.UUID(session_id))
        .order_by(ROIData.detected_at)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "session_id": str(r.session_id),
            "frame_id": str(r.frame_id),
            "x": r.x,
            "y": r.y,
            "width": r.width,
            "height": r.height,
            "confidence": r.confidence,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
        }
        for r in rows
    ]


async def get_all_sessions(session: AsyncSession) -> List[str]:
    """Return a list of all distinct session_ids."""
    result = await session.execute(select(distinct(ROIData.session_id)))
    rows = result.scalars().all()
    return [str(r) for r in rows]