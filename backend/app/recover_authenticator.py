"""Trusted host operator recovery only. Verify identity offline before running."""
import argparse,uuid
from sqlalchemy import select,update
from sqlalchemy.orm import Session
from app.config import Settings
from app.db import make_engine
from app.models import User
from app.enhancement_models import Authenticator,AuthSession
from app.domain_models import utcnow
from app.ids import audit

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--email',required=True);p.add_argument('--confirm-identity-verified',action='store_true',required=True);args=p.parse_args()
    engine=make_engine(Settings())
    try:
        with Session(engine) as db,db.begin():
            user=db.scalar(select(User).where(User.email==args.email.strip().lower()).with_for_update())
            if not user:raise SystemExit('No matching account; nothing changed.')
            factor=db.get(Authenticator,user.id)
            if factor:db.delete(factor)
            db.execute(update(AuthSession).where(AuthSession.user_id==user.id,AuthSession.revoked_at.is_(None)).values(revoked_at=utcnow(),active_user=None))
            audit(db,None,'authenticator_recovery','user',user.id,str(uuid.uuid4()),{'operator':'local_cli','sessions_revoked':True})
        print('Authenticator reset and sessions revoked. Enroll a new authenticator after signing in.')
    finally:engine.dispose()
if __name__=='__main__':main()
