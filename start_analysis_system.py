"""
Start Analysis System - Launch MCP server and provide analysis interface

This script handles starting the MCP server and provides different ways to use
the stock analysis system.
"""

import asyncio
import os
import sys
import subprocess
import time
import signal
import shutil
import socket
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# init environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

class AnalysisSystemManager:
    """Manages the MCP server and analysis system"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.server_port = self._find_available_port(8001)
        self.server_url = f"http://localhost:{self.server_port}/sse"
        print(f"🔍 Detected available port: {self.server_port}")
    
    def _find_available_port(self, start_port: int) -> int:
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('0.0.0.0', port))
                    s.listen(1)
                    s.close()
                    return port
            except OSError as e:
                print(f"Port {port} is in use: {e}")
                continue
        raise RuntimeError(f"No available ports found in range {start_port}-{start_port + 9}")
    
    def check_environment(self) -> bool:
        """Check if environment is properly configured"""
        missing_vars = []
        
        if not os.getenv("FMP_API_KEY"):
            missing_vars.append("FMP_API_KEY")
        
        if not os.getenv("OPENAI_API_KEY"):
            missing_vars.append("OPENAI_API_KEY")
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\nPlease check your .env file")
            return False
        
        print("✅ Environment variables configured")
        return True
    
    def start_server(self) -> bool:
        """Start the MCP server in SSE mode"""
        try:
            print(f"🚀 Starting MCP server on port {self.server_port}...")
            
            # Start server process
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "src.server", "--sse", "--port", str(self.server_port)],
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PORT": str(self.server_port)}
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            time.sleep(3)
            
            # Check if server is still running
            if self.server_process.poll() is None:
                print(f"✅ MCP server started successfully on port {self.server_port}")
                print(f"📡 Server URL: {self.server_url}")
                return True
            else:
                # Server failed to start
                stdout, stderr = self.server_process.communicate()
                print("❌ Server failed to start")
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.server_process and self.server_process.poll() is None:
            print("🛑 Stopping MCP server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✅ Server stopped successfully")
            except subprocess.TimeoutExpired:
                print("⚡ Force killing server...")
                self.server_process.kill()
                self.server_process.wait()
                print("✅ Server force stopped")
        
        self.server_process = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_server()


async def run_interactive_client(server_port: int):
    """Run the interactive stock analysis client"""
    from stock_analysis_client import StockAnalysisClient
    
    print("\n🎯 Starting Interactive Stock Analysis Client...")
    print("   (This provides a menu-driven interface)")
    
    # Use the actual server port that was detected
    server_url = f"http://localhost:{server_port}/sse"
    
    async with StockAnalysisClient(server_url=server_url) as client:
        while True:
            print("\n📊 Available Analysis Options:")
            print("1. Single Stock Analysis")
            print("2. Stock Comparison")
            print("3. Market Analysis") 
            print("4. Custom Analysis")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                symbol = input("Enter stock symbol (e.g., AAPL): ").strip().upper()
                analysis_type = input("Analysis type (comprehensive/fundamental/technical/quick) [comprehensive]: ").strip() or "comprehensive"
                
                print(f"\n🔍 Analyzing {symbol}...")
                result = await client.analyze_stock(symbol, analysis_type)
                print("\n" + "="*80)
                print(result)
                print("="*80)
                
            elif choice == "2":
                symbols_input = input("Enter stock symbols separated by commas (e.g., AAPL,MSFT,GOOGL): ").strip()
                symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
                focus = input("Focus area (overall/valuation/growth/profitability) [overall]: ").strip() or "overall"
                
                if len(symbols) >= 2:
                    print(f"\n⚖️ Comparing {', '.join(symbols)}...")
                    result = await client.compare_stocks(symbols, focus)
                    print("\n" + "="*80)
                    print(result)
                    print("="*80)
                else:
                    print("❌ Please provide at least 2 stock symbols")
                    
            elif choice == "3":
                focus = input("Market focus (general/indices/performers/sectors) [general]: ").strip() or "general"
                
                print(f"\n📈 Market Analysis ({focus})...")
                result = await client.market_analysis(focus)
                print("\n" + "="*80)
                print(result)
                print("="*80)
                
            elif choice == "4":
                prompt = input("Enter your custom analysis request: ").strip()
                
                if prompt:
                    print(f"\n🔍 Processing custom request...")
                    result = await client.custom_analysis(prompt)
                    print("\n" + "="*80)
                    print(result)
                    print("="*80)
                else:
                    print("❌ Please provide a valid prompt")
                    
            elif choice == "5":
                print("👋 Thank you for using Stock Analysis Client!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-5.")


async def run_simple_demo():
    """Run simple analysis demos"""
    from stock_analyzer import StockAnalyzer, quick_analysis
    
    print("\n🧪 Running Analysis Demos...")
    
    # Demo 1: Quick single analysis
    print("\n📊 Demo 1: Single Stock Analysis")
    print("-" * 40)
    result = await quick_analysis(
        "Analyze Apple (AAPL) stock. Give me current price, key metrics, and investment recommendation.",
        enable_trace=True
    )
    print(result)
    
    # Demo 2: Stock comparison
    print("\n📊 Demo 2: Stock Comparison")
    print("-" * 40)
    result = await quick_analysis(
        "Compare Apple (AAPL) vs Microsoft (MSFT) as investments. Which is better for long-term growth?",
        enable_trace=True
    )
    print(result)
    
    # Demo 3: Market analysis
    print("\n📊 Demo 3: Market Analysis")
    print("-" * 40)
    result = await quick_analysis(
        "What are the biggest stock market gainers today? Analyze the top 3 and explain why they're rising.",
        enable_trace=True
    )
    print(result)


async def run_trading_alert_demo():
    """Demo trading alert analysis"""
    from stock_analyzer import analyze_trading_alert
    
    print("\n🚨 Trading Alert Analysis Demo...")
    
    # Sample trading alert
    result = await analyze_trading_alert(
        "AAPL", 
        "Apple breaking above key resistance at $195 with strong volume spike", 
        "1D"
    )
    print("Sample Alert Analysis:")
    print(result)


def show_usage_examples():
    """Show how to use the analysis system programmatically"""
    print("\n📚 Usage Examples for Your Applications:")
    print("=" * 50)
    
    example_code = '''
# Example 1: Simple analysis
from stock_analyzer import quick_analysis

result = await quick_analysis("Analyze Tesla stock and give investment recommendation")
print(result)

# Example 2: Using the analyzer class for multiple requests
from stock_analyzer import StockAnalyzer

analyzer = StockAnalyzer()
await analyzer.initialize()

result1 = await analyzer.analyze("Compare AAPL vs GOOGL")
result2 = await analyzer.analyze("What are today's market trends?")
result3 = await analyzer.analyze("Is Netflix a good buy?")

await analyzer.cleanup()

# Example 3: Convenience functions
from stock_analyzer import analyze_stock, compare_stocks

# Single stock analysis
analysis = await analyze_stock("AAPL", "comprehensive")

# Stock comparison  
comparison = await compare_stocks(["AAPL", "MSFT", "GOOGL"], "investment")

# Example 4: Trading alert analysis
from stock_analyzer import analyze_trading_alert

# Trading alert decision
decision = await analyze_trading_alert("TSLA", "Tesla breaking above $250 resistance with volume", "1D")
'''
    
    print(example_code)


async def main():
    """Main function - handles system startup and user choice"""
    print("🚀 FMP Stock Analysis System")
    print("=" * 50)
    
    # Check environment
    with AnalysisSystemManager() as manager:
        if not manager.check_environment():
            return
        
        # Start MCP server
        if not manager.start_server():
            return
        
        try:
            # Show options
            print("\n🎯 Analysis System Ready!")
            print("\nAvailable Options:")
            print("1. Interactive Client (menu-driven interface)")
            print("2. Simple Demo (automated examples)")
            print("3. Trading Alert Demo (Trade/Monitor/Ignore decisions)")  
            print("4. Show Usage Examples (for integration)")
            print("5. Custom Analysis (enter your own prompt)")
            print("6. Trading Alert Analysis (enter custom alert)")
            print("7. Exit")
            
            while True:
                choice = input("\nSelect option (1-7): ").strip()
                
                if choice == "1":
                    await run_interactive_client(manager.server_port)
                    
                elif choice == "2":
                    await run_simple_demo()
                    
                elif choice == "3":
                    await run_trading_alert_demo()
                    
                elif choice == "4":
                    show_usage_examples()
                    
                elif choice == "5":
                    from stock_analyzer import quick_analysis
                    prompt = input("\nEnter your analysis prompt: ").strip()
                    if prompt:
                        print(f"\n🔍 Analyzing: {prompt}")
                        result = await quick_analysis(prompt, enable_trace=True)
                        print("\n" + "="*80)
                        print(result)
                        print("="*80)
                    else:
                        print("❌ Please provide a valid prompt")
                
                elif choice == "6":
                    from stock_analyzer import analyze_trading_alert
                    ticker = input("Enter ticker symbol: ").strip().upper()
                    alert_text = input("Enter alert text: ").strip()
                    timeframe = input("Enter timeframe [1D]: ").strip() or "1D"
                    
                    if ticker and alert_text:
                        print(f"\n🚨 Analyzing trading alert for {ticker}...")
                        result = await analyze_trading_alert(ticker, alert_text, timeframe)
                        print("\n" + "="*80)
                        print(result)
                        print("="*80)
                    else:
                        print("❌ Please provide ticker and alert text")
                        
                elif choice == "7":
                    print("👋 Thank you for using FMP Stock Analysis System!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please select 1-7.")
                    
        except KeyboardInterrupt:
            print("\n\n👋 System interrupted!")
        except Exception as e:
            print(f"\n❌ System error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")