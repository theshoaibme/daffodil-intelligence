from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.sql import func

from ..core.database import Base


class SimulationLayout(Base):
    """Per-user agent flow canvas layout (custom + default positions)."""

    __tablename__ = "simulation_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    custom_layout = Column(JSON, nullable=True)
    default_layout = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
