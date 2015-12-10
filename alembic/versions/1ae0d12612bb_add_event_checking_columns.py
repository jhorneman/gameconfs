"""add event checking columns

Revision ID: 1ae0d12612bb
Revises: ff1307c5135
Create Date: 2015-12-10 14:53:40.800203

"""

# revision identifiers, used by Alembic.
revision = '1ae0d12612bb'
down_revision = 'ff1307c5135'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # This server default works for PostgreSQL but not SQLite.
    op.add_column('events', sa.Column('last_checked_at', sa.DateTime, server_default=sa.text("TIMESTAMP '2011-01-01 00:00:00'")))
    op.add_column('events', sa.Column('is_being_checked', sa.Boolean, server_default=sa.text("TRUE")))


def downgrade():
    op.drop_column('events', 'is_being_checked')
    op.drop_column('events', 'last_checked_at')
