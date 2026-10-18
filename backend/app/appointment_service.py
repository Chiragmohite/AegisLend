"""Unique database seats enforce capacity across workers; no frontend locks."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.enhancement_models import AppointmentSeat

def reserve(session,appointment,capacity):
    if session.scalar(select(AppointmentSeat.appointment_id).where(AppointmentSeat.user_id==appointment.user_id,AppointmentSeat.starts_at==appointment.starts_at)):
        raise HTTPException(409,'You already have an appointment in this slot')
    for seat in range(capacity):
        try:
            with session.begin_nested():
                session.add(AppointmentSeat(appointment_id=appointment.id,user_id=appointment.user_id,starts_at=appointment.starts_at,seat=seat));session.flush()
            return
        except IntegrityError:continue
    raise HTTPException(409,'Slot is already booked; choose another')
