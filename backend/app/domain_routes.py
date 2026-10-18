from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File
from sqlalchemy import select, update, func, delete
from sqlalchemy.exc import IntegrityError
from app.auth import UserDep, SessionDep, administrator, UserView
from app.models import User
from app.domain_models import *
from app.schemas import *
from app.lending import assess
from app.ids import audit
from app import rag
from app.enhancement_models import AppointmentSeat,BookingKey,WaitEntry,Attendance
from app.appointment_service import reserve

router=APIRouter(prefix='/api/v1')
Admin=Annotated[User,Depends(administrator)]
Limit=Annotated[int,Query(ge=1,le=100)]
Offset=Annotated[int,Query(ge=0)]


def correlation(request):return getattr(request.state,'correlation_id',str(uuid.uuid4()))

def product_or_404(session,product_id):
    p=session.get(Product,str(product_id))
    if p is None or not p.active:raise HTTPException(404,'Active product not found')
    return p


def owned(session,model,identifier,user,request):
    item=session.get(model,str(identifier))
    if item is None:raise HTTPException(404,'Resource not found')
    if item.user_id!=user.id and user.role!='administrator':
        request.state.security_category='resource_access_denied'
        raise HTTPException(404,'Resource not found')
    return item


@router.get('/profile',response_model=ProfileView)
def profile(user:UserDep,session:SessionDep):
    p=session.get(Profile,user.id)
    return p or ProfileView(user_id=user.id,display_name='Demo customer',employment='salaried')


@router.put('/profile',response_model=ProfileView)
def save_profile(data:ProfileInput,request:Request,user:UserDep,session:SessionDep):
    p=session.get(Profile,user.id)
    if p is None:p=Profile(user_id=user.id);session.add(p)
    p.display_name=data.display_name;p.employment=data.employment
    audit(session,user.id,'profile_updated','profile',user.id,correlation(request))
    try:session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Profile changed concurrently; retry')
    return p


@router.get('/products',response_model=list[ProductView])
def products(session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.name).limit(limit).offset(offset)).all()


@router.get('/admin/products',response_model=list[ProductView])
def admin_products(admin:Admin,session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(Product).order_by(Product.name).limit(limit).offset(offset)).all()


@router.post('/admin/products',response_model=ProductView,status_code=201)
def create_product(data:ProductInput,request:Request,admin:Admin,session:SessionDep):
    p=Product(**data.model_dump());session.add(p)
    try:
        session.flush();audit(session,admin.id,'product_created','product',p.id,correlation(request));session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Product name already exists')
    return p


@router.put('/admin/products/{product_id}',response_model=ProductView)
def edit_product(product_id:UUID,data:ProductInput,request:Request,admin:Admin,session:SessionDep):
    p=session.scalar(select(Product).where(Product.id==str(product_id)).with_for_update())
    if not p:raise HTTPException(404,'Product not found')
    for key,value in data.model_dump().items():setattr(p,key,value)
    audit(session,admin.id,'product_updated','product',p.id,correlation(request))
    try:session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Product name already exists')
    return p


@router.post('/eligibility',response_model=AssessmentView,status_code=201)
def eligibility(data:EligibilityInput,request:Request,user:UserDep,session:SessionDep):
    p=product_or_404(session,data.product_id)
    assessment=Assessment(user_id=user.id,product_id=p.id,inputs=data.model_dump(mode='json'),result=assess(data,p))
    session.add(assessment);session.flush()
    audit(session,user.id,'eligibility_calculated','assessment',assessment.id,correlation(request));session.commit()
    return assessment


@router.get('/eligibility/{assessment_id}',response_model=AssessmentView)
def get_eligibility(assessment_id:UUID,request:Request,user:UserDep,session:SessionDep):
    return owned(session,Assessment,assessment_id,user,request)


@router.post('/applications',response_model=ApplicationView,status_code=201)
def create_application(data:ApplicationInput,request:Request,user:UserDep,session:SessionDep):
    fingerprint=hashlib.sha256(data.model_dump_json().encode()).hexdigest()
    existing=session.scalar(select(Application).where(Application.user_id==user.id,Application.request_key==str(data.request_key)))
    if existing:
        if existing.fingerprint!=fingerprint:raise HTTPException(409,'Request key already used for different inputs')
        return existing
    p=product_or_404(session,data.product_id)
    assessment=Assessment(user_id=user.id,product_id=p.id,inputs=data.model_dump(mode='json'),result=assess(data,p))
    session.add(assessment);session.flush()
    a=Application(user_id=user.id,product_id=p.id,assessment_id=assessment.id,request_key=str(data.request_key),fingerprint=fingerprint,amount=data.amount,months=data.months)
    session.add(a)
    try:
        session.flush();session.add(ApplicationHistory(application_id=a.id,actor_id=user.id,status='draft',note='Draft created'))
        audit(session,user.id,'application_created','application',a.id,correlation(request));session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Duplicate request; refresh application history')
    session.refresh(a);return a


@router.put('/applications/{application_id}',response_model=ApplicationView)
def edit_draft(application_id:UUID,data:DraftUpdate,request:Request,user:UserDep,session:SessionDep):
    """Keep previous assessments immutable; edits create a new deterministic snapshot."""
    a=owned(session,Application,application_id,user,request)
    if a.user_id!=user.id:raise HTTPException(403,'Only the customer can edit their own draft')
    if a.status!='draft':raise HTTPException(409,'Only saved drafts can be edited')
    product=product_or_404(session,data.product_id)
    inputs=data.model_dump(mode='json',exclude={'version'})
    assessment=Assessment(user_id=user.id,product_id=product.id,inputs=inputs,result=assess(data,product))
    session.add(assessment);session.flush()
    changed=session.execute(update(Application).where(Application.id==a.id,Application.status=='draft',Application.version==data.version).values(
        product_id=product.id,assessment_id=assessment.id,amount=data.amount,months=data.months,version=Application.version+1,updated_at=utcnow()))
    if changed.rowcount!=1:session.rollback();raise HTTPException(409,'Draft changed; refresh before editing again')
    session.add(ApplicationHistory(application_id=a.id,actor_id=user.id,status='draft',note='Draft revised; eligibility recalculated'))
    audit(session,user.id,'application_draft_updated','application',a.id,correlation(request))
    session.commit();session.refresh(a);return a


@router.get('/dashboard',response_model=DashboardView)
def dashboard(user:UserDep,session:SessionDep):
    counts=dict(session.execute(select(Application.status,func.count()).where(Application.user_id==user.id).group_by(Application.status)).all())
    recent=session.scalars(select(Application).where(Application.user_id==user.id).order_by(Application.created_at.desc()).limit(5)).all()
    upcoming=session.scalars(select(Appointment).where(Appointment.user_id==user.id,Appointment.status=='booked',Appointment.starts_at>utcnow()).order_by(Appointment.starts_at).limit(5)).all()
    return {'application_counts':counts,'recent_applications':recent,'upcoming_appointments':upcoming}


@router.get('/applications',response_model=list[ApplicationView])
def applications(user:UserDep,session:SessionDep,status:Literal['draft','submitted','under_review','approved','rejected','cancelled']|None=None,limit:Limit=50,offset:Offset=0):
    query=select(Application).where(Application.user_id==user.id)
    if status:query=query.where(Application.status==status)
    return session.scalars(query.order_by(Application.created_at.desc()).limit(limit).offset(offset)).all()


@router.get('/applications/{application_id}',response_model=ApplicationView)
def get_application(application_id:UUID,request:Request,user:UserDep,session:SessionDep):
    return owned(session,Application,application_id,user,request)


@router.post('/applications/{application_id}/transition',response_model=ApplicationView)
def transition(application_id:UUID,data:Transition,request:Request,user:UserDep,session:SessionDep):
    a=owned(session,Application,application_id,user,request)
    customer={'draft':{'submitted','cancelled'},'submitted':{'cancelled'}}
    reviewer={'submitted':{'under_review'},'under_review':{'approved','rejected'}}
    customer_action=data.status in ('submitted','cancelled') and a.user_id==user.id
    allowed=customer if customer_action else reviewer if user.role=='administrator' else {}
    if user.role=='administrator' and a.user_id==user.id and data.status in ('under_review','approved','rejected'):
        raise HTTPException(403,'A different administrator must review your application')
    if data.status not in allowed.get(a.status,set()):raise HTTPException(409,'Transition not permitted from current state')
    if user.role=='administrator' and not customer_action and not data.note.strip():raise HTTPException(422,'A review note is required')
    if data.status=='submitted':product_or_404(session,a.product_id)
    changed=session.execute(update(Application).where(Application.id==a.id,Application.version==data.version,Application.status==a.status)
        .values(status=data.status,version=data.version+1,updated_at=utcnow()))
    if changed.rowcount!=1:session.rollback();raise HTTPException(409,'Application changed; refresh and retry')
    session.add(ApplicationHistory(application_id=a.id,actor_id=user.id,status=data.status,note=data.note))
    audit(session,user.id,'application_'+data.status,'application',a.id,correlation(request),{'status':data.status})
    session.commit();session.refresh(a);return a


@router.get('/admin/applications',response_model=list[ApplicationView])
def review_applications(admin:Admin,session:SessionDep,status:str|None=None,limit:Limit=50,offset:Offset=0):
    q=select(Application)
    if status:q=q.where(Application.status==status)
    return session.scalars(q.order_by(Application.created_at.desc()).limit(limit).offset(offset)).all()


def valid_slot(value):
    if value.tzinfo is None:raise HTTPException(422,'Use an ISO timestamp with timezone')
    value=value.astimezone(timezone.utc).replace(tzinfo=None)
    now=utcnow()
    if not now<value<=now+timedelta(days=30) or value.weekday()>4 or value.hour not in range(9,17) or value.minute or value.second or value.microsecond:
        raise HTTPException(422,'Choose a future weekday hourly slot, 09:00–16:00 UTC, within 30 days')
    return value


@router.get('/appointments/slots',response_model=list[str])
def slots(request:Request,user:UserDep,session:SessionDep):
    now=utcnow();occupied=set(session.scalars(select(AppointmentSeat.starts_at).group_by(AppointmentSeat.starts_at).having(func.count()>=request.app.state.settings.appointment_capacity)).all())
    result=[]
    for day in range(30):
        d=now.replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=day)
        if d.weekday()>4:continue
        for hour in range(9,17):
            value=d.replace(hour=hour)
            if value>now and value not in occupied:result.append(value.isoformat()+'Z')
    return result


@router.post('/appointments',response_model=AppointmentView,status_code=201)
def book(data:Booking,request:Request,user:UserDep,session:SessionDep):
    value=valid_slot(data.starts_at)
    fingerprint=hashlib.sha256((value.isoformat()+data.purpose).encode()).hexdigest()
    if data.request_key:
        previous=session.get(BookingKey,(user.id,str(data.request_key)))
        if previous:
            if previous.fingerprint!=fingerprint:raise HTTPException(409,'Booking key already used for different details')
            return session.get(Appointment,previous.appointment_id)
    a=Appointment(user_id=user.id,starts_at=value,active_slot=None,purpose=data.purpose)
    try:
        session.add(a);session.flush();reserve(session,a,request.app.state.settings.appointment_capacity)
        if data.request_key:session.add(BookingKey(user_id=user.id,request_key=str(data.request_key),appointment_id=a.id,fingerprint=fingerprint))
        session.execute(delete(WaitEntry).where(WaitEntry.user_id==user.id,WaitEntry.starts_at==value))
        audit(session,user.id,'appointment_booked','appointment',a.id,correlation(request));session.commit()
    except (IntegrityError,HTTPException) as exc:
        session.rollback()
        if data.request_key:
            previous=session.get(BookingKey,(user.id,str(data.request_key)))
            if previous and previous.fingerprint==fingerprint:return session.get(Appointment,previous.appointment_id)
        if isinstance(exc,HTTPException):raise
        raise HTTPException(409,'Booking conflicted; refresh and retry') from None
    return a


@router.get('/appointments',response_model=list[AppointmentView])
def appointments(user:UserDep,session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(Appointment).where(Appointment.user_id==user.id).order_by(Appointment.starts_at.desc()).limit(limit).offset(offset)).all()


@router.post('/appointments/{appointment_id}/cancel',response_model=AppointmentView)
def cancel(appointment_id:UUID,request:Request,user:UserDep,session:SessionDep):
    a=owned(session,Appointment,appointment_id,user,request)
    changed=session.execute(update(Appointment).where(Appointment.id==a.id,Appointment.status=='booked',Appointment.starts_at>utcnow()).values(status='cancelled',active_slot=None))
    if changed.rowcount!=1:session.rollback();raise HTTPException(409,'Only future booked appointments can be cancelled')
    session.execute(delete(AppointmentSeat).where(AppointmentSeat.appointment_id==a.id))
    audit(session,user.id,'appointment_cancelled','appointment',a.id,correlation(request));session.commit();session.refresh(a);return a


@router.get('/admin/appointments',response_model=list[AppointmentView])
def all_appointments(admin:Admin,session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(Appointment).order_by(Appointment.starts_at.desc()).limit(limit).offset(offset)).all()


@router.get('/activity',response_model=list[AuditView])
def activity(user:UserDep,session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(AuditLog).where(AuditLog.actor_id==user.id).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)).all()


@router.get('/admin/users',response_model=list[UserView])
def users(admin:Admin,session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)).all()


@router.get('/admin/documents',response_model=list[DocumentView])
def documents(admin:Admin,session:SessionDep,limit:Limit=50,offset:Offset=0):
    return session.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).limit(limit).offset(offset)).all()


@router.post('/admin/documents',response_model=DocumentView,status_code=201)
def upload(request:Request,admin:Admin,session:SessionDep,file:UploadFile=File(...)):
    data=file.file.read(rag.MAX_BYTES+1)
    try:content,chunks,digest=rag.extract(file.filename or '',data)
    except Exception:raise HTTPException(422,'Invalid document: use readable UTF-8 TXT/MD or unencrypted text PDF, maximum 2 MiB and 100 pages') from None
    if session.scalar(select(KnowledgeDocument.id).where(KnowledgeDocument.content_hash==digest)):
        raise HTTPException(409,'Document content already indexed')
    document=KnowledgeDocument(title=(file.filename or 'Document').replace('\\','/').split('/')[-1][:160],content=content,content_hash=digest,chunks=chunks,uploaded_by=admin.id)
    session.add(document)
    try:
        session.flush();rag.index_document(document,request.app.state.settings)
        audit(session,admin.id,'document_uploaded','document',document.id,correlation(request));session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Document content already indexed')
    return document


@router.post('/admin/documents/{document_id}/reindex',response_model=DocumentView)
def reindex(document_id:UUID,request:Request,admin:Admin,session:SessionDep):
    document=session.get(KnowledgeDocument,str(document_id))
    if not document:raise HTTPException(404,'Document not found')
    rag.index_document(document,request.app.state.settings)
    audit(session,admin.id,'document_reindexed','document',document.id,correlation(request));session.commit();return document


@router.delete('/admin/documents/{document_id}')
def remove_document(document_id:UUID,request:Request,admin:Admin,session:SessionDep):
    document=session.get(KnowledgeDocument,str(document_id))
    if not document:raise HTTPException(404,'Document not found')
    warning=None
    if request.app.state.settings.chroma_enabled:
        try:rag.chroma_collection(request.app.state.settings).delete(where={'document_id':document.id})
        except Exception:warning='Vector deletion pending; SQL removal prevents retrieval of stale chunks. Re-index service maintenance required.'
    audit(session,admin.id,'document_removed','document',document.id,correlation(request));session.delete(document);session.commit()
    return {'removed':True,'warning':warning}


@router.post('/assistant',response_model=Answer)
def assistant(data:Question,request:Request,user:UserDep,session:SessionDep):
    docs=session.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).limit(100)).all()
    from app.assistant_tools import customer_answer
    result=customer_answer(data.question,user,session) or rag.answer(data.question,docs,request.app.state.settings)
    audit(session,user.id,'assistant_queried','assistant',None,correlation(request),{'sources':len(result['sources']),'mode':result['mode']});session.commit()
    return result


@router.get('/admin/audit',response_model=list[AuditView])
def audit_list(admin:Admin,session:SessionDep,event_type:str|None=None,limit:Limit=50,offset:Offset=0):
    q=select(AuditLog)
    if event_type:q=q.where(AuditLog.event_type==event_type)
    return session.scalars(q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)).all()


@router.get('/admin/security/events',response_model=list[SecurityView])
def events(admin:Admin,session:SessionDep,severity:Literal['low','medium','high','critical']|None=None,category:str|None=None,since:datetime|None=None,until:datetime|None=None,limit:Limit=25,offset:Offset=0):
    q=select(SecurityEvent)
    if severity:q=q.where(SecurityEvent.severity==severity)
    if category:q=q.where(SecurityEvent.category==category)
    for value,name in [(since,'since'),(until,'until')]:
        if value is not None and value.tzinfo is None:raise HTTPException(422,f'{name} needs timezone')
    if since:q=q.where(SecurityEvent.created_at>=since.astimezone(timezone.utc).replace(tzinfo=None))
    if until:q=q.where(SecurityEvent.created_at<=until.astimezone(timezone.utc).replace(tzinfo=None))
    return session.scalars(q.order_by(SecurityEvent.created_at.desc()).limit(limit).offset(offset)).all()


@router.get('/admin/security/risks',response_model=list[RiskView])
def risks(admin:Admin,session:SessionDep,limit:Limit=25,offset:Offset=0):
    return session.scalars(select(RiskAssessment).order_by(RiskAssessment.created_at.desc()).limit(limit).offset(offset)).all()


@router.get('/admin/security/summary')
def security_summary(request:Request,admin:Admin,session:SessionDep):
    distribution=dict(session.execute(select(SecurityEvent.severity,func.count()).group_by(SecurityEvent.severity)).all())
    since=utcnow()-timedelta(days=7)
    trends=[{'date':str(d),'count':n} for d,n in session.execute(select(func.date(SecurityEvent.created_at),func.count()).where(SecurityEvent.category.in_(['auth_failure','unknown_account']),SecurityEvent.created_at>=since).group_by(func.date(SecurityEvent.created_at))).all()]
    from app.enhancement_models import Incident, Restriction, AuthSession
    now=utcnow()
    t=request.app.state.telemetry
    return {'active_restrictions':session.scalar(select(func.count()).select_from(Restriction).where(Restriction.released_at.is_(None),Restriction.expires_at>now)),
        'open_incidents':session.scalar(select(func.count()).select_from(Incident).where(Incident.state.notin_(['resolved','false_positive']))),
        'active_challenges':session.scalar(select(func.count()).select_from(AuthSession).where(AuthSession.revoked_at.is_(None),AuthSession.expires_at>now,AuthSession.challenge_until>now)),
        'total':sum(distribution.values()),'severity':distribution,'failed_login_trend':trends,
        'anomalies':session.scalar(select(func.count()).select_from(RiskAssessment).where(RiskAssessment.anomaly_class==-1)),
        'telemetry':{'degraded':t.degraded,'persisted_this_process':t.persisted,'failed_writes':t.failures},
        'model':{'status':t.model.status,'metadata':t.model.metadata},
        'rate_limiter':{'mode':request.app.state.limiter.mode,'degraded':request.app.state.limiter.degraded},
        'assistant':{'provider':request.app.state.settings.llm_provider,'chroma_configured':request.app.state.settings.chroma_enabled}}


@router.post('/admin/security/probe')
def probe(request:Request,admin:Admin):
    request.state.security_category='demo_probe'
    return {'generated':'controlled synthetic probe','correlation_id':correlation(request),'persistence':'Check response X-Telemetry-Status and Security Center'}


@router.post('/admin/security/train')
def train_model(request:Request,admin:Admin,session:SessionDep):
    try:metadata=request.app.state.telemetry.model.train()
    except Exception:raise HTTPException(503,"Synthetic model training failed; check local model storage") from None
    audit(session,admin.id,'ids_model_trained','model',None,correlation(request),{'version':metadata['version'],'synthetic':True});session.commit()
    return metadata


@router.post('/admin/security/events/{event_id}/review')
def review_event(event_id:UUID,data:Review,request:Request,admin:Admin,session:SessionDep):
    event=session.get(SecurityEvent,str(event_id))
    if not event:raise HTTPException(404,'Event not found')
    review=SecurityReview(event_id=event.id,actor_id=admin.id,action=data.action,note=data.note)
    session.add(review)
    try:
        audit(session,admin.id,'security_'+data.action,'security_event',event.id,correlation(request),{'action':data.action});session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Event already reviewed')
    return {'reviewed':True,'action':data.action,'policy':'Human acknowledgement/escalation only; no account blocking or privileged automated actions'}


@router.post('/appointments/{appointment_id}/reschedule',response_model=AppointmentView)
def reschedule(appointment_id:UUID,data:Booking,request:Request,user:UserDep,session:SessionDep):
    """Move a reservation atomically; a conflict rolls back and preserves the old slot."""
    a=owned(session,Appointment,appointment_id,user,request)
    target=valid_slot(data.starts_at)
    try:
        changed=session.execute(update(Appointment).where(Appointment.id==a.id,Appointment.status=='booked',Appointment.starts_at==a.starts_at,Appointment.starts_at>utcnow()).values(starts_at=target,active_slot=None,purpose=data.purpose))
        if changed.rowcount!=1:session.rollback();raise HTTPException(409,'Appointment changed or is no longer eligible for rescheduling')
        session.execute(delete(AppointmentSeat).where(AppointmentSeat.appointment_id==a.id))
        session.flush();session.refresh(a);reserve(session,a,request.app.state.settings.appointment_capacity)
        audit(session,user.id,'appointment_rescheduled','appointment',a.id,correlation(request));session.commit()
    except (IntegrityError,HTTPException):session.rollback();raise HTTPException(409,'Slot is already booked; original appointment preserved')
    session.refresh(a);return a


@router.post('/appointments/waitlist',status_code=201)
def join_waitlist(data:Booking,request:Request,user:UserDep,session:SessionDep):
    value=valid_slot(data.starts_at)
    row=WaitEntry(user_id=user.id,starts_at=value,purpose=data.purpose);session.add(row)
    try:
        session.flush();audit(session,user.id,'waitlist_joined','waitlist',row.id,correlation(request));session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Already on this slot waitlist')
    return {'id':row.id,'status':'waiting','policy':'Availability notifications are shown in-app; no automatic booking or priority guarantee.'}

@router.get('/appointments/waitlist')
def waitlist(request:Request,user:UserDep,session:SessionDep):
    rows=session.scalars(select(WaitEntry).where(WaitEntry.user_id==user.id).order_by(WaitEntry.created_at).limit(100)).all()
    counts=dict(session.execute(select(AppointmentSeat.starts_at,func.count()).group_by(AppointmentSeat.starts_at)).all())
    return [{'id':r.id,'starts_at':r.starts_at.isoformat()+'Z','purpose':r.purpose,'available':r.starts_at>utcnow() and counts.get(r.starts_at,0)<request.app.state.settings.appointment_capacity,'expired':r.starts_at<=utcnow()} for r in rows]

@router.delete('/appointments/waitlist/{entry_id}')
def leave_waitlist(entry_id:UUID,request:Request,user:UserDep,session:SessionDep):
    row=owned(session,WaitEntry,entry_id,user,request)
    audit(session,user.id,'waitlist_left','waitlist',row.id,correlation(request));session.delete(row);session.commit();return {'removed':True}

class AttendanceInput(Input):
    outcome:Literal['completed','missed']
    note:str=Field(min_length=5,max_length=500)

@router.post('/admin/appointments/{appointment_id}/attendance')
def attendance(appointment_id:UUID,data:AttendanceInput,request:Request,admin:Admin,session:SessionDep):
    row=session.get(Appointment,str(appointment_id))
    if not row:raise HTTPException(404,'Appointment not found')
    if row.status!='booked' or row.starts_at>utcnow():raise HTTPException(409,'Only past booked appointments can have attendance recorded')
    session.add(Attendance(appointment_id=row.id,outcome=data.outcome,note=data.note,actor_id=admin.id))
    try:
        audit(session,admin.id,'appointment_'+data.outcome,'appointment',row.id,correlation(request));session.commit()
    except IntegrityError:session.rollback();raise HTTPException(409,'Attendance already recorded')
    return {'outcome':data.outcome}

@router.get('/appointments/{appointment_id}/attendance')
def view_attendance(appointment_id:UUID,request:Request,user:UserDep,session:SessionDep):
    row=owned(session,Appointment,appointment_id,user,request);record=session.get(Attendance,row.id)
    return {'outcome':record.outcome if record else 'not_recorded'}
