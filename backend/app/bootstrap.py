"""Interactive, synthetic-only local administrator bootstrap. No default credentials."""
import getpass
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth import Registration
from app.config import Settings
from app.db import make_engine
from app.models import User
from app.security import hash_password
from app.ids import audit
import uuid


def main():
    email=input('Synthetic administrator email (must end in @example.com): ').strip().lower()
    if not email.endswith('@example.com'):raise SystemExit('Only synthetic example.com identities are allowed by this demo helper')
    password=getpass.getpass('New password (12–128 characters): ')
    if password!=getpass.getpass('Repeat password: '):raise SystemExit('Passwords do not match')
    data=Registration(email=email,password=password)
    engine=make_engine(Settings())
    try:
        with Session(engine) as session:
            if session.scalar(select(User.id).where(User.email==data.email)):raise SystemExit('Account already exists. Use the explicit operator set-role command if appropriate.')
            user=User(email=str(data.email),password_hash=hash_password(password),role='administrator',is_active=True)
            session.add(user);session.flush()
            audit(session,user.id,'administrator_bootstrapped','user',user.id,str(uuid.uuid4()),{'operator':'local_interactive'})
            session.commit()
        print('Synthetic administrator created. Credentials were not printed.')
    finally:engine.dispose()


if __name__=='__main__':main()
