"""Initial migration

Revision ID: 001_init
Revises:
Create Date: 2026-05-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('store', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, default='EUR'),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('product_url', sa.String(), nullable=False),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.Column('categories', JSON(), nullable=True),
        sa.UniqueConstraint('external_id', 'store', name='uq_product_external_store'),
    )
    # Create price_history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.id'), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('raw_price', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    # Create scrape_jobs table
    op.create_table(
        'scrape_jobs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('keyword', sa.String(), nullable=False),
        sa.Column('store', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', name='jobstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('products_found', sa.Integer(), nullable=False, default=0),
        sa.Column('pages', sa.Integer(), nullable=False, default=1),
        sa.Column('async_mode', sa.Boolean(), nullable=False, default=True),
    )


def downgrade() -> None:
    op.drop_table('scrape_jobs')
    op.drop_table('price_history')
    op.drop_table('products')
