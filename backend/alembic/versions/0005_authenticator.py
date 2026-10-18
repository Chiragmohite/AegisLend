"""Optional authenticator-based OTP enrollment."""
from alembic import op
import sqlalchemy as sa
revision='0005'
down_revision='0004'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('authenticators',sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),primary_key=True),sa.Column('encrypted_secret',sa.String(512),nullable=False),sa.Column('enabled',sa.Integer(),nullable=False),sa.Column('last_step',sa.Integer(),nullable=False),mysql_charset='utf8mb4',mysql_collate='utf8mb4_bin',mysql_engine='InnoDB')
def downgrade():op.drop_table('authenticators')
