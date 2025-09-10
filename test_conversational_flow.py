"""
Test the conversational flow for trading alerts
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)

from simple_prompt_server import SimplePromptAnalyzer

async def test_conversational_system():
    print("=== Testing Conversational Trading Alert System ===\n")
    
    analyzer = SimplePromptAnalyzer()
    
    try:
        await analyzer.start_system()
        
        # Test the exact flow you want
        print("Test: Your Original Prompt Flow")
        print("-" * 60)
        
        # Step 1: Generic prompt (should ask for ticker)
        prompt = "Below are multiple recent frames for a ticker. Below is a recent alert about the price action of this security. Please provide an analysis as to whether we should Trade, Monitor, or Ignore this alert based on its text and the price action. You must start your response with a single word: Trade, Monitor, or Ignore. Then, provide a few sentences as to why you took that stance"
        
        print(f"User Prompt: {prompt}")
        print()
        
        result1 = await analyzer.analyze_prompt(prompt)
        print("System Response:", result1)
        print()
        
        # Step 2: Provide ticker (should continue analysis)
        if result1.startswith("NEED_TICKER:"):
            print("User provides ticker: AAPL")
            result2 = await analyzer.analyze_prompt(prompt, "AAPL")
            print("System Response:")
            print(result2)
            print()
            
            # Check format
            if result2.startswith(("Trade", "Monitor", "Ignore")):
                print("✅ FORMAT CHECK: Response starts with Trade/Monitor/Ignore")
            else:
                print("❌ FORMAT CHECK: Response does NOT start with Trade/Monitor/Ignore")
                print(f"   Actual start: '{result2[:20]}...'")
        
        print("\n" + "="*80)
        
        # Test with specific ticker directly
        print("\nTest 2: Direct Ticker Analysis")
        print("-" * 40)
        
        direct_prompt = "TSLA breaking above $250 resistance with strong volume. Please provide analysis as to whether we should Trade, Monitor, or Ignore this alert. Start with Trade, Monitor, or Ignore."
        
        print(f"User Prompt: {direct_prompt}")
        result3 = await analyzer.analyze_prompt(direct_prompt)
        print("System Response:")
        print(result3)
        
        # Check format
        if result3.startswith(("Trade", "Monitor", "Ignore")):
            print("✅ FORMAT CHECK: Response starts with Trade/Monitor/Ignore")
        else:
            print("❌ FORMAT CHECK: Response does NOT start with Trade/Monitor/Ignore")
            
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(test_conversational_system())