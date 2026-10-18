"""Full workflow on an explicitly configured dedicated MySQL database; rollback all test rows."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from app.config import Settings
from app.db import make_engine,get_session
from app.main import create_app
from app.seed import seed
from test_integrated import test_complete_customer_to_admin_workflow as run_workflow


@pytest.mark.mysql
@pytest.mark.skipif(os.getenv('RUN_MYSQL_DOMAIN_TESTS')!='1',reason='Requires migrated dedicated MySQL test database')
def test_mysql_complete_domain_workflow(tmp_path):
    settings=Settings()
    assert settings.db_name.startswith('aegislend_test_'),'Never use a customer database'
    settings.ids_model_path=tmp_path/'ids.joblib';settings.auth_rate_limit=1000
    engine=make_engine(settings)
    with engine.connect() as connection:
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()=='0007'
        connection.rollback();transaction=connection.begin()
        factory=sessionmaker(bind=connection,expire_on_commit=False,join_transaction_mode='create_savepoint')
        try:
            with factory() as session:seed(session,settings)
            app=create_app(settings);app.state.session_factory=factory
            def sessions():
                with factory() as session:yield session
            app.dependency_overrides[get_session]=sessions
            with TestClient(app) as client:run_workflow((client,factory,settings,engine,None))
        finally:transaction.rollback()
    engine.dispose()
