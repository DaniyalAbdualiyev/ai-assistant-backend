import pytest
from app.services.ai_service import AIService, ContextManager, PromptEngine, ResponseGenerator
from app.models.message import Message
from app.models.assistant import AIAssistant

class TestAIAssistant:
    @pytest.fixture
    def ai_service(self):
        return AIService()

    @pytest.fixture
    def test_config(self):
        return {
            "business_type": "selling",
            "language": "en",
            "tone": "normal"
        }

    @pytest.mark.asyncio
    async def test_basic_response(self, ai_service, test_config):
        """Test basic response generation"""
        response = await ai_service.get_response(
            query="What are your prices?",
            config=test_config,
            assistant_id=1,
            user_id=1
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_business_types(self, ai_service):
        """Test responses for different business types"""
        test_cases = [
            {
                "type": "selling",
                "query": "Tell me about your offerings",
                "expected_keywords": ["product", "price", "available"],
                "sample_query": "What products do you have available and what are their prices?"
            },
            {
                "type": "consulting",
                "query": "I need help with my business",
                "expected_keywords": ["schedule", "consultation", "advice"],
                "sample_query": "Would you like to schedule a consultation to discuss your business needs?"
            },
            {
                "type": "tech_support",
                "query": "My device isn't working",
                "expected_keywords": ["troubleshoot", "help", "support"],
                "sample_query": "Let me help you troubleshoot your device issue. What specific problems are you experiencing?"
            }
        ]

        for case in test_cases:
            config = {
                "business_type": case["type"], 
                "language": "en",
                "tone": "normal"
            }
            
            print(f"\nTesting {case['type']} business type:")
            print(f"Query: {case['query']}")
            
            response = await ai_service.get_response(
                query=case["query"],
                config=config,
                assistant_id=1,
                user_id=1
            )
            
            print(f"Response: {response}")
            
            # Check if response contains relevant keywords
            found_keywords = [keyword for keyword in case["expected_keywords"] 
                             if keyword in response.lower()]
            
            assert len(found_keywords) > 0, (
                f"Response for {case['type']} business type doesn't contain any expected keywords.\n"
                f"Expected keywords: {case['expected_keywords']}\n"
                f"Response: {response}"
            )

    @pytest.mark.asyncio
    async def test_conversation_history(self, ai_service, test_config):
        """Test conversation history maintenance"""
        queries = [
            "What products do you have?",
            "How much is the first one?",
            "Can I pay with credit card?"
        ]
        
        for query in queries:
            response = await ai_service.get_response(
                query=query,
                config=test_config,
                assistant_id=1,
                user_id=1
            )
        
        # Check conversation history
        conversation = ai_service.conversations.get("1_1", [])
        assert len(conversation) == len(queries) * 2  # Each query has a response 