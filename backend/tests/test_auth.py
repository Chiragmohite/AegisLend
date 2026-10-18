"""Synthetic identities, random keys/passwords, real SQLAlchemy persistence (SQLite)."""
from datetime import datetime, timedelta, timezone
import secrets
import uuid
from unittest.mock import MagicMock
import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import Settings
from app.db import Base, get_session
from app.main import create_app
from app.models import User
from app.security import decode_token, issue_token, verify_password


@pytest.fixture
def auth():
    settings = Settings(_env_file=None, db_password=secrets.token_urlsafe(24),
                        jwt_secret=secrets.token_urlsafe(48))
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    app = create_app(settings)
    def session_override():
        with factory() as session:
            yield session
    app.dependency_overrides[get_session] = session_override
    with TestClient(app) as client:
        yield client, factory, settings
    engine.dispose()


@pytest.fixture
def account():
    return {'email': f'synthetic-{uuid.uuid4().hex}@example.com', 'password': secrets.token_urlsafe(24)}


def register_login(auth, account):
    client, _, _ = auth
    response = client.post('/api/v1/auth/register', json=account)
    assert response.status_code == 201
    response = client.post('/api/v1/auth/login', json=account)
    assert response.status_code == 200
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def test_registration_stores_argon2_hash_and_assigns_customer(auth, account):
    client, factory, _ = auth
    response = client.post('/api/v1/auth/register', json=account)
    assert response.status_code == 201
    assert response.json()['role'] == 'customer'
    assert set(response.json()) == {'id', 'email', 'role'}
    assert account['password'] not in response.text
    with factory() as session:
        user = session.scalar(select(User))
        assert user.password_hash.startswith('$argon2id$')
        assert verify_password(account['password'], user.password_hash)
        assert user.password_hash != account['password']


def test_login_token_claims_expiry_and_private_response(auth, account):
    client, _, settings = auth
    client.post('/api/v1/auth/register', json=account)
    response = client.post('/api/v1/auth/login', json=account)
    assert response.status_code == 200
    body = response.json()
    assert body['token_type'] == 'bearer' and body['expires_in'] == 900
    assert response.headers['cache-control'] == 'no-store'
    claims = jwt.decode(body['access_token'], settings.jwt_secret.get_secret_value(),
                        algorithms=['HS256'], audience=settings.jwt_audience, issuer=settings.jwt_issuer)
    assert claims['exp'] - claims['iat'] == 900
    assert 'role' not in claims and 'password' not in claims
    assert decode_token(body['access_token'], settings) == claims['sub']


def test_invalid_credentials_do_not_reveal_account_existence(auth, account):
    client, _, _ = auth
    client.post('/api/v1/auth/register', json=account)
    unknown = client.post('/api/v1/auth/login', json={**account, 'email': 'missing@example.com'})
    wrong = client.post('/api/v1/auth/login', json={**account, 'password': secrets.token_urlsafe(24)})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()
    assert wrong.headers['www-authenticate'] == 'Bearer'


@pytest.mark.parametrize('path', ['/api/v1/auth/me', '/api/v1/admin/access'])
@pytest.mark.parametrize('header', [None, 'Basic invalid', 'Bearer malformed'])
def test_protected_endpoints_reject_missing_or_invalid_auth(auth, path, header):
    response = auth[0].get(path, headers={'Authorization': header} if header else {})
    assert response.status_code == 401


def test_customer_me_and_admin_denial(auth, account):
    headers = register_login(auth, account)
    assert auth[0].get('/api/v1/auth/me', headers=headers).json()['email'] == account['email']
    assert auth[0].get('/api/v1/admin/access', headers=headers).status_code == 403


def test_database_role_changes_take_effect_for_existing_token(auth, account):
    client, factory, _ = auth
    headers = register_login(auth, account)
    with factory.begin() as session:
        session.scalar(select(User)).role = 'administrator'
    assert client.get('/api/v1/admin/access', headers=headers).status_code == 200
    with factory.begin() as session:
        session.scalar(select(User)).role = 'customer'
    assert client.get('/api/v1/admin/access', headers=headers).status_code == 403


@pytest.mark.parametrize('extra', [{'role': 'administrator'}, {'is_active': True}, {'password_hash': 'injected'}, {'id': 'injected'}])
def test_registration_rejects_privilege_fields(auth, account, extra):
    response = auth[0].post('/api/v1/auth/register', json={**account, **extra})
    assert response.status_code == 422
    assert account['password'] not in response.text
    with auth[1]() as session:
        assert session.scalar(select(User)) is None


@pytest.mark.parametrize('changes', [{'email': 'not-an-email'}, {'password': 'short'}, {'password': 'x' * 129}])
def test_registration_validation_redacts_values(auth, account, changes):
    data = {**account, **changes}
    response = auth[0].post('/api/v1/auth/register', json=data)
    assert response.status_code == 422
    assert data['password'] not in response.text


def test_duplicate_email_case_normalization_and_rollback(auth, account):
    client, _, _ = auth
    assert client.post('/api/v1/auth/register', json=account).status_code == 201
    assert client.post('/api/v1/auth/register', json={**account, 'email': account['email'].upper()}).status_code == 409
    assert client.post('/api/v1/auth/login', json={**account, 'email': account['email'].upper()}).status_code == 200


def test_disabled_and_deleted_accounts_cannot_use_old_tokens(auth, account):
    client, factory, _ = auth
    headers = register_login(auth, account)
    with factory.begin() as session:
        session.scalar(select(User)).is_active = False
    assert client.get('/api/v1/auth/me', headers=headers).status_code == 401
    assert client.post('/api/v1/auth/login', json=account).status_code == 401
    with factory.begin() as session:
        session.delete(session.scalar(select(User)))
    assert client.get('/api/v1/auth/me', headers=headers).status_code == 401


@pytest.mark.parametrize('mutation', ['expired', 'future', 'issuer', 'audience', 'missing-exp', 'wrong-key', 'wrong-alg', 'bad-sub'])
def test_jwt_validation(auth, account, mutation):
    client, factory, settings = auth
    register_login(auth, account)
    with factory() as session:
        user_id = session.scalar(select(User.id))
    now = datetime.now(timezone.utc)
    claims = {'sub': user_id, 'iat': now, 'nbf': now, 'exp': now + timedelta(minutes=15),
              'iss': settings.jwt_issuer, 'aud': settings.jwt_audience, 'jti': str(uuid.uuid4())}
    if mutation == 'expired': claims['exp'] = now - timedelta(seconds=10)
    if mutation == 'future': claims['nbf'] = now + timedelta(minutes=10)
    if mutation == 'issuer': claims['iss'] = 'wrong'
    if mutation == 'audience': claims['aud'] = 'wrong'
    if mutation == 'missing-exp': del claims['exp']
    if mutation == 'bad-sub': claims['sub'] = 'not-a-uuid'
    key = secrets.token_urlsafe(48) if mutation == 'wrong-key' else settings.jwt_secret.get_secret_value()
    token = jwt.encode(claims, key, algorithm='HS384' if mutation == 'wrong-alg' else 'HS256')
    assert client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer ' + token}).status_code == 401


def test_even_a_signed_role_claim_cannot_grant_admin(auth, account):
    client, factory, settings = auth
    headers = register_login(auth, account)
    with factory() as session:
        user_id = session.scalar(select(User.id))
    token = headers['Authorization'].removeprefix('Bearer ')
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=['HS256'], audience=settings.jwt_audience)
    claims['role'] = 'administrator'
    token = jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm='HS256')
    assert client.get('/api/v1/admin/access', headers={'Authorization': 'Bearer ' + token}).status_code == 403


def test_no_signing_key_fails_closed_but_keeps_health(auth, account):
    app = create_app(Settings(_env_file=None, db_password=secrets.token_urlsafe(24), jwt_secret=None))
    with TestClient(app) as client:
        assert client.get('/api/v1/health/live').status_code == 200
        assert client.post('/api/v1/auth/register', json=account).status_code == 503
        assert client.post('/api/v1/auth/login', json=account).status_code == 503
        assert client.get('/api/v1/auth/me').status_code == 503


def test_secret_and_expiry_configuration_validation():
    for kwargs in [{'jwt_secret': 'short'}, {'access_token_minutes': 0}, {'access_token_minutes': 61}]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, db_password=secrets.token_urlsafe(24), **kwargs)
    secret = secrets.token_urlsafe(48)
    settings = Settings(_env_file=None, db_password=secrets.token_urlsafe(24), jwt_secret=secret)
    assert secret not in repr(settings)


def test_auth_database_errors_are_redacted(auth, account):
    client, _, _ = auth
    session = MagicMock()
    secret = secrets.token_urlsafe(24)
    session.scalar.side_effect = OperationalError('query', {}, Exception(secret))
    client.app.dependency_overrides[get_session] = lambda: session
    response = client.post('/api/v1/auth/login', json=account)
    assert response.status_code == 503
    assert secret not in response.text and 'query' not in response.text


def test_authorization_cors_preflight(auth):
    response = auth[0].options('/api/v1/auth/login', headers={
        'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'authorization,content-type'})
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'


def test_no_public_role_mutation_endpoint(auth, account):
    headers = register_login(auth, account)
    assert auth[0].post('/api/v1/auth/me', json={'role': 'administrator'}, headers=headers).status_code == 405
    assert auth[0].get('/api/v1/admin/access', headers=headers).status_code == 403
