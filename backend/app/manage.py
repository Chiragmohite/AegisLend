"""Local operator-only role assignment. Never exposed through HTTP or an LLM."""
import argparse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import TypeAdapter, EmailStr
from app.config import Settings
from app.db import make_engine
from app.models import User
from app.ids import audit
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['set-role'])
    parser.add_argument('--email', required=True)
    parser.add_argument('--role', choices=['customer', 'administrator'], required=True)
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    engine = make_engine(Settings())
    try:
        with Session(engine) as session:
            with session.begin():
                user = session.scalar(select(User).where(User.email == email).with_for_update())
                if user is None or not user.is_active:
                    raise SystemExit('No active registered account matched; no change made.')
                user.role = args.role
                audit(session,None,"role_changed","user",user.id,str(uuid.uuid4()),{"role":args.role,"operator":"local_cli"})
        print('Role updated. Future requests use the current database role.')
    except SQLAlchemyError:
        raise SystemExit("Database operation failed; verify configuration and migrations. No success is reported.") from None
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
