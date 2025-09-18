"""create story reports table

Revision ID: create_story_reports
Revises: 
Create Date: 2025-01-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'create_story_reports'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create story_reports table
    op.create_table('story_reports',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('story_id', sa.String(36), nullable=False),
        sa.Column('reporter_id', sa.String(36), nullable=False),
        sa.Column('reason', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for faster queries
    op.create_index('idx_story_reports_story_id', 'story_reports', ['story_id'])
    op.create_index('idx_story_reports_reporter_id', 'story_reports', ['reporter_id'])
    op.create_index('idx_story_reports_created_at', 'story_reports', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_story_reports_created_at', table_name='story_reports')
    op.drop_index('idx_story_reports_reporter_id', table_name='story_reports')
    op.drop_index('idx_story_reports_story_id', table_name='story_reports')
    
    # Drop table
    op.drop_table('story_reports')
