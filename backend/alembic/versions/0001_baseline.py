"""Phase 1 infrastructure baseline."""
from alembic import op
import sqlalchemy as sa
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    table = op.create_table("system_metadata",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.String(255), nullable=False),
        mysql_charset="utf8mb4", mysql_engine="InnoDB")
    op.bulk_insert(table, [{"key": "schema_phase", "value": "1"}])


def downgrade():
    op.drop_table("system_metadata")
