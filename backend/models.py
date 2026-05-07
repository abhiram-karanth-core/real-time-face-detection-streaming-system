import uuid
from sqlalchemy import Column, Integer, Float, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ROIData(Base):
    """
    One row per detected face per frame.
    session_id  — groups all frames from one browser connection together.
    frame_id    — unique ID for this specific frame (generated in detection.py).
    x, y        — top-left pixel of the bounding box.
    width, height — box dimensions in pixels.
    confidence  — mediapipe detection confidence score (0.0 – 1.0).
    detected_at — auto-set by the DB on insert.
    """
    __tablename__ = "roi_data"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    session_id  = Column(UUID(as_uuid=True), nullable=False, index=True)
    frame_id    = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    x           = Column(Integer, nullable=False)
    y           = Column(Integer, nullable=False)
    width       = Column(Integer, nullable=False)
    height      = Column(Integer, nullable=False)
    confidence  = Column(Float, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())