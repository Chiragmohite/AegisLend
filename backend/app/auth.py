from typing import Annotated, Literal
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator
from sqlalchemy import select
from app.enhancement_models import AuthSession, Restriction
from app.domain_models import utcnow
from app.session_service import open_session
from app.security import token_session_id
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import Settings
from app.db import get_session
from app.models import User
from app.security import decode_token, hash_password, issue_token, password_hasher, verify_password

router = APIRouter(prefix="/api/v1", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)
SessionDep = Annotated[Session, Depends(get_session)]


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)
    otp: SecretStr | None = Field(default=None,min_length=6,max_length=6)

    @field_validator("email")
    @classmethod
    def canonical_email(cls, value: str) -> str:
        return value.lower()


class Registration(Credentials):
    password: SecretStr = Field(min_length=12, max_length=128)


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    role: Literal["customer", "administrator"]


class TokenView(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


def auth_settings(request: Request) -> Settings:
    settings = request.app.state.settings
    if request.url.path in ('/api/v1/auth/register','/api/v1/auth/login'):
        # Never trust a caller-supplied forwarding header for the rate-limit identity.
        import hashlib
        key=hashlib.sha256((request.client.host if request.client else 'local').encode()).hexdigest()
        if not request.app.state.limiter.allow(key):
            request.state.security_category='rate_limit'
            raise HTTPException(429,'Too many authentication attempts; retry in 60 seconds',headers={'Retry-After':'60'})
    if settings.jwt_secret is None:
        raise HTTPException(503, "Authentication is not configured")
    return settings


SettingsDep = Annotated[Settings, Depends(auth_settings)]


def unauthorized() -> HTTPException:
    return HTTPException(401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})


def current_user(request: Request, session: SessionDep, settings: SettingsDep,
                 credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> User:
    if credentials is None or len(credentials.credentials) > 4096:
        raise unauthorized()
    try:
        user_id = decode_token(credentials.credentials, settings)
    except jwt.InvalidTokenError:
        raise unauthorized()
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized()
    request.state.actor_id = user.id
    sid=token_session_id(credentials.credentials,settings)
    login_session=session.get(AuthSession,sid)
    if login_session is None or login_session.user_id!=user.id or login_session.revoked_at or login_session.expires_at<=utcnow():
        raise unauthorized()
    request.state.session_id=sid
    if login_session.challenge_until and login_session.challenge_until<=utcnow():
        login_session.revoked_at=utcnow();login_session.active_user=None;session.commit()
        request.state.security_category='session_expired_challenge'
        raise unauthorized()
    if request.method not in ('GET','HEAD') and request.url.path not in ('/api/v1/auth/logout','/api/v1/auth/session/confirm'):
        from app.security_policy import mutation_policy
        restricted=session.scalar(select(Restriction.id).where(Restriction.user_id==user.id,Restriction.released_at.is_(None),Restriction.expires_at>utcnow()))
        policy=mutation_policy(bool(login_session.challenge_until),bool(restricted))
        if policy!='allow':request.state.applied_action=policy
        if policy=='require_reauthentication':
            raise HTTPException(403,'Confirm the active-session security challenge before continuing. Your saved drafts are preserved.')
        if policy=='deny_sensitive_operation':
            raise HTTPException(403,'Sensitive operations are temporarily restricted. Contact an administrator for review.')
    return user


UserDep = Annotated[User, Depends(current_user)]


def administrator(user: UserDep) -> User:
    if user.role != "administrator":
        raise HTTPException(403, "Insufficient permissions")
    return user


@router.post("/auth/register", response_model=UserView, status_code=201)
def register(data: Registration, request: Request, session: SessionDep, settings: SettingsDep):
    # Role and activation are exclusively server-assigned, never mass-assigned from JSON.
    user = User(email=str(data.email), password_hash=hash_password(data.password.get_secret_value()),
                role="customer", is_active=True)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if session.scalar(select(User.id).where(User.email == str(data.email))) is not None:
            raise HTTPException(409, "Unable to register with these details") from None
        raise
    session.refresh(user)
    request.state.actor_id=user.id
    request.state.security_category="registration"
    return user


@router.post("/auth/login", response_model=TokenView)
def login(data: Credentials, request: Request, session: SessionDep, settings: SettingsDep):
    import hashlib,hmac
    request.state.login_account_key=hmac.new(settings.jwt_secret.get_secret_value().encode(),str(data.email).encode(),hashlib.sha256).hexdigest()
    user = session.scalar(select(User).where(User.email == str(data.email)))
    request.state.security_category="unknown_account" if user is None else "auth_failure"
    valid = verify_password(data.password.get_secret_value(), user.password_hash if user else None)
    if not valid or user is None or not user.is_active:
        raise unauthorized()
    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password.get_secret_value())
        session.commit()
    from app.enhancement_models import Authenticator
    from app.otp_service import verify as verify_otp
    authenticator=session.get(Authenticator,user.id)
    if authenticator and authenticator.enabled and not verify_otp(session,authenticator,data.otp.get_secret_value() if data.otp else '',settings):raise unauthorized()
    request.state.actor_id=user.id
    request.state.security_category="login_success"
    login_session=open_session(session,user,request,settings)
    session.commit()
    return TokenView(access_token=issue_token(user.id, settings,login_session.id), expires_in=settings.access_token_minutes * 60)


@router.get("/auth/me", response_model=UserView)
def me(user: UserDep):
    return user


@router.get("/admin/access", tags=["Administration"])
def admin_access(user: Annotated[User, Depends(administrator)]):
    """Read-only RBAC proof endpoint; does not execute privileged security actions."""
    return {"access": "granted", "role": user.role}


class ConfirmSession(BaseModel):
    model_config=ConfigDict(extra='forbid',hide_input_in_errors=True)
    password:SecretStr=Field(min_length=1,max_length=128)
    otp:SecretStr|None=Field(default=None,min_length=6,max_length=6)

@router.get('/auth/session')
def session_status(request:Request,user:UserDep,session:SessionDep):
    row=session.get(AuthSession,request.state.session_id)
    from app.enhancement_models import Authenticator
    authenticator=session.get(Authenticator,user.id)
    return {'otp_enabled':bool(authenticator and authenticator.enabled),'id':row.id,'expires_at':row.expires_at.isoformat()+'Z','challenge_until':row.challenge_until.isoformat()+'Z' if row.challenge_until else None,'verification_method':'password_and_authenticator' if authenticator and authenticator.enabled else 'password_reauthentication'}

@router.post('/auth/session/confirm')
def confirm_session(data:ConfirmSession,request:Request,user:UserDep,session:SessionDep):
    from sqlalchemy import update
    from app.ids import audit
    row=session.get(AuthSession,request.state.session_id)
    if row.challenge_until is None:raise HTTPException(409,'No active challenge')
    from app.enhancement_models import Authenticator
    from app.otp_service import verify as verify_otp
    authenticator=session.get(Authenticator,user.id)
    valid=verify_password(data.password.get_secret_value(),user.password_hash)
    if authenticator and authenticator.enabled:valid=valid and verify_otp(session,authenticator,data.otp.get_secret_value() if data.otp else '',request.app.state.settings)
    if not valid:
        session.execute(update(AuthSession).where(AuthSession.id==row.id).values(challenge_attempts=AuthSession.challenge_attempts+1))
        session.commit();session.refresh(row)
        if row.challenge_attempts>=5:row.revoked_at=utcnow();row.active_user=None;session.commit()
        request.state.security_category='auth_failure'
        raise unauthorized()
    changed=session.execute(update(AuthSession).where(AuthSession.id==row.id,AuthSession.revoked_at.is_(None),AuthSession.challenge_until>utcnow(),AuthSession.challenge_attempts<5).values(challenge_until=None,challenge_attempts=0))
    if changed.rowcount!=1:session.rollback();raise unauthorized()
    audit(session,user.id,'session_challenge_verified','session',row.id,request.state.correlation_id)
    session.commit();return {'verified':True,'competing_login':'rejected'}

@router.post('/auth/logout')
def logout_session(request:Request,user:UserDep,session:SessionDep):
    from app.ids import audit
    row=session.get(AuthSession,request.state.session_id);row.revoked_at=utcnow();row.active_user=None
    audit(session,user.id,'session_revoked','session',row.id,request.state.correlation_id)
    session.commit();return {'revoked':True}

class OTPEnrollment(BaseModel):
    model_config=ConfigDict(extra='forbid',hide_input_in_errors=True)
    password:SecretStr=Field(min_length=1,max_length=128)
class OTPVerification(BaseModel):
    model_config=ConfigDict(extra='forbid',hide_input_in_errors=True)
    code:SecretStr=Field(min_length=6,max_length=6)

@router.get('/auth/otp')
def otp_status(user:UserDep,session:SessionDep):
    from app.enhancement_models import Authenticator
    row=session.get(Authenticator,user.id)
    return {'enabled':bool(row and row.enabled)}

@router.post('/auth/otp/enroll')
def otp_enroll(data:OTPEnrollment,request:Request,user:UserDep,session:SessionDep,settings:SettingsDep):
    from app.enhancement_models import Authenticator
    from app.otp_service import generate_secret,cipher
    if not request.app.state.limiter.allow('otp:'+user.id,10):raise HTTPException(429,'Verification limit reached; retry in 60 seconds')
    if not verify_password(data.password.get_secret_value(),user.password_hash):raise unauthorized()
    row=session.get(Authenticator,user.id)
    if row and row.enabled:raise HTTPException(409,'Authenticator already enrolled')
    secret=generate_secret()
    if row is None:row=Authenticator(user_id=user.id);session.add(row)
    row.encrypted_secret=cipher(settings).encrypt(secret.encode()).decode();row.last_step=-1
    session.commit()
    return {'secret':secret,'issuer':'AegisLend Demo','digits':6,'period':30,'algorithm':'SHA1','instruction':'Add this secret manually to your authenticator app, then confirm a code. Do not share it.'}

@router.post('/auth/otp/activate')
def otp_activate(data:OTPVerification,request:Request,user:UserDep,session:SessionDep,settings:SettingsDep):
    from app.enhancement_models import Authenticator
    from app.otp_service import verify
    from app.ids import audit
    if not request.app.state.limiter.allow('otp:'+user.id,10):raise HTTPException(429,'Verification limit reached; retry in 60 seconds')
    row=session.get(Authenticator,user.id)
    if not row or row.enabled or not verify(session,row,data.code.get_secret_value(),settings):raise unauthorized()
    row.enabled=1;audit(session,user.id,'otp_enrolled','user',user.id,request.state.correlation_id);session.commit()
    return {'enabled':True}
