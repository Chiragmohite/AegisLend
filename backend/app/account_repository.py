"""Explicitly scoped reads used by account services. No prompt-derived owner identifiers."""
from sqlalchemy import select
from app.domain_models import Application, Appointment


def recent_applications(session, user_id):
    return session.scalars(select(Application).where(Application.user_id==user_id).order_by(Application.created_at.desc()).limit(10)).all()


def recent_appointments(session, user_id):
    return session.scalars(select(Appointment).where(Appointment.user_id==user_id).order_by(Appointment.starts_at.desc()).limit(10)).all()
