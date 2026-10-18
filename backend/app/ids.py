"""Synthetic telemetry model, transparent scoring and observable best-effort persistence."""
from collections import defaultdict, deque
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
from pathlib import Path
import secrets
import threading
import time
import uuid
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sqlalchemy.exc import SQLAlchemyError
from app.domain_models import SecurityEvent, RiskAssessment, AuditLog

FEATURES = ['requests', 'auth_failures', 'denials', 'rate_violations']
logger = logging.getLogger('aegislend.security')


class AnomalyModel:
    def __init__(self, path: Path, threshold: float = 0.0):
        self.path, self.threshold, self.model, self.metadata = Path(path), threshold, None, None
        self.lock = threading.RLock()
        self.status = 'untrained'
        if self.path.exists():
            try: self.load()
            except Exception: self.status = 'load_failed'

    def train(self):
        with self.lock:
            rng = np.random.default_rng(42)
            frame = pd.DataFrame({'requests': rng.poisson(12,512)+1, 'auth_failures': rng.binomial(2,.10,512),
                                  'denials': rng.binomial(2,.08,512), 'rate_violations': rng.binomial(1,.02,512)})
            model = IsolationForest(n_estimators=100, contamination=.03, random_state=42, n_jobs=1)
            model.fit(np.log1p(frame[FEATURES]))
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            joblib.dump(model,temporary)
            temporary.replace(self.path)
            metadata = {'version': 'synthetic-iforest-v1', 'features': FEATURES, 'samples': len(frame),
                'trained_at': datetime.now(timezone.utc).isoformat(), 'synthetic': True,
                'sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(), 'preprocessing': 'log1p', 'seed':42, 'sklearn_version':sklearn.__version__}
            self.path.with_suffix('.json').write_text(json.dumps(metadata,indent=2))
            self.model, self.metadata, self.status = model, metadata, 'ready'
            return metadata

    def load(self):
        metadata = json.loads(self.path.with_suffix('.json').read_text())
        if metadata.get('sklearn_version') != sklearn.__version__ or metadata['features'] != FEATURES or metadata['sha256'] != hashlib.sha256(self.path.read_bytes()).hexdigest():
            raise ValueError('Model metadata mismatch')
        # Trusted local artifacts only; uploaded documents can never reach this path.
        self.model = joblib.load(self.path)
        self.metadata, self.status = metadata, 'ready'

    def predict(self, features: dict):
        with self.lock:
            if self.model is None: return None
            frame = pd.DataFrame([{k: max(0,min(100000,float(features[k]))) for k in FEATURES}])
            score = float(self.model.decision_function(np.log1p(frame[FEATURES]))[0])
            return {'anomaly_score': round(score,6), 'anomaly_class': -1 if score < self.threshold else 1,
                    'model_version': self.metadata['version']}


def extract_features(window):
    """Stable numeric schema from a sanitized, already time-bounded event window."""
    categories=[category for _,category in window]
    return {'requests':len(categories),
            'auth_failures':sum(c in ('auth_failure','unknown_account') for c in categories),
            'denials':sum(c in ('unauthorized','resource_access_denied','privilege_escalation') for c in categories),
            'rate_violations':sum(c=='rate_limit' for c in categories)}


def risk(category, features, model=None, failed_threshold=5, burst_threshold=60):
    rules=[]; score=0
    weights={'unknown_account':15,'auth_failure':10,'unauthorized':25,'resource_access_denied':45,
             'session_conflict':65,'session_expired_challenge':65,'parameter_tampering':30,'privilege_escalation':65,'suspicious_request':65,'rate_limit':40,'demo_probe':35}
    if category in weights: rules.append(category);score=weights[category]
    if features['auth_failures']>=failed_threshold: rules.append('repeated_failed_logins');score+=35
    if features['rate_violations']>=3: rules.append('repeated_rate_limits');score+=20
    if features['requests']>=burst_threshold: rules.append('request_burst');score+=25
    prediction=model.predict(features) if model else None
    if prediction and prediction['anomaly_class']==-1: rules.append('isolation_forest_anomaly');score+=25
    score=min(100,score)
    severity='critical' if score>=80 else 'high' if score>=60 else 'medium' if score>=30 else 'low'
    return {'score':score,'severity':severity,'rules':rules,
            'explanation': ' + '.join(rules) or 'No configured rule triggered; baseline telemetry.',
            **(prediction or {'anomaly_score':None,'anomaly_class':None,'model_version':None})}


def audit(session, actor, event, target_type, target_id, correlation, details=None):
    # Callers pass explicitly constructed non-secret metadata only.
    session.add(AuditLog(actor_id=actor,event_type=event,target_type=target_type,target_id=target_id,
                         correlation_id=correlation,details=details or {}))


class Telemetry:
    def __init__(self, settings):
        self.settings=settings
        self.model=AnomalyModel(settings.ids_model_path,settings.ids_anomaly_threshold)
        self.windows=defaultdict(deque);self.account_windows=defaultdict(deque);self.lock=threading.RLock()
        self.persisted=0;self.failures=0;self.degraded=False;self.retry_at=0
        self.key=secrets.token_bytes(32)

    def client_key(self,request):
        host=request.client.host if request.client else 'local'
        return hmac.new(self.key,host.encode(),hashlib.sha256).hexdigest()

    def record(self, request, status, factory):
        category=getattr(request.state,'security_category',None)
        if category is None:
            category='unauthorized' if status in (401,403) else 'rate_limit' if status==429 else 'request'
        now=time.monotonic(); key=self.client_key(request)
        with self.lock:
            # Bound local memory for a demo; multi-worker correlation requires shared infrastructure.
            if len(self.windows)>10000:self.windows.clear();self.account_windows.clear()
            window=self.windows[key]
            while window and window[0][0]<now-60:window.popleft()
            window.append((now,category))
            accounts=self.account_windows[key]
            while accounts and accounts[0][0]<now-60:accounts.popleft()
            account=getattr(request.state,'login_account_key',None)
            if account and category in ('auth_failure','unknown_account'):accounts.append((now,account))
            distinct_accounts=len({a for _,a in accounts})
            features=extract_features(window)
        result=risk(category,features,self.model,self.settings.ids_failed_threshold,self.settings.ids_burst_threshold)
        extra=[]
        if distinct_accounts>=self.settings.ids_stuffing_threshold and features['auth_failures']>=self.settings.ids_failed_threshold:extra.append('credential_stuffing')
        if category=='unknown_account' and features['auth_failures']>=self.settings.ids_failed_threshold:extra.append('account_enumeration')
        if features['requests']>=self.settings.ids_burst_threshold and features['denials']>=3:extra.append('suspicious_data_access')
        if features['requests']>=self.settings.ids_burst_threshold and features['rate_violations']>=3:extra.extend(['automated_flooding','bot_behavior'])
        if extra:
            result['rules']+=extra;result['score']=min(100,result['score']+20)
            result['severity']='critical' if result['score']>=80 else 'high' if result['score']>=60 else 'medium'
            result['explanation']=' + '.join(result['rules'])
        if category=='request' and not result['rules']:return
        if now<self.retry_at:return
        try:
            with factory() as session:
                event=SecurityEvent(actor_id=getattr(request.state,'actor_id',None),category=category,
                    severity=result['severity'],correlation_id=request.state.correlation_id,features=features,rules=list(dict.fromkeys(result['rules']+getattr(request.state,'signature_matches',[]))))
                session.add(event);session.flush()
                session.add(RiskAssessment(event_id=event.id,**{k:v for k,v in result.items() if k!='rules'}))
                if result['score']>=self.settings.ids_incident_threshold:
                    from app.enhancement_models import Incident
                    from app.security_policy import decision, VERSION
                    session.add(Incident(event_id=event.id,actor_id=event.actor_id,recommended_action=decision(category,result['score']),policy_version=VERSION,applied_action=getattr(request.state,'applied_action',None) or ('request_denied' if status>=400 else 'log')))
                audit(session,event.actor_id,category,'security_event',event.id,event.correlation_id,{'http_status':status,'applied_action':getattr(request.state,'applied_action',None) or ('request_denied' if status>=400 else 'log')})
                session.commit()
            self.persisted+=1;self.degraded=False
        except Exception:
            self.failures+=1;self.degraded=True;self.retry_at=now+10
            logger.warning('telemetry_write_failed correlation=%s',request.state.correlation_id)


class RateLimiter:
    def __init__(self,settings):
        self.settings=settings;self.windows=defaultdict(deque);self.lock=threading.Lock()
        self.mode='local';self.redis=None;self.degraded=False
        if settings.redis_enabled:
            try:
                from redis import Redis
                self.redis=Redis.from_url(settings.redis_url,socket_connect_timeout=.3,socket_timeout=.3)
                self.redis.ping();self.mode='redis'
            except Exception:self.redis=None;self.degraded=True

    def allow(self,key,limit=None):
        limit=limit or self.settings.auth_rate_limit
        if self.redis is not None:
            try:
                count=self.redis.eval("local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",1,'aegislend:auth:'+key)
                return count<=limit
            except Exception:
                self.degraded=True
                # In Redis mode outages fail closed; no reset-to-empty bypass.
                return False
        with self.lock:
            now=time.monotonic()
            if len(self.windows)>10000:return False
            window=self.windows[key]
            while window and window[0]<now-60:window.popleft()
            if len(window)>=limit:return False
            window.append(now);return True
