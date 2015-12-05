"""add publish state to events

Revision ID: ff1307c5135
Revises: 53a929e1d92d
Create Date: 2015-12-04 22:00:32.207419

"""

# revision identifiers, used by Alembic.
revision = 'ff1307c5135'
down_revision = '53a929e1d92d'

from alembic import op
import sqlalchemy as sa


enum = sa.Enum('draft', 'published', name='publish_states')


def upgrade():
    op.execute("CREATE TYPE publish_states AS ENUM ('draft', 'published');")
    op.add_column('events', sa.Column('publish_status', enum, server_default='published'))


def downgrade():
    op.drop_column('events', 'publish_status')
    op.execute("DROP TYPE publish_states;")
