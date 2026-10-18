"""Read-only customer summaries. Authentication supplies the actor, never the LLM."""
from app import account_repository


def summarize_account(kind, user, session):
    if not user.is_active:
        raise ValueError('Active authenticated account required')
    if kind=='applications':
        rows=account_repository.recent_applications(session,user.id)
        return '\n'.join(f'Application {r.id}: {r.status.replace("_"," ")} — INR {r.amount}, {r.months} months.' for r in rows) or 'You have no saved applications yet.'
    if kind=='appointments':
        rows=account_repository.recent_appointments(session,user.id)
        return '\n'.join(f'Appointment {r.id}: {r.starts_at.isoformat()} UTC — {r.status}.' for r in rows) or 'You have no appointments yet. Use the Appointments page to view available slots.'
    raise ValueError('Unsupported read-only account tool')
