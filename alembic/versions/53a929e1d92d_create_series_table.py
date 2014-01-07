"""create series table

Revision ID: 53a929e1d92d
Revises: None
Create Date: 2014-01-06 14:06:18.337772

"""

# revision identifiers, used by Alembic.
revision = '53a929e1d92d'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'series',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(250), unique=True, nullable=False),
    )
    op.add_column(
        'events',
        sa.Column('series_id', sa.Integer, sa.ForeignKey('series.id'), nullable=True)
    )


def downgrade():
    op.drop_column('events', 'series_id')
    op.drop_table('series')
