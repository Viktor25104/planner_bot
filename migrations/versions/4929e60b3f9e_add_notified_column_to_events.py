"""Add notified column to events

Revision ID: 4929e60b3f9e
Revises: 81dae09f3e6a
Create Date: 2025-05-22 09:37:39.424290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4929e60b3f9e'
down_revision: Union[str, None] = '81dae09f3e6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('notified', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'notified')
    # ### end Alembic commands ###
