"""Research paper library models."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..core.database import Base


class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(512), nullable=False)
    authors = Column(String(512), nullable=False)
    year = Column(String(8), nullable=False)
    citations = Column(Integer, nullable=False, default=0)
    source = Column(String(255), nullable=False, default="Local Library")
    category = Column(String(128), nullable=False, index=True)
    abstract = Column(Text, nullable=False)
    url = Column(String(2048), nullable=True)
    pdf_url = Column(Text, nullable=True)
    pdf_file_name = Column(String(512), nullable=True)
    tags = Column(JSONB, nullable=False, server_default="[]")
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_research_papers_is_public_created_at", "is_public", "created_at"),
        Index("ix_research_papers_user_id", "user_id"),
    )
