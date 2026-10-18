"""Deterministic policies. Anomaly scores alone never restrict an account."""
import re
from urllib.parse import unquote_plus
VERSION='policy-v3'
PATTERNS={
 'sql_injection':r'\bunion\s+(?:all\s+)?select\b|\bor\s+1\s*=\s*1',
 'xss':r'<\s*script\b|javascript\s*:|onerror\s*=',
 'path_traversal':r'\.\.[/\\]',
 'command_injection':r';\s*(?:cat|curl|wget|bash|powershell)\b|\$\(',
}
def signatures(path_query):
    value=unquote_plus(unquote_plus(path_query)).lower()[:8192]
    return [name for name,pattern in PATTERNS.items() if re.search(pattern,value)]

def decision(category,score):
    if category in ('session_conflict','session_expired_challenge'):
        return 'require_reauthentication'
    if category in ('privilege_escalation','resource_access_denied'):
        return 'investigate'
    return 'investigate' if score>=60 else 'monitor'

# Security enforcement is based on verified database state, never an ML verdict.
def mutation_policy(challenge_pending: bool, restricted: bool) -> str:
    if challenge_pending:
        return 'require_reauthentication'
    if restricted:
        return 'deny_sensitive_operation'
    return 'allow'

OPEN_STATES={'detected','triaged','action_recommended','action_applied','under_investigation'}
ACTION_STATES={
    'triage':{'detected'},
    'investigate':{'detected','triaged','action_recommended','action_applied'},
    'recommend':{'detected','triaged','under_investigation'},
    'restrict':OPEN_STATES,
    'revoke_session':OPEN_STATES,
    'require_reauthentication':OPEN_STATES,
    'resolve':OPEN_STATES,
    'false_positive':OPEN_STATES,
    'note':OPEN_STATES|{'resolved','false_positive'},
    'release':OPEN_STATES|{'resolved','false_positive'},
}

def allowed_actions(state: str) -> list[str]:
    return [action for action,states in ACTION_STATES.items() if state in states]
