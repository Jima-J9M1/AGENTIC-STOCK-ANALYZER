"""
Simple Prompt Server - Direct prompt to analysis with MCP

Just asks for prompt, analyzes with agent, returns result.
No menus, no options - pure prompt-to-analysis functionality.
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

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

class SimplePromptAnalyzer:
    """Simple prompt-to-analysis server"""
    
    def __init__(self):
        self.server_process = None
        self.server_port = self._find_available_port(8001)
        self.server_url = f"http://localhost:{self.server_port}/sse"
        self.agent = None
        self.server = None
    
    def _find_available_port(self, start_port):
        """Find available port"""
        import socket
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return start_port
    
    async def start_system(self):
        """Start MCP server and initialize agent"""
        print("Starting Financial Analysis System...")
        print(f"Using port: {self.server_port}")
        
        # Start MCP server
        self.server_process = subprocess.Popen(
            [sys.executable, "-m", "src.server", "--sse", "--port", str(self.server_port)],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server
        await asyncio.sleep(3)
        
        # Initialize agent
        self.server = MCPServerSse(
            name="FMP Analysis Server",
            params={"url": self.server_url}
        )
        await self.server.__aenter__()
        
        # Create advanced financial analysis agent
        self.agent = Agent(
            name="Advanced Financial Analysis Expert",
            instructions="""You are an advanced financial analyst and trading expert with deep market expertise.

CRITICAL INSTRUCTION - TRADING ALERT FORMAT:
When analyzing trading alerts, you MUST follow this exact format:
1. Start response with EXACTLY ONE WORD: "Trade", "Monitor", or "Ignore"  
2. Follow immediately with detailed reasoning based on real market data
3. Include specific price levels, volume data, and risk factors

EXAMPLE PERFECT RESPONSE:
"Trade Apple has confirmed breakout above $195.50 with volume 2.1x average at 65M shares. Current price $234.35 shows strong follow-through with analyst support rating B+. Risk below $225 offers good reward potential to $250 target."

TICKER IDENTIFICATION RULES:
- Look for actual ticker symbols in ALL CAPS (AAPL, TSLA, MSFT, etc.)
- If prompt mentions company names, convert to tickers (Apple = AAPL, Tesla = TSLA)
- If no specific ticker found, ask user to clarify
- NEVER analyze made-up tickers like "FRAME", "TICKER", etc.

CAPABILITIES:
- Comprehensive stock analysis using real-time market data
- Trading alert analysis with Trade/Monitor/Ignore decisions  
- Market trend analysis and sector insights
- Investment recommendations with detailed reasoning
- Risk assessment and portfolio guidance
- Technical and fundamental analysis integration

ANALYSIS APPROACH:
1. FIRST identify the specific ticker symbol to analyze
2. Use ALL available FMP tools to gather comprehensive market data for that ticker
3. Provide data-driven analysis with specific metrics and numbers
4. Give clear, actionable insights and recommendations
5. Include risk factors and key levels to watch
6. Structure responses professionally with clear sections

TOOL USAGE PRIORITY (only after ticker is identified):
- get_quote: Current price, volume, market data
- get_company_profile: Business fundamentals
- get_price_change: Performance across timeframes
- get_ratings_snapshot: Analyst consensus
- get_income_statement: Financial health
- get_biggest_gainers/losers: Market context
- get_technical_indicators: Momentum and trends
- get_market_hours: Trading session status
- Use other relevant tools based on prompt context

RESPONSE QUALITY:
- Always identify the specific ticker being analyzed
- Include specific data points and metrics for that ticker
- Provide clear recommendations with reasoning
- Mention key risk factors
- Use professional financial terminology
- Be decisive and actionable

TRADING DECISION CRITERIA:
🟢 TRADE: Strong setup confirmed by data (volume + price action + good risk/reward)
🟡 MONITOR: Setup developing but needs more confirmation or better timing  
🔴 IGNORE: Alert contradicts actual market data or poor risk/reward setup

MANDATORY FORMAT FOR TRADING ALERTS:
- First word: "Trade", "Monitor", or "Ignore" (no punctuation, no introduction)
- Immediately follow with detailed reasoning using current market data
- Include specific numbers: current price, volume, key levels, percentages
- Mention risk factors and potential targets

EXAMPLE HANDLING:
User: "Below are frames for a ticker. Should I trade this alert?"
Response: "Please specify which ticker symbol you'd like me to analyze (e.g., AAPL, TSLA, NVDA, MSFT). Once you provide the ticker, I'll analyze the current market data and give you a Trade/Monitor/Ignore recommendation."
""",
            mcp_servers=[self.server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        
        print("System ready!")
        return True
    
    def _preprocess_prompt(self, prompt):
        """Pre-process prompt to check for missing ticker information"""
        import re
        
        # Look for ticker symbols (3-4 uppercase letters)
        ticker_patterns = re.findall(r'\b[A-Z]{3,4}\b', prompt)
        
        # Filter out common non-ticker words
        non_tickers = {'TRADE', 'MONITOR', 'IGNORE', 'ABOVE', 'BELOW', 'HIGH', 'LOW', 'PRICE', 'VOLUME', 'FRAME', 'FRAMES', 'TICKER', 'ALERT', 'SECURITY'}
        potential_tickers = [t for t in ticker_patterns if t not in non_tickers]
        
        # Check if prompt mentions generic terms without specific ticker
        generic_terms = ['a ticker', 'this ticker', 'the ticker', 'this security', 'the security', 'frames for a ticker']
        has_generic_reference = any(term in prompt.lower() for term in generic_terms)
        
        if has_generic_reference and not potential_tickers:
            return "MISSING_TICKER", prompt  # Return original prompt for context
        
        return "VALID", prompt

    async def analyze_prompt(self, prompt, ticker_context=None):
        """Analyze user prompt with agent"""
        try:
            # If ticker_context is provided, this means we're continuing from a previous request
            if ticker_context:
                # User provided ticker, now analyze with original prompt
                ticker = ticker_context.strip().upper()
                enhanced_prompt = f"{prompt}\n\nTicker to analyze: {ticker}"
                processed_prompt = enhanced_prompt
            else:
                # Pre-process to check for missing information
                status, processed_prompt = self._preprocess_prompt(prompt)
                
                if status == "MISSING_TICKER":
                    return "NEED_TICKER: Please specify which ticker symbol (e.g., AAPL, TSLA, NVDA, MSFT):"
            
            # Generate trace for debugging
            trace_id = gen_trace_id()
            
            with trace(workflow_name="Financial Analysis", trace_id=trace_id):
                print("Analyzing... (This may take 30-60 seconds)")
                print(f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=processed_prompt
                )
                
                return result.final_output
                
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    async def cleanup(self):
        """Clean up resources"""
        if self.server:
            await self.server.__aexit__(None, None, None)
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

async def main():
    """Main server loop - just prompt and analysis"""
    
    # Check environment
    if not os.getenv("FMP_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Missing API keys in .env file")
        return
    
    print("=== Financial Analysis Server ===")
    print("Advanced AI-powered financial analysis with real-time market data")
    print("=" * 60)
    
    analyzer = SimplePromptAnalyzer()
    
    try:
        # Start system
        await analyzer.start_system()
        
        print("\nReady for analysis!")
        print("Enter your prompts below (Ctrl+C to exit):")
        print("-" * 60)
        
        # Main loop - just prompt and analyze
        while True:
            try:
                # Get prompt from user
                prompt = input("\nPrompt: ").strip()
                
                if not prompt:
                    print("Please enter a prompt.")
                    continue
                
                if prompt.lower() in ['exit', 'quit', 'bye']:
                    print("Goodbye!")
                    break
                
                print(f"\nAnalyzing: {prompt}")
                print("=" * 80)
                
                # Analyze with agent
                result = await analyzer.analyze_prompt(prompt)
                
                # Check if we need ticker information
                if result.startswith("NEED_TICKER:"):
                    print(result.replace("NEED_TICKER: ", ""))
                    
                    # Get ticker from user
                    ticker_input = input("Ticker: ").strip()
                    
                    if ticker_input.upper() in ['EXIT', 'QUIT', 'BYE']:
                        print("Goodbye!")
                        break
                    
                    if ticker_input:
                        print(f"\nAnalyzing with ticker: {ticker_input.upper()}")
                        print("=" * 80)
                        
                        # Now analyze with the ticker
                        result = await analyzer.analyze_prompt(prompt, ticker_input)
                        print(result)
                    else:
                        print("No ticker provided, skipping analysis.")
                        continue
                else:
                    # Display result normally
                    print(result)
                
                print("=" * 80)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete!")
    except Exception as e:
        print(f"Fatal error: {e}")