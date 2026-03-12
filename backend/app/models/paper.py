from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, UUID, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from app.db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime


class Paper(Base):
	__tablename__ = "papers"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	title = Column(Text, nullable=False)
	abstract = Column(Text)
	doi = Column(Text)
	arxiv_id = Column(Text)
	primary_field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
	primary_subfield_id = Column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
	subjects = Column(ARRAY(Text))  # TODO: To be removed and replaced with M:M mapping paper_fields
	categories = Column(ARRAY(Text))  # TODO: To be removed and replaced with M:M mapping paper_fields
	pdf_url = Column(Text)
	published_date = Column(DateTime)
	submitted_date = Column(DateTime)
	updated_date = Column(DateTime)
	status = Column(Text)
	extracted_text = Column(Text)
	text_chunks = Column(JSONB)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	# Relationships
	articles = relationship("Article", back_populates="paper", cascade="all, delete-orphan")
	authors = relationship("PaperAuthor", back_populates="paper")

	primary_field = relationship(
		"Field",
		foreign_keys=[primary_field_id],
		back_populates="papers_with_primary_field"
	)
	primary_subfield = relationship(
		"Field",
		foreign_keys=[primary_subfield_id],
		back_populates="papers_with_primary_subfield"
	)
