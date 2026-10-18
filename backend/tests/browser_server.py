"""Playwright-only server. Always creates a new temporary SQLite database, never uses DB_* settings."""
from pathlib import Path
import os
import secrets
import tempfile
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import Settings
from app.db import get_session
from app.main import create_app
from app.models import User
from app.seed import seed
from app.security import hash_password


def create():
    password=os.environ.get('AEGIS_E2E_PASSWORD')
    if not password:raise RuntimeError('This server is only launched by the E2E runner')
    temporary=Path(tempfile.mkdtemp(prefix='aegislend-e2e-'))
    engine=create_engine('sqlite:///'+str(temporary/'synthetic.sqlite'),connect_args={'check_same_thread':False})
    settings=Settings(_env_file=None,db_password=secrets.token_urlsafe(32),jwt_secret=secrets.token_urlsafe(48),ids_model_path=temporary/'model.joblib',auth_rate_limit=1000)
    config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
    with engine.begin() as connection:
        config.attributes['connection']=connection;command.upgrade(config,'head')
    factory=sessionmaker(engine,expire_on_commit=False)
    with factory() as session:
        seed(session,settings)
        session.add(User(email='synthetic-admin@example.com',password_hash=hash_password(password),role='administrator',is_active=True));session.commit()
    app=create_app(settings);app.state.session_factory=factory
    def sessions():
        with factory() as session:yield session
    app.dependency_overrides[get_session]=sessions
    return app
