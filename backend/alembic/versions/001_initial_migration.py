# backend/alembic/versions/001_initial_migration.py
"""Initial migration with all models

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create stores table
    op.create_table('stores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moysklad_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('moysklad_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stores_archived'), 'stores', ['archived'], unique=False)
    op.create_index(op.f('ix_stores_id'), 'stores', ['id'], unique=False)
    op.create_index(op.f('ix_stores_moysklad_id'), 'stores', ['moysklad_id'], unique=True)
    op.create_index(op.f('ix_stores_name'), 'stores', ['name'], unique=False)

    # Create currencies table
    op.create_table('currencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moysklad_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('iso_code', sa.String(length=3), nullable=True),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('multiplicity', sa.Integer(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_currencies_code'), 'currencies', ['code'], unique=False)
    op.create_index(op.f('ix_currencies_id'), 'currencies', ['id'], unique=False)
    op.create_index(op.f('ix_currencies_moysklad_id'), 'currencies', ['moysklad_id'], unique=True)

    # Create employees table
    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moysklad_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=100), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('moysklad_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_archived'), 'employees', ['archived'], unique=False)
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index(op.f('ix_employees_moysklad_id'), 'employees', ['moysklad_id'], unique=True)
    op.create_index(op.f('ix_employees_name'), 'employees', ['name'], unique=False)

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moysklad_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('article', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('sale_price', sa.Float(), nullable=True),
        sa.Column('buy_price', sa.Float(), nullable=True),
        sa.Column('uom_name', sa.String(length=255), nullable=True),
        sa.Column('group_name', sa.String(length=255), nullable=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('moysklad_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_product_group', 'products', ['group_name'], unique=False)
    op.create_index('idx_product_search', 'products', ['name', 'code', 'article'], unique=False)
    op.create_index('idx_product_sync', 'products', ['moysklad_id', 'synced_at'], unique=False)
    op.create_index('idx_product_type_archived', 'products', ['entity_type', 'archived'], unique=False)
    op.create_index(op.f('ix_products_archived'), 'products', ['archived'], unique=False)
    op.create_index(op.f('ix_products_article'), 'products', ['article'], unique=False)
    op.create_index(op.f('ix_products_code'), 'products', ['code'], unique=False)
    op.create_index(op.f('ix_products_entity_type'), 'products', ['entity_type'], unique=False)
    op.create_index(op.f('ix_products_group_name'), 'products', ['group_name'], unique=False)
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_moysklad_id'), 'products', ['moysklad_id'], unique=True)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)

    # Create customers table
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moysklad_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('legal_title', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=100), nullable=True),
        sa.Column('inn', sa.String(length=12), nullable=True),
        sa.Column('kpp', sa.String(length=9), nullable=True),
        sa.Column('ogrn', sa.String(length=15), nullable=True),
        sa.Column('legal_address', sa.Text(), nullable=True),
        sa.Column('actual_address', sa.Text(), nullable=True),
        sa.Column('group_name', sa.String(length=255), nullable=True),
        sa.Column('discount_percentage', sa.Float(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('moysklad_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_group', 'customers', ['group_name'], unique=False)
    op.create_index('idx_customer_search', 'customers', ['name', 'inn', 'email'], unique=False)
    op.create_index('idx_customer_status', 'customers', ['archived'], unique=False)
    op.create_index(op.f('ix_customers_archived'), 'customers', ['archived'], unique=False)
    op.create_index(op.f('ix_customers_code'), 'customers', ['code'], unique=False)
    op.create_index(op.f('ix_customers_group_name'), 'customers', ['group_name'], unique=False)
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_inn'), 'customers', ['inn'], unique=False)
    op.create_index(op.f('ix_customers_moysklad_id'), 'customers', ['moysklad_id'], unique=True)
    op.create_index(op.f('ix_customers_name'), 'customers', ['name'], unique=False)

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('moysklad_id', sa.String(length=36), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('moment', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sum_total', sa.Float(), nullable=True),
        sa.Column('agent_name', sa.String(length=255), nullable=True),
        sa.Column('organization_name', sa.String(length=255), nullable=True),
        sa.Column('store_name', sa.String(length=255), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('moysklad_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_agent', 'documents', ['agent_name'], unique=False)
    op.create_index('idx_document_status', 'documents', ['archived'], unique=False)
    op.create_index('idx_document_type_date', 'documents', ['document_type', 'moment'], unique=False)
    op.create_index(op.f('ix_documents_agent_name'), 'documents', ['agent_name'], unique=False)
    op.create_index(op.f('ix_documents_archived'), 'documents', ['archived'], unique=False)
    op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_moment'), 'documents', ['moment'], unique=False)
    op.create_index(op.f('ix_documents_moysklad_id'), 'documents', ['moysklad_id'], unique=True)

    # Create stock_reports table
    op.create_table('stock_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('moysklad_product_id', sa.String(length=36), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('moysklad_store_id', sa.String(length=36), nullable=True),
        sa.Column('stock_quantity', sa.Float(), nullable=False),
        sa.Column('reserve_quantity', sa.Float(), nullable=False),
        sa.Column('inTransit_quantity', sa.Float(), nullable=False),
        sa.Column('available_quantity', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_stock_moysklad', 'stock_reports', ['moysklad_product_id', 'moysklad_store_id'], unique=False)
    op.create_index('idx_stock_product_store', 'stock_reports', ['product_id', 'store_id'], unique=False)
    op.create_index(op.f('ix_stock_reports_id'), 'stock_reports', ['id'], unique=False)
    op.create_index(op.f('ix_stock_reports_moysklad_product_id'), 'stock_reports', ['moysklad_product_id'], unique=False)
    op.create_index(op.f('ix_stock_reports_product_id'), 'stock_reports', ['product_id'], unique=False)
    op.create_index(op.f('ix_stock_reports_store_id'), 'stock_reports', ['store_id'], unique=False)

    # Create product_turnovers table
    op.create_table('product_turnovers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('moysklad_product_id', sa.String(length=36), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('stock_start', sa.Float(), nullable=False),
        sa.Column('stock_end', sa.Float(), nullable=False),
        sa.Column('income_quantity', sa.Float(), nullable=False),
        sa.Column('outcome_quantity', sa.Float(), nullable=False),
        sa.Column('income_sum', sa.Float(), nullable=False),
        sa.Column('outcome_sum', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_turnover_moysklad', 'product_turnovers', ['moysklad_product_id'], unique=False)
    op.create_index('idx_turnover_product_period', 'product_turnovers', ['product_id', 'period_start', 'period_end'], unique=False)
    op.create_index(op.f('ix_product_turnovers_id'), 'product_turnovers', ['id'], unique=False)
    op.create_index(op.f('ix_product_turnovers_moysklad_product_id'), 'product_turnovers', ['moysklad_product_id'], unique=False)
    op.create_index(op.f('ix_product_turnovers_period_start'), 'product_turnovers', ['period_start'], unique=False)
    op.create_index(op.f('ix_product_turnovers_product_id'), 'product_turnovers', ['product_id'], unique=False)

    # Create sync_logs table
    op.create_table('sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_processed', sa.Integer(), nullable=False),
        sa.Column('records_created', sa.Integer(), nullable=False),
        sa.Column('records_updated', sa.Integer(), nullable=False),
        sa.Column('records_errors', sa.Integer(), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_date', 'sync_logs', ['started_at'], unique=False)
    op.create_index('idx_sync_type_status', 'sync_logs', ['sync_type', 'status'], unique=False)
    op.create_index(op.f('ix_sync_logs_id'), 'sync_logs', ['id'], unique=False)
    op.create_index(op.f('ix_sync_logs_status'), 'sync_logs', ['status'], unique=False)
    op.create_index(op.f('ix_sync_logs_sync_type'), 'sync_logs', ['sync_type'], unique=False)

    # Создание индексов для производительности
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_fulltext ON products USING GIN (to_tsvector('russian', name || ' ' || COALESCE(description, '')))")
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_fulltext ON customers USING GIN (to_tsvector('russian', name || ' ' || COALESCE(legal_title, '')))")


def downgrade() -> None:
    # Удаление таблиц в обратном порядке
    op.drop_table('sync_logs')
    op.drop_table('product_turnovers')
    op.drop_table('stock_reports')
    op.drop_table('documents')
    op.drop_table('customers')
    op.drop_table('products')
    op.drop_table('employees')
    op.drop_table('currencies')
    op.drop_table('stores')
    op.drop_table('users')