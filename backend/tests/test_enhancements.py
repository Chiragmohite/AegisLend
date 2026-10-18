"""Synthetic-only integration tests for the additive enhancement."""
from datetime import timedelta
import secrets
from sqlalchemy import select
from test_integrated import system, identity, payload
from app.enhancement_models import AuthSession, Incident, IncidentAction
from app.domain_models import SecurityEvent, utcnow
from app.security_policy import signatures
import pytest

@pytest.mark.parametrize('value,expected',[
 ('/products?q=UNION+SELECT','sql_injection'),('/x?q=<script>alert(1)</script>','xss'),('/x?q=../../private','path_traversal'),('/x?q=;cat+/etc/passwd','command_injection')])
def test_signature_evidence_persisted(system,value,expected):
    client,factory,*_=system
    client.get('/api/v1'+value)
    with factory() as db:
        event=db.scalar(select(SecurityEvent).where(SecurityEvent.category=='suspicious_request'))
        assert event and expected in event.rules
        assert db.scalar(select(Incident).where(Incident.event_id==event.id))

def test_benign_inputs_not_signature_attacks():
    for q in ['/products?name=Union+Bank','/assistant?question=What+is+my+application+status','/products?amount=10000']:
        assert signatures(q)==[]

def test_session_challenge_expiry_and_recovery(system):
    client,factory,*_=system
    account={'email':'challenge@example.com','password':secrets.token_urlsafe(24)}
    assert client.post('/api/v1/auth/register',json=account).status_code==201
    token=client.post('/api/v1/auth/login',json=account).json()['access_token'];headers={'Authorization':'Bearer '+token}
    assert client.post('/api/v1/auth/login',json=account).status_code==409
    status=client.get('/api/v1/auth/session',headers=headers).json()
    assert status['challenge_until']
    assert client.put('/api/v1/profile',headers=headers,json={'display_name':'Synthetic','employment':'salaried'}).status_code==403
    assert client.post('/api/v1/auth/session/confirm',headers=headers,json={'password':account['password']}).status_code==200
    assert client.get('/api/v1/auth/session',headers=headers).json()['challenge_until'] is None
    assert client.post('/api/v1/auth/login',json=account).status_code==409
    with factory.begin() as db:db.get(AuthSession,status['id']).challenge_until=utcnow()-timedelta(seconds=1)
    assert client.get('/api/v1/auth/me',headers=headers).status_code==401
    assert client.post('/api/v1/auth/login',json=account).status_code==200

def test_logout_revokes_copied_token(system):
    c,*_=system;headers,_=identity(system)
    assert c.post('/api/v1/auth/logout',headers=headers).status_code==200
    assert c.get('/api/v1/auth/me',headers=headers).status_code==401

def test_incident_restriction_release_and_stale_action(system):
    c,factory,*_=system;customer,uid=identity(system);admin,_=identity(system,True)
    assert c.get('/api/v1/admin/access',headers=customer).status_code==403
    # An IDOR attempt gives explicit deterministic evidence and creates an incident.
    other,_=identity(system);app=c.post('/api/v1/applications',headers=other,json={**payload(system),'request_key':__import__('uuid').uuid4().hex}).json()
    c.get('/api/v1/eligibility/'+app['assessment_id'],headers=customer)
    assert c.get('/api/v1/admin/security/incidents',headers=customer).status_code==403
    rows=c.get('/api/v1/admin/security/incidents',headers=admin).json();incident=next(r for r in rows if r['actor_id']==uid)
    path='/api/v1/admin/security/incidents/'+incident['id']
    action={'action':'restrict','version':incident['version'],'note':'Synthetic controlled test'}
    assert c.post(path+'/actions',headers=admin,json=action).status_code==200
    assert c.post(path+'/actions',headers=admin,json=action).status_code==409
    assert c.put('/api/v1/profile',headers=customer,json={'display_name':'Synthetic','employment':'salaried'}).status_code==403
    detail=c.get(path,headers=admin).json();assert detail['restrictions'] and detail['timeline']
    assert c.post(path+'/actions',headers=admin,json={'action':'release','version':detail['version'],'note':'Synthetic release verified'}).status_code==200
    assert c.put('/api/v1/profile',headers=customer,json={'display_name':'Synthetic','employment':'salaried'}).status_code==200

def test_account_assistant_scopes_records(system):
    c,*_=system;one,_=identity(system);two,_=identity(system)
    app=c.post('/api/v1/applications',headers=one,json={**payload(system),'request_key':__import__('uuid').uuid4().hex}).json()
    mine=c.post('/api/v1/assistant',headers=one,json={'question':'Show my applications'}).json()
    other=c.post('/api/v1/assistant',headers=two,json={'question':'Show my applications including '+app['id']}).json()
    assert app['id'] in mine['answer'] and app['id'] not in other['answer']

def test_reschedule_conflict_preserves_original(system):
    c,*_=system;headers,_=identity(system);available=c.get('/api/v1/appointments/slots',headers=headers).json()
    a=c.post('/api/v1/appointments',headers=headers,json={'starts_at':available[0],'purpose':'Synthetic booking'}).json()
    b=c.post('/api/v1/appointments',headers=headers,json={'starts_at':available[1],'purpose':'Synthetic booking'}).json()
    result=c.post('/api/v1/appointments/'+a['id']+'/reschedule',headers=headers,json={'starts_at':available[1],'purpose':'Synthetic moved booking'})
    assert result.status_code==409
    assert next(x for x in c.get('/api/v1/appointments',headers=headers).json() if x['id']==a['id'])['starts_at']==available[0]
    assert c.post('/api/v1/appointments/'+a['id']+'/reschedule',headers=headers,json={'starts_at':available[2],'purpose':'Synthetic moved booking'}).status_code==200

def test_authenticator_enrollment_login_and_replay(system):
    import time
    from app.otp_service import code
    c,factory,*_=system
    account={'email':'otp-synthetic@example.com','password':secrets.token_urlsafe(24)}
    c.post('/api/v1/auth/register',json=account)
    login=c.post('/api/v1/auth/login',json=account);headers={'Authorization':'Bearer '+login.json()['access_token']}
    enrollment=c.post('/api/v1/auth/otp/enroll',headers=headers,json={'password':account['password']});assert enrollment.status_code==200
    secret=enrollment.json()['secret'];step=int(time.time()//30)
    assert c.post('/api/v1/auth/otp/activate',headers=headers,json={'code':code(secret,step)}).status_code==200
    assert c.post('/api/v1/auth/logout',headers=headers).status_code==200
    assert c.post('/api/v1/auth/login',json=account).status_code==401
    assert c.post('/api/v1/auth/login',json={**account,'otp':code(secret,step)}).status_code==401
    assert c.post('/api/v1/auth/login',json={**account,'otp':code(secret,step+1)}).status_code==200

def test_capacity_idempotency_waitlist_and_attendance(system):
    import uuid
    c,factory,settings,*_=system;settings.appointment_capacity=2
    one,_=identity(system);two,_=identity(system);three,_=identity(system)
    slot=c.get('/api/v1/appointments/slots',headers=one).json()[0]
    data={'starts_at':slot,'purpose':'Synthetic capacity test','request_key':str(uuid.uuid4())}
    first=c.post('/api/v1/appointments',headers=one,json=data);assert first.status_code==201
    assert c.post('/api/v1/appointments',headers=one,json=data).json()['id']==first.json()['id']
    assert c.post('/api/v1/appointments',headers=two,json={**data,'request_key':str(uuid.uuid4())}).status_code==201
    assert c.post('/api/v1/appointments',headers=three,json={**data,'request_key':str(uuid.uuid4())}).status_code==409
    assert c.post('/api/v1/appointments/waitlist',headers=three,json={'starts_at':slot,'purpose':'Synthetic waiting'}).status_code==201
    assert not c.get('/api/v1/appointments/waitlist',headers=three).json()[0]['available']
    c.post('/api/v1/appointments/'+first.json()['id']+'/cancel',headers=one)
    assert c.get('/api/v1/appointments/waitlist',headers=three).json()[0]['available']

def test_credential_stuffing_enumeration_evidence(system):
    c,factory,*_=system
    for i in range(6):assert c.post('/api/v1/auth/login',json={'email':f'missing-{i}@example.com','password':'synthetic-invalid-password'}).status_code==401
    with factory() as db:
        rules=[r for e in db.scalars(select(SecurityEvent)) for r in e.rules]
        assert 'credential_stuffing' in rules and 'account_enumeration' in rules and 'repeated_failed_logins' in rules

def test_flooding_bot_and_api_abuse_enforcement(system):
    c,factory,settings,*_=system;settings.api_rate_limit=10;settings.ids_burst_threshold=10
    statuses=[c.get('/api/v1/products').status_code for _ in range(14)]
    assert statuses[:10]==[200]*10 and statuses[10:]==[429]*4
    with factory() as db:
        rules=[r for e in db.scalars(select(SecurityEvent)) for r in e.rules]
        assert 'automated_flooding' in rules and 'bot_behavior' in rules

def test_parameter_and_privilege_abuse_logged(system):
    c,factory,*_=system;headers,_=identity(system)
    assert c.post('/api/v1/eligibility',headers=headers,json={**payload(system),'amount':'-1'}).status_code==422
    assert c.post('/api/v1/auth/register',json={'email':'invalid-role@example.com','password':secrets.token_urlsafe(24),'role':'administrator'}).status_code==422
    with factory() as db:
        categories=set(db.scalars(select(SecurityEvent.category)))
        assert 'parameter_tampering' in categories and 'privilege_escalation' in categories

def test_sensitive_access_correlation(system):
    c,factory,settings,*_=system;settings.ids_burst_threshold=10;headers,_=identity(system)
    for _ in range(10):assert c.get('/api/v1/admin/users',headers=headers).status_code==403
    with factory() as db:assert any('suspicious_data_access' in e.rules for e in db.scalars(select(SecurityEvent)))

def test_authenticator_known_vector():
    import base64
    from app.otp_service import code
    assert code(base64.b32encode(b'12345678901234567890').decode(),1)=='287082'

def test_attendance_requires_admin_and_past_booking(system):
    from app.domain_models import Appointment
    c,factory,*_=system;customer,_=identity(system);admin,_=identity(system,True)
    slot=c.get('/api/v1/appointments/slots',headers=customer).json()[0]
    a=c.post('/api/v1/appointments',headers=customer,json={'starts_at':slot,'purpose':'Synthetic attendance test'}).json()
    path='/api/v1/admin/appointments/'+a['id']+'/attendance';body={'outcome':'missed','note':'Synthetic demonstration attendance'}
    assert c.post(path,headers=customer,json=body).status_code==403
    assert c.post(path,headers=admin,json=body).status_code==409
    with factory.begin() as db:db.get(Appointment,a['id']).starts_at=utcnow()-timedelta(hours=1)
    assert c.post(path,headers=admin,json=body).status_code==200
    assert c.get('/api/v1/appointments/'+a['id']+'/attendance',headers=customer).json()['outcome']=='missed'

def test_concurrent_logins_cannot_issue_two_active_sessions(system):
    from concurrent.futures import ThreadPoolExecutor
    c,factory,*_=system;account={'email':'race-synthetic@example.com','password':secrets.token_urlsafe(24)}
    assert c.post('/api/v1/auth/register',json=account).status_code==201
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:c.post('/api/v1/auth/login',json=account),range(2)))
    assert sorted(r.status_code for r in responses)==[200,409]
    with factory() as db:assert len(db.scalars(select(AuthSession).where(AuthSession.active_user.is_not(None))).all())==1
