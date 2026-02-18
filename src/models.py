import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, JSON, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

_PAYLOAD_TYPE = JSON().with_variant(JSONB(), "postgresql")

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payload: Mapped[dict] = mapped_column(_PAYLOAD_TYPE, nullable=False)
    valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class WebhookData(Base):
    __tablename__ = "webhook_data"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    id_venda: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    payload: Mapped[dict] = mapped_column(_PAYLOAD_TYPE, nullable=False)
