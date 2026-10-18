"""Database-enforced single active session, including engines without row locks.
Sessions predating this invariant require a fresh login; account and draft data stay intact.
"""
from alembic import op
import sqlalchemy as sa
revision='0007'
down_revision='0006'
branch_labels=None
depends_on=None
def upgrade():
    op.execute(sa.text('UPDATE auth_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE revoked_at IS NULL'))
    with op.batch_alter_table('auth_sessions') as batch:
        batch.add_column(sa.Column('active_user',sa.String(36),nullable=True))
        batch.create_unique_constraint('uq_auth_sessions_active_user',['active_user'])
def downgrade():
    with op.batch_alter_table('auth_sessions') as batch:
        batch.drop_constraint('uq_auth_sessions_active_user',type_='unique')
        batch.drop_column('active_user')
