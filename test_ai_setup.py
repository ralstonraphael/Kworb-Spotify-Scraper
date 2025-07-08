"""Test script to verify OpenAI integration setup."""
from src.ai_helper import AIHelper

def test_openai_connection():
    """Test the OpenAI connection and API key setup."""
    try:
        ai_helper = AIHelper()
        # Test with a simple data structure
        test_data = [{"title": "Test Song", "artist": "Test Artist", "rank": 1}]
        
        # Try to get insights
        result = ai_helper.analyze_chart_data(test_data)
        
        if result["status"] == "success":
            print("✅ OpenAI integration test passed!")
            print("Sample insight:", result["insights"][:100] + "...")
        else:
            print("❌ Test failed:", result.get("error", "Unknown error"))
            
    except Exception as e:
        print("❌ Setup verification failed:")
        print(f"Error: {str(e)}")
        
if __name__ == "__main__":
    print("Testing OpenAI integration...")
    test_openai_connection() 