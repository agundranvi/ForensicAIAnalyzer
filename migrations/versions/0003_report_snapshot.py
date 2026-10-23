from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "reports", sa.Column("snapshot", sa.JSON(), nullable=False, server_default="{}")
    )


def downgrade():
    raise RuntimeError("Destructive downgrade disabled")
