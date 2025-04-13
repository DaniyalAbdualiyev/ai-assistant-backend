import asyncio
import time
from app.services.ai_service import AIService
from statistics import mean
import datetime

async def measure_response_time():
    ai_service = AIService()
    test_queries = [
        "What are your prices?",
        "Tell me about your services",
        "How can I contact support?"
    ]
    
    business_types = ["selling", "consulting", "tech_support"]
    results = []
    
    print("\n=== AI Assistant Performance Test ===\n")
    print(f"Starting tests at: {datetime.datetime.now()}\n")
    
    for business_type in business_types:
        config = {
            "business_type": business_type,
            "language": "en",
            "tone": "normal"
        }
        
        print(f"\nTesting {business_type.upper()} Assistant:")
        print("-" * 40)
        
        for query in test_queries:
            start_time = time.time()
            
            response = await ai_service.get_response(
                query=query,
                config=config,
                assistant_id=1,
                user_id=1
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            results.append(response_time)
            
            print(f"Query: '{query}'")
            print(f"Response time: {response_time:.3f} seconds")
            print(f"Response length: {len(response)} characters")
            print("-" * 40)
    
    # Calculate statistics
    avg_time = mean(results)
    max_time = max(results)
    min_time = min(results)
    total_requests = len(results)
    
    print("\n=== Performance Summary ===")
    print(f"Total requests: {total_requests}")
    print(f"Average response time: {avg_time:.3f} seconds")
    print(f"Fastest response: {min_time:.3f} seconds")
    print(f"Slowest response: {max_time:.3f} seconds")
    print(f"Responses under 1 second: {len([t for t in results if t < 1])}/{total_requests}")
    
    # Visual representation of response times
    print("\nResponse Time Distribution:")
    for i, time_value in enumerate(results, 1):
        bar = "█" * int(time_value * 50)
        print(f"Request {i:2d}: {time_value:.3f}s |{bar}")

if __name__ == "__main__":
    asyncio.run(measure_response_time()) 