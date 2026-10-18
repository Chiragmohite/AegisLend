from collections.abc import Iterator
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.config import Settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings):
    return create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=1800,
                         connect_args={"connect_timeout": 3, "read_timeout": 3,
                                       "write_timeout": 3, "init_command": "SET time_zone = '+00:00'"})


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session
