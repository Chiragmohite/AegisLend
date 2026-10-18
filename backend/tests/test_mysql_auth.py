"""Opt-in real MySQL smoke test; restricted to a dedicated synthetic test database."""
import os
import secrets
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session
from app.config import Settings
from app.db import make_engine
from app.main import create_app
from app.models import User


@pytest.mark.mysql
@pytest.mark.skipif(os.getenv('RUN_MYSQL_AUTH_TESTS') != '1', reason='Requires migrated dedicated MySQL test database')
def test_real_mysql_registration_login_and_roles():
    settings = Settings()
    assert settings.db_name.startswith('aegislend_test_'), 'Use a dedicated aegislend_test_ database'
    assert settings.jwt_secret is not None, 'Configure a random JWT_SECRET'
    engine = make_engine(settings)
    account = {'email': f'synthetic-{uuid.uuid4().hex}@example.com', 'password': secrets.token_urlsafe(24)}
    try:
        with engine.connect() as connection:
            assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == '0007'
        with TestClient(create_app(settings)) as client:
            response = client.post('/api/v1/auth/register', json=account)
            assert response.status_code == 201
            assert response.json()['role'] == 'customer'
            assert client.post('/api/v1/auth/register', json=account).status_code == 409
            response = client.post('/api/v1/auth/login', json=account)
            assert response.status_code == 200
            headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
            assert client.get('/api/v1/auth/me', headers=headers).status_code == 200
            assert client.get('/api/v1/admin/access', headers=headers).status_code == 403
            with Session(engine) as session, session.begin():
                session.scalar(select(User).where(User.email == account['email'])).role = 'administrator'
            assert client.get('/api/v1/admin/access', headers=headers).status_code == 200
    finally:
        try:
            with Session(engine) as session, session.begin():
                session.execute(delete(User).where(User.email == account['email']))
        finally:
            engine.dispose()
