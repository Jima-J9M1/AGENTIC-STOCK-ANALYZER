"""
Simple Test - Basic functionality test without unicode characters
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_fmp_api():
    """Test FMP API directly"""
    print("Testing FMP API connection...")
    
    try:
        from src.api.client import fmp_api_request
        
        result = await fmp_api_request('profile', {'symbol': 'AAPL'})
        
        if 'error' in result:
            print(f"ERROR: {result['error']}")
            return False
        elif isinstance(result, list) and len(result) > 0:
            company = result[0].get('companyName', 'Unknown Company')
            print(f"SUCCESS: Retrieved profile for {company}")
            return True
        else:
            print("WARNING: No data returned")
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_company_tool():
    """Test company profile tool"""
    print("Testing company profile tool...")
    
    try:
        from src.tools.company import get_company_profile
        
        result = await get_company_profile("AAPL")
        
        if "Error" in result:
            print(f"ERROR: {result}")
            return False
        else:
            print(f"SUCCESS: Got company profile ({len(result)} chars)")
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_quote_tool():
    """Test quote tool"""
    print("Testing quote tool...")
    
    try:
        from src.tools.quote import get_quote
        
        result = await get_quote("AAPL")
        
        if "Error" in result:
            print(f"ERROR: {result}")
            return False
        else:
            print(f"SUCCESS: Got quote data ({len(result)} chars)")
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def main():
    """Run tests"""
    print("FMP Stock Analysis System - Simple Test")
    print("=" * 50)
    
    # Check environment
    print("Checking environment variables...")
    if not os.getenv("FMP_API_KEY"):
        print("ERROR: FMP_API_KEY not set")
        return False
    print("FMP_API_KEY: OK")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set (needed for AI analysis)")
    else:
        print("OPENAI_API_KEY: OK")
    
    # Run tests
    tests = [
        ("FMP API Connection", test_fmp_api),
        ("Company Tool", test_company_tool),
        ("Quote Tool", test_quote_tool)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"ERROR: Test failed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n--- Test Summary ---")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("ALL TESTS PASSED!")
        print("\nYour FMP data system is working correctly.")
        print("You can now use the analysis clients with confidence.")
        return True
    else:
        print("Some tests failed. Check errors above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    except Exception as e:
        print(f"FATAL ERROR: {e}")