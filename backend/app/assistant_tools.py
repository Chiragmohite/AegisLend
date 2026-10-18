"""Validated read-only tool → account service → scoped repository → database."""
from app.account_service import summarize_account


def customer_answer(question,user,session):
    q=question.lower().strip()
    if any(x in q for x in ('my application','my loan status','application progress')):
        kind='applications'
    elif any(x in q for x in ('my appointment','my booking')):
        kind='appointments'
    else:
        return None
    text=summarize_account(kind,user,session)
    return {'answer':text+'\nOnly your own records are shown. This does not approve a loan.','sources':[],'mode':'authorized_account_lookup','retrieval':'authenticated_database','warning':None,'stages':['authenticate','read_own_records','format']}
