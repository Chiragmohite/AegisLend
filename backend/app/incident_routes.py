"""Authorized, versioned incident actions with transactional audit records."""
from datetime import timedelta
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from app.auth import administrator, SessionDep
from app.models import User
from app.domain_models import SecurityEvent, RiskAssessment, utcnow
from app.enhancement_models import Incident, IncidentAction, AuthSession, Restriction
from app.ids import audit
from app.security_policy import allowed_actions, VERSION
router=APIRouter(prefix='/api/v1/admin/security',tags=['Security incidents'])
Admin=Annotated[User,Depends(administrator)]
class Action(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action:Literal['triage','investigate','recommend','resolve','false_positive','note','revoke_session','require_reauthentication','restrict','release']
    note:str=Field(min_length=5,max_length=500)
    version:int=Field(ge=1)
    session_id:UUID|None=None
    minutes:int=Field(default=15,ge=1,le=60)
def view(row):
    return {'id':row.id,'event_id':row.event_id,'actor_id':row.actor_id,'state':row.state,'recommended_action':row.recommended_action,'applied_action':row.applied_action,'policy_version':row.policy_version,'version':row.version,'allowed_actions':allowed_actions(row.state),'created_at':row.created_at.isoformat()+'Z'}
@router.get('/incidents')
def incidents(admin:Admin,session:SessionDep,state:str|None=None,limit:int=50,offset:int=0):
    if not 1<=limit<=100 or offset<0:raise HTTPException(422,'Invalid pagination')
    q=select(Incident)
    if state:q=q.where(Incident.state==state)
    return [view(row) for row in session.scalars(q.order_by(Incident.created_at.desc()).limit(limit).offset(offset))]
@router.get('/incidents/{incident_id}')
def detail(incident_id:UUID,admin:Admin,session:SessionDep):
    row=session.get(Incident,str(incident_id))
    if not row:raise HTTPException(404,'Incident not found')
    event=session.get(SecurityEvent,row.event_id)
    risk=session.scalar(select(RiskAssessment).where(RiskAssessment.event_id==row.event_id))
    actions=session.scalars(select(IncidentAction).where(IncidentAction.incident_id==row.id).order_by(IncidentAction.created_at,IncidentAction.id)).all()
    sessions=session.scalars(select(AuthSession).where(AuthSession.user_id==row.actor_id,AuthSession.revoked_at.is_(None),AuthSession.expires_at>utcnow())).all() if row.actor_id else []
    restrictions=session.scalars(select(Restriction).where(Restriction.user_id==row.actor_id,Restriction.released_at.is_(None),Restriction.expires_at>utcnow())).all() if row.actor_id else []
    return {**view(row),'evidence':{'category':event.category,'rules':event.rules,'features':event.features,'correlation_id':event.correlation_id},'risk':{'score':risk.score,'severity':risk.severity,'anomaly_score':risk.anomaly_score,'model_version':risk.model_version} if risk else None,'timeline':[{'action':a.action,'note':a.note,'actor_id':a.actor_id,'created_at':a.created_at.isoformat()+'Z'} for a in actions],'sessions':[{'id':s.id,'created_at':s.created_at.isoformat()+'Z','challenge_until':s.challenge_until.isoformat()+'Z' if s.challenge_until else None} for s in sessions],'restrictions':[{'id':r.id,'expires_at':r.expires_at.isoformat()+'Z'} for r in restrictions]}
@router.post('/incidents/{incident_id}/actions')
def act(incident_id:UUID,data:Action,request:Request,admin:Admin,session:SessionDep):
    row=session.get(Incident,str(incident_id))
    if not row:raise HTTPException(404,'Incident not found')
    if data.action not in allowed_actions(row.state):raise HTTPException(409,'Action not permitted from the current incident state')
    targets={'require_reauthentication':'action_applied','triage':'triaged','investigate':'under_investigation','recommend':'action_recommended','resolve':'resolved','false_positive':'false_positive','restrict':'action_applied','revoke_session':'action_applied'}
    if data.action=='triage' and row.state!='detected':raise HTTPException(409,'Only detected incidents may be triaged')
    if data.action in ('restrict','release','revoke_session','require_reauthentication') and (not row.actor_id or row.actor_id==admin.id):raise HTTPException(409,'Action requires another identified account')
    changed=session.execute(update(Incident).where(Incident.id==row.id,Incident.version==data.version).values(state=targets.get(data.action,row.state),version=Incident.version+1,updated_at=utcnow(),policy_version=VERSION))
    if changed.rowcount!=1:session.rollback();raise HTTPException(409,'Incident changed; reload it')
    if data.action in ('revoke_session','require_reauthentication'):
        target=session.get(AuthSession,str(data.session_id)) if data.session_id else None
        if not target or target.user_id!=row.actor_id or target.revoked_at or target.expires_at<=utcnow():session.rollback();raise HTTPException(422,'Select a session belonging to the incident account')
        if data.action=='revoke_session':
            changed=session.execute(update(AuthSession).where(AuthSession.id==target.id,AuthSession.revoked_at.is_(None)).values(revoked_at=utcnow(),active_user=None))
        else:
            changed=session.execute(update(AuthSession).where(AuthSession.id==target.id,AuthSession.revoked_at.is_(None),AuthSession.expires_at>utcnow(),AuthSession.challenge_until.is_(None)).values(challenge_until=utcnow()+timedelta(seconds=120),challenge_attempts=0))
        if changed.rowcount!=1:session.rollback();raise HTTPException(409,'Session changed or already has a challenge; refresh')
        row.applied_action=data.action
    elif data.action=='restrict':
        if session.scalar(select(Restriction.id).where(Restriction.incident_id==row.id,Restriction.released_at.is_(None),Restriction.expires_at>utcnow())):
            session.rollback();raise HTTPException(409,'An active restriction already exists for this incident')
        session.add(Restriction(user_id=row.actor_id,incident_id=row.id,expires_at=utcnow()+timedelta(minutes=data.minutes)));row.applied_action='temporary_restriction'
    elif data.action in ('release','false_positive'):
        session.execute(update(Restriction).where(Restriction.incident_id==row.id,Restriction.released_at.is_(None)).values(released_at=utcnow()));row.applied_action='release'
    session.add(IncidentAction(incident_id=row.id,actor_id=admin.id,action=data.action,note=data.note))
    audit(session,admin.id,'incident_'+data.action,'incident',row.id,request.state.correlation_id,{'action':data.action,'policy_version':VERSION})
    session.commit();session.refresh(row);return view(row)
