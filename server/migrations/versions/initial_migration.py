"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2025-05-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create absence_periods table
    op.create_table('absence_periods',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_absence_periods_id'), 'absence_periods', ['id'], unique=False)


def downgrade() -> None:
    # Drop absence_periods table
    op.drop_index(op.f('ix_absence_periods_id'), table_name='absence_periods')
    op.drop_table('absence_periods')
