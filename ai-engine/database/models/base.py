"""
Base Database Model
===================
Base SQLAlchemy model with common fields and configurations.
"""

import re
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped, mapped_column


@as_declarative()
class Base:
    """Base class for all database models with common fields and table naming."""

    # Primary key UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key UUID"
    )

    # Timestamp when record was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )

    # Timestamp when record was last updated
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (CamelCase -> snake_case_plural)."""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return name if name.endswith('s') else f"{name}s"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary with serialized types."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model fields from dictionary, excluding id and timestamps."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ('id', 'created_at', 'updated_at'):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation showing class name and ID."""
        return f"<{self.__class__.__name__}(id={self.id})>"