"""
Test the improved prompt system
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)

from simple_prompt_server import SimplePromptAnalyzer

async def test_improved_system():
    print("=== Testing Improved Prompt System ===\n")
    
    analyzer = SimplePromptAnalyzer()
    
    try:
        await analyzer.start_system()
        
        # Test 1: Your original problematic prompt
        print("Test 1: Generic prompt (should ask for ticker)")
        print("-" * 50)
        prompt1 = "Below are multiple recent frames for a ticker. Below is a recent alert about the price action of this security. Please provide an analysis as to whether we should Trade, Monitor, or Ignore this alert based on its text and the price action. You must start your response with a single word: Trade, Monitor, or Ignore."
        
        result1 = await analyzer.analyze_prompt(prompt1)
        print("Result:")
        print(result1)
        print("\n" + "="*80 + "\n")
        
        # Test 2: Specific ticker prompt
        print("Test 2: Specific ticker prompt (should analyze)")
        print("-" * 50)
        prompt2 = "AAPL breaking above key resistance at $195 with strong volume. Should I Trade, Monitor, or Ignore this alert?"
        
        result2 = await analyzer.analyze_prompt(prompt2)
        print("Result:")
        print(result2)
        print("\n" + "="*80 + "\n")
        
        # Test 3: Company name (should work)
        print("Test 3: Company name prompt (should analyze)")
        print("-" * 50)
        prompt3 = "Tesla testing support at $240 with declining volume. Trade, Monitor, or Ignore?"
        
        result3 = await analyzer.analyze_prompt(prompt3)
        print("Result:")
        print(result3)
        
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(test_improved_system())