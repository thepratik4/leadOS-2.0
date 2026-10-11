"""Initial schema for companies, evidence, signals, saved leads, and search runs

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-10 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Companies
    op.create_table(
        'companies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('domain', sa.String(length=255), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('employee_range', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_companies_domain', 'companies', ['domain'])
    op.create_index('ix_companies_name', 'companies', ['name'])
    op.create_index('ix_companies_industry', 'companies', ['industry'])
    op.create_index('ix_companies_country', 'companies', ['country'])

    # 2. Evidence
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_type', sa.String(length=100), nullable=False),
        sa.Column('claim_value', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_category', sa.String(length=100), nullable=False),
        sa.Column('source_excerpt', sa.Text(), nullable=True),
        sa.Column('publication_date', sa.String(length=50), nullable=True),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verification_status', sa.String(length=50), nullable=False),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evidence_company_id', 'evidence', ['company_id'])
    op.create_index('ix_evidence_verification_status', 'evidence', ['verification_status'])

    # 3. Business Signals
    op.create_table(
        'business_signals',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evidence_id', sa.String(length=36), sa.ForeignKey('evidence.id', ondelete='SET NULL'), nullable=True),
        sa.Column('signal_type', sa.String(length=100), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_business_signals_company_id', 'business_signals', ['company_id'])
    op.create_index('ix_business_signals_signal_type', 'business_signals', ['signal_type'])

    # 4. Saved Leads
    op.create_table(
        'saved_leads',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_saved_leads_company_id', 'saved_leads', ['company_id'])
    op.create_index('ix_saved_leads_status', 'saved_leads', ['status'])

    # 5. Search Runs
    op.create_table(
        'search_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('filters_json', sa.Text(), nullable=False),
        sa.Column('candidate_count', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('search_runs')
    op.drop_table('saved_leads')
    op.drop_table('business_signals')
    op.drop_table('evidence')
    op.drop_table('companies')
