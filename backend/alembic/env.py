from alembic import context
from app.config import Settings
from app.db import Base, make_engine
from app import models  # Register model metadata for autogeneration.

settings = Settings()
if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=Base.metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
elif context.config.attributes.get('connection') is not None:
    context.configure(connection=context.config.attributes['connection'], target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(settings)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
