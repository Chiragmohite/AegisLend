from contextlib import asynccontextmanager
from typing import Annotated, Literal
from fastapi import Depends, FastAPI, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.auth import router as auth_router
from app.incident_routes import router as incident_router
from app.security_policy import signatures
from app.domain_routes import router as domain_router
from app.ids import Telemetry, RateLimiter
from app.body_limit import BodyLimitMiddleware
from starlette.concurrency import run_in_threadpool
import re
import hashlib
import uuid
from urllib.parse import unquote_plus
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from app.config import Settings
from app.db import get_session, make_engine


class Health(BaseModel):
    status: Literal["ok", "ready", "unavailable"]
    service: str = "aegislend-api"
    database: Literal["ready", "unavailable"] | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        engine.dispose()

    app = FastAPI(title="AegisLend AI", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.telemetry = Telemetry(settings)
    app.state.limiter = RateLimiter(settings)
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Content-Type", "Authorization"])

    app.include_router(auth_router)
    app.include_router(domain_router)
    app.include_router(incident_router)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if request.url.path.endswith('/auth/register') and any(str(e.get('loc', [''])[-1]) in ('role','is_active','password_hash') for e in exc.errors()):
            request.state.security_category='privilege_escalation'
        elif request.url.path.startswith(('/api/v1/applications','/api/v1/eligibility','/api/v1/admin/')):
            request.state.security_category='parameter_tampering'
        # Never echo submitted passwords, tokens, unknown fields or raw request bodies.
        return JSONResponse(status_code=422, content={"detail": "Invalid request data"})

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        return JSONResponse(status_code=503, content={"detail": "Service temporarily unavailable"})

    @app.middleware("http")
    async def private_auth_responses(request: Request, call_next):
        request.state.correlation_id = str(uuid.uuid4())
        request.state.signature_matches=signatures(request.url.path+'?'+request.url.query)
        raw = unquote_plus(str(request.url.path) + '?' + str(request.url.query)).lower()
        if re.search(r"union\s+select|<script|\.\./|or\s+1\s*=\s*1", raw):
            request.state.security_category = 'suspicious_request'
        if request.state.signature_matches:request.state.security_category='suspicious_request'
        if request.url.path.startswith('/api/v1/') and '/health/' not in request.url.path and not app.state.limiter.allow('api:'+hashlib.sha256((request.client.host if request.client else 'local').encode()).hexdigest(),settings.api_rate_limit):
            request.state.security_category='rate_limit'
            response=JSONResponse(status_code=429,content={'detail':'Request limit reached; retry in 60 seconds'},headers={'Retry-After':'60'})
        else:
            response = await call_next(request)
        response.headers['X-Request-ID'] = request.state.correlation_id
        if request.url.path.startswith('/api/v1/') and '/health/' not in request.url.path:
            await run_in_threadpool(app.state.telemetry.record, request, response.status_code, app.state.session_factory)
            response.headers['X-Telemetry-Status'] = 'degraded' if app.state.telemetry.degraded else 'available'

        if request.url.path.startswith('/api/v1/') and (request.headers.get('authorization') or request.url.path.startswith('/api/v1/auth/')):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        response.headers['X-Content-Type-Options']='nosniff'
        return response

    @app.get("/api/v1/health/live", response_model=Health, response_model_exclude_none=True)
    def live():
        return Health(status="ok")

    @app.get("/api/v1/health/ready", response_model=Health,
             responses={503: {"model": Health}})
    def ready(response: Response, session: Annotated[Session, Depends(get_session)]):
        try:
            session.execute(text("SELECT 1"))
            # Verify the baseline migration too, rather than only connectivity.
            marker = session.execute(text(
                "SELECT value FROM system_metadata WHERE `key` = 'schema_phase'"
            )).scalar_one_or_none()
            if marker != "1":
                response.status_code = 503
                return Health(status="unavailable", database="unavailable")
        except SQLAlchemyError:
            response.status_code = 503
            return Health(status="unavailable", database="unavailable")
        return Health(status="ready", database="ready")

    @app.get("/api/v1/health/application", response_model=Health)
    def application_ready(response: Response, session: Annotated[Session, Depends(get_session)]):
        try:
            version=session.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            if version != "0007":
                response.status_code=503
                return Health(status="unavailable",database="unavailable")
        except SQLAlchemyError:
            response.status_code=503
            return Health(status="unavailable",database="unavailable")
        return Health(status="ready",database="ready")

    return app
