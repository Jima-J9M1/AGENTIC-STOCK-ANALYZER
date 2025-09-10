"""
Simple test for conversational flow
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)

from simple_prompt_server import SimplePromptAnalyzer

async def test():
    print("Testing Conversational System")
    print("=" * 40)
    
    analyzer = SimplePromptAnalyzer()
    
    try:
        await analyzer.start_system()
        
        # Your original prompt
        prompt = "Below are multiple recent frames for a ticker. Below is a recent alert about the price action of this security. Please provide an analysis as to whether we should Trade, Monitor, or Ignore this alert based on its text and the price action. You must start your response with a single word: Trade, Monitor, or Ignore. Then, provide a few sentences as to why you took that stance"
        
        print("Step 1: Generic prompt")
        print("Prompt:", prompt[:80] + "...")
        
        result1 = await analyzer.analyze_prompt(prompt)
        print("Response:", result1)
        
        if result1.startswith("NEED_TICKER"):
            print("\nStep 2: Providing ticker AAPL")
            result2 = await analyzer.analyze_prompt(prompt, "AAPL")
            print("Response:", result2[:100] + "...")
            
            # Check format
            first_word = result2.split()[0] if result2.split() else ""
            if first_word in ["Trade", "Monitor", "Ignore"]:
                print("SUCCESS: Response starts with", first_word)
            else:
                print("ISSUE: Response starts with", first_word)
        
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(test())