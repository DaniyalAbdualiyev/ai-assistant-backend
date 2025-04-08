import pytest
from app.services.ai_service import AIService, MessageProcessor, ResponseFormatter
from app.models.message import Message

class TestPlatformIntegration:
    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing"""
        return AIService()

    @pytest.fixture
    def message_processor(self, ai_service):
        """Create message processor with AI service"""
        return MessageProcessor(ai_service)

    @pytest.mark.asyncio
    async def test_instagram_formatting(self, message_processor):
        """Test Instagram message processing"""
        response = await message_processor.process_message(
            message="What are your prices?",
            platform="instagram",
            assistant_id=1,
            user_id=1
        )
        
        assert isinstance(response, dict)
        assert "text" in response
        assert len(response["text"]) <= 2000  # Instagram limit

    @pytest.mark.asyncio
    async def test_whatsapp_formatting(self, message_processor):
        """Test WhatsApp message processing"""
        response = await message_processor.process_message(
            message="What are your prices?",
            platform="whatsapp",
            assistant_id=1,
            user_id=1
        )
        
        assert isinstance(response, dict) 