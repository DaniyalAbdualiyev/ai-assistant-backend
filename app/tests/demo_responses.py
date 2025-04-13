import pytest
import asyncio
from app.services.ai_service import AIService

async def demonstrate_responses():
    ai_service = AIService()
    
    # Test query
    query = "What are your prices?"
    
    # Test different business types
    configs = [
        {
            "business_type": "selling",
            "language": "en",
            "tone": "normal"
        },
        {
            "business_type": "consulting",
            "language": "en",
            "tone": "professional"
        },
        {
            "business_type": "tech_support",
            "language": "en",
            "tone": "helpful"
        }
    ]
    
    print("\n=== AI Assistant Response Demo ===\n")
    print(f"Query: '{query}'\n")
    
    for config in configs:
        print(f"\n{config['business_type'].upper()} ASSISTANT:")
        response = await ai_service.get_response(
            query=query,
            config=config,
            assistant_id=1,
            user_id=1
        )
        print(f"Response: {response}\n")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(demonstrate_responses()) 