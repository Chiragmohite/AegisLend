from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, DateTime, Enum, String, func, true
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class SystemMetadata(Base):
    """Infrastructure marker; contains no customer or financial data."""
    __tablename__ = "system_metadata"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_bin", "mysql_engine": "InnoDB"}
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("customer", "administrator", name="user_role", native_enum=False,
             create_constraint=True, length=13), nullable=False, default="customer", server_default="customer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), server_default=func.now())

# Register later-phase tables while retaining the original User/SystemMetadata definitions.
from app.domain_models import (Profile, Product, Assessment, Application, ApplicationHistory,
    Appointment, KnowledgeDocument, SecurityEvent, RiskAssessment, AuditLog, SecurityReview)
from app.enhancement_models import AuthSession, Incident, IncidentAction, Restriction
