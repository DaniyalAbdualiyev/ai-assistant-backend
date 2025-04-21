"""
Migration script to add analytics tables to the database.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, MetaData, Table, create_engine
from datetime import datetime
import os

def upgrade(engine):
    """
    Create the conversation_analytics and client_analytics tables.
    """
    metadata = MetaData()
    
    # Create conversation_analytics table
    conversation_analytics = Table(
        'conversation_analytics', metadata,
        Column('id', Integer, primary_key=True, index=True),
        Column('assistant_id', Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False),
        Column('business_profile_id', Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False),
        Column('total_conversations', Integer, default=0),
        Column('total_messages', Integer, default=0),
        Column('avg_response_time', Float, default=0.0),
        Column('last_updated', DateTime, default=datetime.utcnow),
        Column('date', DateTime, default=datetime.utcnow)
    )
    
    # Create client_analytics table
    client_analytics = Table(
        'client_analytics', metadata,
        Column('id', Integer, primary_key=True, index=True),
        Column('client_session_id', String, nullable=False, index=True),
        Column('assistant_id', Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False),
        Column('business_profile_id', Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False),
        Column('session_start', DateTime, default=datetime.utcnow),
        Column('session_end', DateTime, nullable=True),
        Column('message_count', Integer, default=0),
        Column('avg_response_time', Float, nullable=True),
        Column('client_ip', String, nullable=True),
        Column('client_device', String, nullable=True),
        Column('client_location', String, nullable=True)
    )
    
    # Create tables
    metadata.create_all(engine)


def downgrade(engine):
    """
    Drop the analytics tables.
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    if 'client_analytics' in metadata.tables:
        metadata.tables['client_analytics'].drop(engine)
    
    if 'conversation_analytics' in metadata.tables:
        metadata.tables['conversation_analytics'].drop(engine)
