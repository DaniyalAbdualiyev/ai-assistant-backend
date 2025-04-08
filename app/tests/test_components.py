import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.ai_service import ContextManager, PromptEngine, ResponseGenerator
from app.models.message import Message
from app.database import Base
from datetime import datetime

# Add database fixture
@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    # Use SQLite in memory for testing
    engine = create_engine('sqlite:///:memory:')
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

class TestPromptEngine:
    @pytest.fixture
    def prompt_engine(self):
        return PromptEngine()

    def test_prompt_creation(self, prompt_engine):
        """Test prompt creation with different configurations"""
        config = {
            "business_type": "selling",
            "language": "en",
            "tone": "expert"
        }
        
        prompt = prompt_engine.create_prompt(
            query="What are your prices?",
            config=config
        )
        
        assert "Business Type: selling" in prompt
        assert "Focus on product features" in prompt
        assert "detailed, professional explanation" in prompt

class TestContextManager:
    @pytest.fixture
    def context_manager(self, db_session):
        return ContextManager(db_session)

    @pytest.fixture
    def sample_messages(self, db_session):
        """Create sample messages for testing"""
        messages = [
            Message(
                assistant_id=1,
                user_id=1,
                user_query="Test question 1",
                ai_response="Test response 1",
                timestamp=datetime.now()
            ),
            Message(
                assistant_id=1,
                user_id=1,
                user_query="Test question 2",
                ai_response="Test response 2",
                timestamp=datetime.now()  # This will be slightly later
            )
        ]
        
        for message in messages:
            db_session.add(message)
        db_session.commit()
        
        return messages

    @pytest.mark.asyncio
    async def test_context_retrieval(self, context_manager, sample_messages):
        """Test conversation context retrieval"""
        context = await context_manager.get_conversation_context(assistant_id=1)
        
        assert isinstance(context, list)
        assert len(context) == 2
        # Most recent message should be first (Test question 2)
        assert context[0].user_query == "Test question 2"
        # Older message should be second (Test question 1)
        assert context[1].user_query == "Test question 1" 