"""
Test Trading Alert Analysis
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment first
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verify environment
print(f"FMP_API_KEY loaded: {'YES' if os.getenv('FMP_API_KEY') else 'NO'}")
print(f"OPENAI_API_KEY loaded: {'YES' if os.getenv('OPENAI_API_KEY') else 'NO'}")

if not os.getenv('FMP_API_KEY') or not os.getenv('OPENAI_API_KEY'):
    print("ERROR: Missing required API keys")
    exit(1)

# Now import and test
from stock_analyzer import analyze_trading_alert

async def test_trading_alert():
    print("\n=== Testing Trading Alert Analysis ===")
    
    # Test case 1: Breakout alert
    print("\nTest 1: Breakout Alert")
    print("-" * 30)
    
    result1 = await analyze_trading_alert(
        ticker="AAPL",
        alert_text="Apple breaking above key resistance at $195 with strong volume spike",
        timeframe="1D"
    )
    
    print("Alert: Apple breaking above key resistance at $195 with strong volume spike")
    print("Result:")
    print(result1)
    
    print("\n" + "="*60)
    
    # Test case 2: Support test alert
    print("\nTest 2: Support Test Alert")
    print("-" * 30)
    
    result2 = await analyze_trading_alert(
        ticker="TSLA", 
        alert_text="Tesla testing critical support at $240 level with declining volume",
        timeframe="1D"
    )
    
    print("Alert: Tesla testing critical support at $240 level with declining volume")
    print("Result:")
    print(result2)
    
    print("\n" + "="*60)
    
    # Test case 3: Gap up alert
    print("\nTest 3: Gap Up Alert")
    print("-" * 30)
    
    result3 = await analyze_trading_alert(
        ticker="NVDA",
        alert_text="NVIDIA gapping up 3% pre-market on earnings beat, approaching $150 resistance",
        timeframe="1D"
    )
    
    print("Alert: NVIDIA gapping up 3% pre-market on earnings beat, approaching $150 resistance")
    print("Result:")
    print(result3)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_trading_alert())
    except Exception as e:
        print(f"Test failed: {e}")