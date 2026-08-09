"""Switch email verification / password reset to OTP codes.

Adds an attempts counter to auth_tokens for brute-force protection and
drops the uniqueness constraint on token_hash: short numeric OTP codes are
looked up scoped by user_id, so two different users legitimately being
issued the same hash is expected and must not raise an IntegrityError.

Revision ID: 20260809_0001
Revises: 20260526_0001
Create Date: 2026-08-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260809_0001"
down_revision: Union[str, None] = "20260526_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auth_tokens",
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.drop_index("ix_auth_tokens_token_hash", table_name="auth_tokens")
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"])


def downgrade() -> None:
    # Any legitimate cross-user hash collisions created under OTP semantics
    # would violate a unique index, so this table is cleared before the
    # unique index is restored.
    op.execute("DELETE FROM auth_tokens")
    op.drop_index("ix_auth_tokens_token_hash", table_name="auth_tokens")
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"], unique=True)
    op.drop_column("auth_tokens", "attempts")
