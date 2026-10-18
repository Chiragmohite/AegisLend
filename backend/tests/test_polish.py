"""Approved enhancement: real HTTP flows against an isolated synthetic database."""
import secrets
import uuid
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, func
from test_integrated import system, identity, payload
from app.domain_models import Application, Assessment, AuditLog, SecurityEvent, utcnow
from app.enhancement_models import Incident, AuthSession, Restriction
from app.security_policy import allowed_actions, mutation_policy


def draft(system,headers):
    return system[0].post('/api/v1/applications',headers=headers,json={**payload(system),'request_key':str(uuid.uuid4())}).json()


def test_draft_edit_snapshot_ownership_and_lifecycle(system):
    c,factory,*_=system;one,uid=identity(system);other,_=identity(system);admin,_=identity(system,True)
    app=draft(system,one);old=app['assessment_id'];path='/api/v1/applications/'+app['id']
    data={**payload(system),'amount':'120000','version':1}
    assert c.put(path,headers=other,json=data).status_code==404
    assert c.put(path,headers=admin,json=data).status_code==403
    updated=c.put(path,headers=one,json=data);assert updated.status_code==200,updated.text
    row=updated.json();assert row['version']==2 and row['assessment_id']!=old and row['status']=='draft'
    assert c.get('/api/v1/eligibility/'+old,headers=one).json()['inputs']['amount']=='100000'
    assert c.get('/api/v1/eligibility/'+row['assessment_id'],headers=one).json()['inputs']['amount']=='120000'
    assert c.put(path,headers=one,json=data).status_code==409
    assert c.post(path+'/transition',headers=one,json={'status':'submitted','version':2}).status_code==200
    assert c.put(path,headers=one,json={**data,'version':3}).status_code==409
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Assessment).where(Assessment.user_id==uid))==2
        assert db.scalar(select(AuditLog).where(AuditLog.event_type=='application_draft_updated',AuditLog.actor_id==uid))


def test_concurrent_draft_edits_one_winner(system):
    c,_,*_=system;headers,_=identity(system);app=draft(system,headers)
    data={**payload(system),'version':1}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda amount:c.put('/api/v1/applications/'+app['id'],headers=headers,json={**data,'amount':amount}),['110000','120000']))
    assert sorted(r.status_code for r in responses)==[200,409]


def test_dashboard_aggregates_owned_records_and_filter(system):
    c,*_=system;one,_=identity(system);two,_=identity(system)
    draft(system,one);draft(system,one);draft(system,two)
    response=c.get('/api/v1/dashboard',headers=one)
    assert response.status_code==200 and response.json()['application_counts']=={'draft':2}
    assert len(response.json()['recent_applications'])==2
    assert c.get('/api/v1/dashboard').status_code==401
    assert c.get('/api/v1/applications?status=submitted',headers=one).json()==[]
    assert c.get('/api/v1/applications?status=invalid',headers=one).status_code==422
    assert response.headers['cache-control']=='no-store'


def test_challenge_blocks_factor_changes_and_preserves_draft(system):
    c,*_=system;account={'email':'challenge-polish@example.com','password':secrets.token_urlsafe(24)}
    c.post('/api/v1/auth/register',json=account)
    h={'Authorization':'Bearer '+c.post('/api/v1/auth/login',json=account).json()['access_token']}
    app=draft(system,h)
    assert c.post('/api/v1/auth/login',json=account).status_code==409
    assert c.post('/api/v1/auth/otp/enroll',headers=h,json={'password':account['password']}).status_code==403
    assert c.put('/api/v1/applications/'+app['id'],headers=h,json={**payload(system),'version':1}).status_code==403
    assert c.get('/api/v1/applications/'+app['id'],headers=h).json()['version']==1
    assert c.post('/api/v1/auth/session/confirm',headers=h,json={'password':account['password']}).status_code==200
    assert c.put('/api/v1/applications/'+app['id'],headers=h,json={**payload(system),'version':1}).status_code==200


def test_incident_lifecycle_reauthentication_and_expiring_restriction(system):
    c,factory,*_=system;customer,uid=identity(system);other,_=identity(system);admin,_=identity(system,True)
    app=draft(system,other)
    c.get('/api/v1/applications/'+app['id'],headers=customer)
    row=next(r for r in c.get('/api/v1/admin/security/incidents',headers=admin).json() if r['actor_id']==uid)
    path='/api/v1/admin/security/incidents/'+row['id'];sid=c.get('/api/v1/auth/session',headers=customer).json()['id']
    def act(action,version,**kw):return c.post(path+'/actions',headers=admin,json={'action':action,'version':version,'note':'Synthetic authorized investigation',**kw})
    changed=act('require_reauthentication',row['version'],session_id=sid);assert changed.status_code==200,changed.text
    assert c.get('/api/v1/auth/session',headers=customer).json()['challenge_until']
    assert act('triage',changed.json()['version']).status_code==409
    assert act('require_reauthentication',changed.json()['version'],session_id=sid).status_code==409
    restricted=act('restrict',changed.json()['version']);assert restricted.status_code==200
    assert act('restrict',restricted.json()['version']).status_code==409
    summary=c.get('/api/v1/admin/security/summary',headers=admin).json();assert summary['active_restrictions']==1 and summary['active_challenges']==1
    with factory.begin() as db:
        db.get(AuthSession,sid).challenge_until=None
        restriction=db.scalar(select(Restriction).where(Restriction.incident_id==row['id']));restriction.expires_at=utcnow()-timedelta(seconds=1)
    assert c.put('/api/v1/profile',headers=customer,json={'display_name':'Synthetic recovery','employment':'salaried'}).status_code==200
    resolved=act('resolve',restricted.json()['version']);assert resolved.status_code==200
    assert act('investigate',resolved.json()['version']).status_code==409
    assert set(resolved.json()['allowed_actions'])=={'note','release'}
    with factory() as db:assert db.scalar(select(AuditLog).where(AuditLog.event_type=='incident_require_reauthentication'))


def test_policy_never_restricts_from_ml_score_alone():
    assert mutation_policy(False,False)=='allow'
    assert mutation_policy(True,False)=='require_reauthentication'
    assert mutation_policy(False,True)=='deny_sensitive_operation'
    assert 'triage' not in allowed_actions('action_applied')


@pytest.mark.parametrize('attack,benign,rule',[
 ('UNION SELECT secret','Union education policy','sql_injection'),
 ('<script>alert(1)</script>','How are scripts reviewed?','xss'),
 ('../../private','Loan folder overview','path_traversal'),
 (';cat /etc/passwd','Describe cat ownership expenses','command_injection'),
])
def test_signature_pair_sanitized_persistence_and_no_execution(system,attack,benign,rule):
    c,factory,*_=system
    normal=c.get('/api/v1/products',params={'q':benign});assert normal.status_code==200
    with factory() as db:assert db.scalar(select(func.count()).select_from(SecurityEvent))==0
    response=c.get('/api/v1/products',params={'q':attack});assert response.status_code==200
    assert response.json()==normal.json() # unused query never becomes SQL, shell, or a path
    with factory() as db:
        event=db.scalar(select(SecurityEvent).where(SecurityEvent.category=='suspicious_request'))
        assert event and rule in event.rules
        incident=db.scalar(select(Incident).where(Incident.event_id==event.id))
        assert incident and incident.recommended_action=='investigate' and incident.applied_action=='log'
        audit=db.scalar(select(AuditLog).where(AuditLog.target_id==event.id))
        assert attack not in str(audit.details) and attack not in str(event.features)


def test_generic_login_errors_and_benign_account_access(system):
    c,factory,*_=system;password=secrets.token_urlsafe(24);account={'email':'enumeration-pair@example.com','password':password}
    c.post('/api/v1/auth/register',json=account)
    known=c.post('/api/v1/auth/login',json={**account,'password':'incorrect-synthetic-value'})
    unknown=c.post('/api/v1/auth/login',json={**account,'email':'unknown-pair@example.com','password':'incorrect-synthetic-value'})
    assert known.status_code==unknown.status_code==401 and known.json()==unknown.json()
    h={'Authorization':'Bearer '+c.post('/api/v1/auth/login',json=account).json()['access_token']}
    assert c.get('/api/v1/auth/me',headers=h).status_code==200
    with factory() as db:assert not db.scalar(select(Incident))


def test_benign_browsing_no_bot_restriction_and_privileged_denial(system):
    c,factory,*_=system;customer,_=identity(system);admin,_=identity(system,True)
    for _ in range(8):assert c.get('/api/v1/products',headers=customer).status_code==200
    assert c.get('/api/v1/admin/users',headers=admin).status_code==200
    assert c.get('/api/v1/admin/users',headers=customer).status_code==403
    assert c.get('/api/v1/profile',headers=customer).status_code==200
    with factory() as db:
        assert not db.scalar(select(Restriction))
        assert not any('bot_behavior' in e.rules for e in db.scalars(select(SecurityEvent)))


def test_denial_policy_is_recorded_truthfully(system):
    c,factory,*_=system;headers,uid=identity(system)
    for _ in range(3):c.get('/api/v1/admin/users',headers=headers)
    with factory() as db:
        logs=db.scalars(select(AuditLog).where(AuditLog.actor_id==uid,AuditLog.event_type=='unauthorized')).all()
        assert logs and all(r.details['applied_action']=='request_denied' for r in logs)


def test_feature_schema_and_configured_incident_threshold(system):
    from app.ids import extract_features, FEATURES
    c,factory,settings,*_=system
    assert extract_features([(1,'auth_failure'),(2,'unauthorized'),(3,'rate_limit')])==dict(zip(FEATURES,[3,1,1,1]))
    settings.ids_incident_threshold=80
    c.get('/api/v1/products',params={'q':'UNION SELECT'})
    with factory() as db:
        assert db.scalar(select(SecurityEvent))
        assert not db.scalar(select(Incident))


def test_competing_login_never_extends_existing_deadline(system):
    c,*_=system;account={'email':'deadline-synthetic@example.com','password':secrets.token_urlsafe(24)}
    c.post('/api/v1/auth/register',json=account)
    h={'Authorization':'Bearer '+c.post('/api/v1/auth/login',json=account).json()['access_token']}
    assert c.post('/api/v1/auth/login',json=account).status_code==409
    deadline=c.get('/api/v1/auth/session',headers=h).json()['challenge_until']
    assert c.post('/api/v1/auth/login',json=account).status_code==409
    assert c.get('/api/v1/auth/session',headers=h).json()['challenge_until']==deadline
