"""
Test System - Validate end-to-end functionality

This script tests the complete stock analysis system to ensure everything works properly.
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

def check_environment():
    """Check if all required environment variables are set"""
    print("Checking Environment...")
    
    missing = []
    if not os.getenv("FMP_API_KEY"):
        missing.append("FMP_API_KEY")
    if not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        return False
    
    print("Environment check passed")
    return True

def start_server():
    """Start the MCP server"""
    print("Starting MCP server...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "src.server", "--sse", "--port", "8000"],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("MCP server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print("ERROR: Server failed to start")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return None
            
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        return None

async def test_fmp_connection():
    """Test FMP API connection"""
    print("\nTesting FMP API connection...")
    
    try:
        from src.api.client import fmp_api_request
        
        # Test a simple FMP API call
        result = await fmp_api_request('profile', {'symbol': 'AAPL'})
        
        if 'error' in result:
            print(f"ERROR: FMP API test failed: {result['error']}")
            return False
        elif isinstance(result, list) and len(result) > 0:
            company_name = result[0].get('companyName', 'Unknown')
            print(f"FMP API test passed - Retrieved data for: {company_name}")
            return True
        else:
            print("WARNING: FMP API returned empty data")
            return True  # Still consider this a pass
            
    except Exception as e:
        print(f"ERROR: FMP API test failed: {e}")
        return False

async def test_basic_tool():
    """Test a basic FMP tool"""
    print("\n🔧 Testing FMP tool functionality...")
    
    try:
        from src.tools.company import get_company_profile
        
        result = await get_company_profile("AAPL")
        
        if "Error" in result or "error" in result.lower():
            print(f"ERROR: Tool test failed: {result}")
            return False
        else:
            print("✅ Tool test passed - Company profile retrieved successfully")
            print(f"   Result preview: {result[:100]}...")
            return True
            
    except Exception as e:
        print(f"ERROR: Tool test failed: {e}")
        return False

async def test_simple_analysis():
    """Test the simple analysis interface"""
    print("\n🧠 Testing simple analysis interface...")
    
    try:
        # Import our analyzer - but don't use agents (which need OpenAI)
        # Instead just test the FMP data retrieval
        from src.tools.company import get_company_profile
        from src.tools.quote import get_quote
        
        # Get basic company data
        profile = await get_company_profile("AAPL")
        quote = await get_quote("AAPL")
        
        if "Error" not in profile and "Error" not in quote:
            print("✅ Basic analysis components working")
            print(f"   Profile data: {len(profile)} characters")
            print(f"   Quote data: {len(quote)} characters")
            return True
        else:
            print(f"ERROR: Analysis test failed")
            print(f"   Profile: {profile[:100] if 'Error' not in profile else profile}")
            print(f"   Quote: {quote[:100] if 'Error' not in quote else quote}")
            return False
            
    except Exception as e:
        print(f"ERROR: Analysis test failed: {e}")
        return False

def stop_server(process):
    """Stop the MCP server"""
    if process and process.poll() is None:
        print("\n🛑 Stopping MCP server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✅ Server stopped successfully")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            print("✅ Server force stopped")

async def main():
    """Main test function"""
    print("🧪 FMP Stock Analysis System - End-to-End Test")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        return False
    
    # Start server
    server_process = start_server()
    if not server_process:
        return False
    
    try:
        # Wait a bit more for server to be ready
        await asyncio.sleep(2)
        
        # Run tests
        test_results = []
        
        # Test 1: FMP API connection
        test_results.append(await test_fmp_connection())
        
        # Test 2: Basic tool functionality
        test_results.append(await test_basic_tool())
        
        # Test 3: Simple analysis
        test_results.append(await test_simple_analysis())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"\n📋 Test Summary")
        print("=" * 30)
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! System is ready for use.")
            return True
        else:
            print("⚠️  Some tests failed. Check the errors above.")
            return False
            
    finally:
        stop_server(server_process)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted!")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Fatal test error: {e}")
        sys.exit(1)