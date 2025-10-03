from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5g6"
down_revision = "a1b2c3d4e5f7"  # keep your current value if different
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # 1) add column nullable (no default)
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("retain_until", sa.DateTime(), nullable=True))

        # 2) backfill values using SQLite datetime function
        op.execute(
            sa.text(
                "UPDATE users "
                "SET retain_until = DATETIME('now','+7 years') "
                "WHERE retain_until IS NULL"
            )
        )

        # 3) make NOT NULL (batch_alter_table rebuilds table safely on SQLite)
        with op.batch_alter_table("users") as batch:
            batch.alter_column(
                "retain_until",
                existing_type=sa.DateTime(),
                nullable=False,
            )
    else:
        # PostgreSQL (and others): keep a true DB default
        op.add_column(
            "users",
            sa.Column(
                "retain_until",
                sa.DateTime(),
                server_default=sa.text("NOW() + INTERVAL '7 years'"),
                nullable=False,
            ),
        )


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("retain_until")
