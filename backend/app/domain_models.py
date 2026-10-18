"""Domain entities added after the immutable Phase 2 migration."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, Numeric, JSON, ForeignKey, UniqueConstraint, CheckConstraint, func, case
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


def uid(): return str(uuid.uuid4())
def utcnow(): return datetime.now(timezone.utc).replace(tzinfo=None)


class Profile(Base):
    __tablename__ = 'profiles'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80), default='Demo customer')
    employment: Mapped[str] = mapped_column(String(30), default='salaried')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Product(Base):
    __tablename__ = 'loan_products'
    __table_args__ = (CheckConstraint('min_amount > 0 AND max_amount >= min_amount', name='ck_product_amount'), CheckConstraint('min_months > 0 AND max_months >= min_months', name='ck_product_tenure'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)
    product_type: Mapped[str] = mapped_column(String(30))
    min_amount: Mapped[Decimal] = mapped_column(Numeric(14,2))
    max_amount: Mapped[Decimal] = mapped_column(Numeric(14,2))
    min_months: Mapped[int] = mapped_column(Integer)
    max_months: Mapped[int] = mapped_column(Integer)
    annual_rate: Mapped[Decimal] = mapped_column(Numeric(6,3))
    min_income: Mapped[Decimal] = mapped_column(Numeric(14,2))
    max_dti: Mapped[Decimal] = mapped_column(Numeric(5,4), default=Decimal('0.4'))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Assessment(Base):
    __tablename__ = 'eligibility_assessments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey('loan_products.id'))
    inputs: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Application(Base):
    __tablename__ = 'loan_applications'
    __table_args__ = (UniqueConstraint('user_id','request_key',name='uq_application_request'), CheckConstraint("status IN ('draft','submitted','under_review','approved','rejected','cancelled')", name='ck_application_status'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey('loan_products.id'))
    assessment_id: Mapped[str] = mapped_column(ForeignKey('eligibility_assessments.id'), unique=True)
    request_key: Mapped[str] = mapped_column(String(36))
    fingerprint: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(14,2))
    months: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    history: Mapped[list['ApplicationHistory']] = relationship(order_by=lambda: (ApplicationHistory.created_at, case({'draft':0,'submitted':1,'under_review':2,'approved':3,'rejected':3,'cancelled':3}, value=ApplicationHistory.status)), lazy='selectin')


class ApplicationHistory(Base):
    __tablename__ = 'application_history'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    application_id: Mapped[str] = mapped_column(ForeignKey('loan_applications.id'), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String(500), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Appointment(Base):
    __tablename__ = 'appointments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    active_slot: Mapped[datetime | None] = mapped_column(DateTime, unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='booked')
    purpose: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (CheckConstraint("status IN ('booked','cancelled')", name='ck_appointment_status'),)


class KnowledgeDocument(Base):
    __tablename__ = 'knowledge_documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(160))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    content: Mapped[str] = mapped_column(Text)
    chunks: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default='local_ready')
    error: Mapped[str | None] = mapped_column(String(160), nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SecurityEvent(Base):
    __tablename__ = 'security_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    features: Mapped[dict] = mapped_column(JSON)
    rules: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class RiskAssessment(Base):
    __tablename__ = 'risk_assessments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey('security_events.id'), unique=True)
    score: Mapped[int] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(20))
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    explanation: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class SecurityReview(Base):
    __tablename__ = 'security_reviews'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey('security_events.id'), unique=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

# MySQL string foreign keys must share the existing users table's binary collation.
for _table in (Profile.__table__, Product.__table__, Assessment.__table__, Application.__table__, ApplicationHistory.__table__, Appointment.__table__, KnowledgeDocument.__table__, SecurityEvent.__table__, RiskAssessment.__table__, AuditLog.__table__, SecurityReview.__table__):
    _table.dialect_options['mysql']['charset']='utf8mb4'
    _table.dialect_options['mysql']['collate']='utf8mb4_bin'
    _table.dialect_options['mysql']['engine']='InnoDB'
