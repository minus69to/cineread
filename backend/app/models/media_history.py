from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MediaHistory(Base):
    __tablename__ = "media_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    user_message: Mapped[str] = mapped_column(Text)
    assistant_response: Mapped[str] = mapped_column(Text)
    recommended_ids: Mapped[str] = mapped_column(Text, default="")  # JSON list of media_ids
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
