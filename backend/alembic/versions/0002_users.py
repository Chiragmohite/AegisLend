"""Add users for authentication; preserve Phase 1 infrastructure marker."""
from alembic import op
import sqlalchemy as sa
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("customer", "administrator", name="user_role",
            native_enum=False, create_constraint=True, length=13), nullable=False, server_default="customer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email"),
        mysql_charset="utf8mb4", mysql_collate="utf8mb4_bin", mysql_engine="InnoDB")


def downgrade():
    op.drop_table("users")
