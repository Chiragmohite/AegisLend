"""Persistent sessions. User row locking serializes competing MySQL logins."""
from datetime import timedelta
import hashlib
from fastapi import HTTPException
from sqlalchemy import select,update
from sqlalchemy.exc import IntegrityError
from app.domain_models import utcnow
from app.enhancement_models import AuthSession
from app.models import User

def open_session(db,user,request,settings):
    # Lock an existing parent row even when no session exists yet.
    db.execute(select(User.id).where(User.id==user.id).with_for_update()).scalar_one()
    now=utcnow()
    db.execute(update(AuthSession).where(AuthSession.user_id==user.id,AuthSession.expires_at<=now).values(active_user=None))
    active=db.scalars(select(AuthSession).where(AuthSession.user_id==user.id,AuthSession.revoked_at.is_(None),AuthSession.expires_at>now).with_for_update()).all()
    for row in active:
        if row.challenge_until and row.challenge_until<=now:
            row.revoked_at=now;row.active_user=None
    remaining=[row for row in active if row.revoked_at is None]
    if remaining:
        for row in remaining:
            if row.challenge_until is None:row.challenge_until=now+timedelta(seconds=120)
        db.commit()
        request.state.security_category='session_conflict'
        raise HTTPException(409,'An active session must confirm its identity. This login was rejected; use the existing session or wait for its challenge to expire.')
    row=AuthSession(user_id=user.id,active_user=user.id,expires_at=now+timedelta(minutes=settings.access_token_minutes),device_hash=hashlib.sha256(request.headers.get('user-agent','unknown').encode()).hexdigest())
    db.add(row)
    try:db.flush()
    except IntegrityError:
        db.rollback();request.state.security_category='session_conflict'
        raise HTTPException(409,'A concurrent sign-in won the reservation. This attempt was rejected; retry to initiate identity verification.') from None
    return row
