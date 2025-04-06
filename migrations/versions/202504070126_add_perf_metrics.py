"""Add performance metrics columns

Revision ID: 202504070126
Revises: 
Create Date: 2025-04-07 01:26:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '202504070126'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('submissions', sa.Column('performance_metrics', sa.JSON))
    op.add_column('submissions', sa.Column('timestamp', sa.DateTime))

def downgrade():
    op.drop_column('submissions', 'performance_metrics')
    op.drop_column('submissions', 'timestamp')
