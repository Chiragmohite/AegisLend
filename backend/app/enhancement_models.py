"""Additive session and incident state; no secrets or raw request payloads."""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from app.domain_models import uid, utcnow

class AuthSession(Base):
    __tablename__='auth_sessions'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    expires_at:Mapped[datetime]=mapped_column(DateTime,index=True)
    revoked_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    active_user:Mapped[str|None]=mapped_column(String(36),unique=True,nullable=True)
    device_hash:Mapped[str]=mapped_column(String(64))
    challenge_until:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    challenge_attempts:Mapped[int]=mapped_column(Integer,default=0)

class Incident(Base):
    __tablename__='security_incidents'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    event_id:Mapped[str]=mapped_column(ForeignKey('security_events.id'),unique=True)
    actor_id:Mapped[str|None]=mapped_column(ForeignKey('users.id'),nullable=True,index=True)
    state:Mapped[str]=mapped_column(String(30),default='detected',index=True)
    recommended_action:Mapped[str]=mapped_column(String(40))
    applied_action:Mapped[str]=mapped_column(String(40),default='log')
    policy_version:Mapped[str]=mapped_column(String(40),default='policy-v2')
    version:Mapped[int]=mapped_column(Integer,default=1)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)
    __table_args__=(CheckConstraint("state IN ('detected','triaged','action_recommended','action_applied','under_investigation','resolved','false_positive')",name='ck_incident_state'),)

class IncidentAction(Base):
    __tablename__='incident_actions'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    incident_id:Mapped[str]=mapped_column(ForeignKey('security_incidents.id'),index=True)
    actor_id:Mapped[str|None]=mapped_column(ForeignKey('users.id'),nullable=True)
    action:Mapped[str]=mapped_column(String(40))
    note:Mapped[str]=mapped_column(String(500))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Restriction(Base):
    __tablename__='security_restrictions'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),index=True)
    incident_id:Mapped[str]=mapped_column(ForeignKey('security_incidents.id'))
    expires_at:Mapped[datetime]=mapped_column(DateTime,index=True)
    released_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)

for table in (AuthSession.__table__,Incident.__table__,IncidentAction.__table__,Restriction.__table__):
    table.dialect_options['mysql'].update(charset='utf8mb4',collate='utf8mb4_bin',engine='InnoDB')

class Authenticator(Base):
    __tablename__='authenticators'
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    encrypted_secret:Mapped[str]=mapped_column(String(512))
    enabled:Mapped[int]=mapped_column(Integer,default=0)
    last_step:Mapped[int]=mapped_column(Integer,default=-1)
    __table_args__={'mysql_charset':'utf8mb4','mysql_collate':'utf8mb4_bin','mysql_engine':'InnoDB'}

from sqlalchemy import UniqueConstraint
class AppointmentSeat(Base):
    __tablename__='appointment_seats'
    appointment_id:Mapped[str]=mapped_column(ForeignKey('appointments.id'),primary_key=True)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    starts_at:Mapped[datetime]=mapped_column(DateTime,index=True)
    seat:Mapped[int]=mapped_column(Integer)
    __table_args__=(UniqueConstraint('starts_at','seat',name='uq_slot_seat'),UniqueConstraint('user_id','starts_at',name='uq_customer_slot'),{'mysql_charset':'utf8mb4','mysql_collate':'utf8mb4_bin','mysql_engine':'InnoDB'})
class BookingKey(Base):
    __tablename__='booking_keys'
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    request_key:Mapped[str]=mapped_column(String(36),primary_key=True)
    appointment_id:Mapped[str]=mapped_column(ForeignKey('appointments.id'))
    fingerprint:Mapped[str]=mapped_column(String(64))
    __table_args__={'mysql_charset':'utf8mb4','mysql_collate':'utf8mb4_bin','mysql_engine':'InnoDB'}
class WaitEntry(Base):
    __tablename__='appointment_waitlist'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),index=True)
    starts_at:Mapped[datetime]=mapped_column(DateTime)
    purpose:Mapped[str]=mapped_column(String(120))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    __table_args__=(UniqueConstraint('user_id','starts_at',name='uq_wait_customer_slot'),{'mysql_charset':'utf8mb4','mysql_collate':'utf8mb4_bin','mysql_engine':'InnoDB'})
class Attendance(Base):
    __tablename__='appointment_attendance'
    appointment_id:Mapped[str]=mapped_column(ForeignKey('appointments.id'),primary_key=True)
    outcome:Mapped[str]=mapped_column(String(20))
    note:Mapped[str]=mapped_column(String(500))
    actor_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    __table_args__={'mysql_charset':'utf8mb4','mysql_collate':'utf8mb4_bin','mysql_engine':'InnoDB'}
