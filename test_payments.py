import requests
import json
import webbrowser  # Add this import

BASE_URL = "http://localhost:8000"

def test_subscription_setup():
    # 1. Create a test subscription plan
    plan_data = {
        "name": "Premium Test Plan",
        "price": 29.99,
        "features": "All premium features included"
    }
    
    response = requests.post(f"{BASE_URL}/payments/plans", json=plan_data)
    print("Created plan:", json.dumps(response.json(), indent=2))
    return response.json()["id"]

def test_complete_payment_flow():
    # Get available plans
    response = requests.get(f"{BASE_URL}/payments/plans")
    plans = response.json()
    print("\nAvailable plans:", json.dumps(plans, indent=2))

    # Create a subscription
    subscription_data = {
        "user_id": 1,
        "plan_id": plans[0]["id"] if plans else 1
    }
    
    response = requests.post(
        f"{BASE_URL}/payments/subscriptions",
        json=subscription_data
    )
    result = response.json()
    print("\nCheckout session:", json.dumps(result, indent=2))
    
    # Print the URL for manual testing
    print("\nCheckout URL:", result["url"])
    
    # Optionally, open the URL in browser
    webbrowser.open(result["url"])
    
    return result["session_id"]

if __name__ == "__main__":
    print("Starting payment system verification...\n")
    
    try:
        # Create test plan if needed
        plan_id = test_subscription_setup()
        
        # Test complete payment flow
        session_id = test_complete_payment_flow()
        
        print("\nTest Completion Instructions:")
        print("1. Use this test card number: 4242 4242 4242 4242")
        print("2. Any future expiry date")
        print("3. Any 3-digit CVC")
        print("4. Any billing postal code")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}") 