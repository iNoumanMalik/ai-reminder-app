"""Cascade delete delivery_attempts when reminder is deleted.

Revision ID: 20260523_0001
Revises: 20260415_0001
Create Date: 2026-05-23

"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260523_0001"
down_revision: Union[str, None] = "20260415_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "delivery_attempts_reminder_id_fkey",
        "delivery_attempts",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "delivery_attempts_reminder_id_fkey",
        "delivery_attempts",
        "reminders",
        ["reminder_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "delivery_attempts_reminder_id_fkey",
        "delivery_attempts",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "delivery_attempts_reminder_id_fkey",
        "delivery_attempts",
        "reminders",
        ["reminder_id"],
        ["id"],
    )
