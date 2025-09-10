"""
Stock Analyzer - Simple API for Stock Analysis

A simplified, programmatic interface for stock analysis using FMP data and GPT.
Perfect for integrating into other applications where you need clean prompt-to-result functionality.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

class StockAnalyzer:
    """
    Simple Stock Analyzer - Direct prompt to analysis result
    
    This class provides a clean interface where you input a prompt
    and get back a comprehensive analysis result.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/sse"):
        self.server_url = server_url
        self._agent = None
        self._server = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the analyzer (call once before using)"""
        if self._initialized:
            return
            
        self._server = MCPServerSse(
            name="FMP Financial Analysis Server",
            params={"url": self.server_url}
        )
        await self._server.__aenter__()
        
        # Create expert financial analysis agent
        self._agent = Agent(
            name="Expert Financial Analyst",
            instructions="""You are a senior financial analyst and investment advisor. 
            
            Your expertise includes:
            - Comprehensive fundamental analysis using financial statements
            - Technical analysis and market trend identification
            - Valuation methodologies and ratio analysis
            - Risk assessment and portfolio management
            - Investment recommendations with clear reasoning
            
            When analyzing stocks or markets:
            1. Use all available FMP tools to gather comprehensive data
            2. Provide objective, data-driven analysis
            3. Structure responses clearly with headers and bullet points
            4. Include specific numbers, ratios, and metrics in your analysis
            5. Give clear investment recommendations with reasoning
            6. Identify key risks and opportunities
            
            Always be thorough but concise, focusing on actionable insights.""",
            mcp_servers=[self._server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        
        self._initialized = True
    
    async def analyze(self, prompt: str, enable_trace: bool = False) -> str:
        """
        Analyze based on any prompt - the core function for your clients
        
        Args:
            prompt: Analysis request (e.g., "Analyze Apple stock", "Compare AAPL vs MSFT")
            enable_trace: Whether to enable OpenAI tracing for debugging
            
        Returns:
            Comprehensive analysis result as formatted string
            
        Examples:
            analyzer = StockAnalyzer()
            await analyzer.initialize()
            
            # Simple analysis
            result = await analyzer.analyze("Analyze AAPL stock performance and give investment recommendation")
            
            # Comparison
            result = await analyzer.analyze("Compare AAPL, MSFT, and GOOGL for long-term investment")
            
            # Market analysis  
            result = await analyzer.analyze("What are the top performing stocks today and why?")
            
            # Custom analysis
            result = await analyzer.analyze("Is Tesla a good buy right now considering EV market competition?")
        """
        if not self._initialized:
            await self.initialize()
        
        trace_id = gen_trace_id() if enable_trace else None
        
        try:
            if enable_trace and trace_id:
                with trace(workflow_name="Stock Analysis", trace_id=trace_id):
                    print(f"📊 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                    result = await Runner.run(
                        starting_agent=self._agent,
                        input=prompt
                    )
            else:
                result = await Runner.run(
                    starting_agent=self._agent,
                    input=prompt
                )
            
            return result.final_output
            
        except Exception as e:
            return f"ERROR: Analysis failed: {str(e)}\n\nPlease ensure:\n1. MCP server is running on {self.server_url}\n2. FMP and OpenAI API keys are configured\n3. Internet connection is available"
    
    async def cleanup(self):
        """Clean up resources"""
        if self._server:
            await self._server.__aexit__(None, None, None)
        self._initialized = False


# Convenience functions for direct usage
async def quick_analysis(prompt: str, enable_trace: bool = False) -> str:
    """
    Quick one-shot analysis - handles initialization and cleanup automatically
    
    Args:
        prompt: Analysis request
        enable_trace: Enable OpenAI tracing
        
    Returns:
        Analysis result
    """
    analyzer = StockAnalyzer()
    try:
        await analyzer.initialize()
        result = await analyzer.analyze(prompt, enable_trace)
        return result
    finally:
        await analyzer.cleanup()


async def analyze_stock(symbol: str, analysis_type: str = "comprehensive") -> str:
    """
    Convenience function for single stock analysis
    
    Args:
        symbol: Stock ticker symbol
        analysis_type: Type of analysis
        
    Returns:
        Analysis result
    """
    analysis_prompts = {
        "comprehensive": f"Provide comprehensive investment analysis of {symbol} including company profile, financial analysis, valuation, analyst ratings, and clear buy/sell/hold recommendation with detailed reasoning.",
        "fundamental": f"Perform fundamental analysis of {symbol} focusing on financial statements, key metrics, ratios, and intrinsic value assessment.",
        "technical": f"Conduct technical analysis of {symbol} including price trends, momentum indicators, chart patterns, and trading signals.",
        "quick": f"Give a quick investment snapshot of {symbol} - current situation, key metrics, and brief recommendation in 2-3 paragraphs."
    }
    
    prompt = analysis_prompts.get(analysis_type, analysis_prompts["comprehensive"])
    return await quick_analysis(prompt)


async def analyze_trading_alert(ticker: str, alert_text: str, timeframe: str = "1D") -> str:
    """
    Convenience function for trading alert analysis
    
    Args:
        ticker: Stock ticker symbol
        alert_text: Description of the trading alert
        timeframe: Analysis timeframe
        
    Returns:
        Trade/Monitor/Ignore decision with reasoning
    """
    prompt = f"""
    TRADING ALERT ANALYSIS - {ticker.upper()}
    
    Alert: {alert_text}
    Timeframe: {timeframe}
    
    Please analyze this trading alert and provide a decision. You must:
    
    1. Use FMP tools to get current market data for {ticker}:
       - Current price and volume
       - Recent price performance  
       - Technical indicators if available
       - Market context
    
    2. Compare alert claims with actual market data
    
    3. Start your response with exactly one word: Trade, Monitor, or Ignore
    
    4. Follow with 2-3 sentences explaining your reasoning based on the data
    
    DECISION CRITERIA:
    - Trade: Strong setup with volume confirmation and good risk/reward
    - Monitor: Setup developing but needs confirmation or better entry
    - Ignore: Alert contradicts market data or poor risk/reward
    
    Begin analysis now.
    """
    
    return await quick_analysis(prompt)


async def compare_stocks(symbols: List[str], focus: str = "investment") -> str:
    """
    Convenience function for stock comparison
    
    Args:
        symbols: List of stock ticker symbols
        focus: Focus area for comparison
        
    Returns:
        Comparison analysis
    """
    symbols_str = ", ".join(symbols)
    
    if focus == "investment":
        prompt = f"Compare {symbols_str} as investment opportunities. Analyze valuation, growth prospects, financial strength, and competitive position. Rank them for long-term investment and explain reasoning."
    elif focus == "valuation":
        prompt = f"Compare valuation metrics of {symbols_str}. Focus on P/E, P/B, EV/EBITDA, PEG ratios and determine which offers best value."
    elif focus == "growth":
        prompt = f"Compare growth prospects of {symbols_str}. Analyze revenue growth, earnings growth, market expansion opportunities, and future potential."
    else:
        prompt = f"Compare {symbols_str} focusing on {focus}. Provide detailed side-by-side analysis with clear conclusions."
    
    return await quick_analysis(prompt)


# Example usage and testing functions
async def demo():
    """Demo function showing various analysis capabilities"""
    
    print("🚀 Stock Analyzer Demo")
    print("=" * 50)
    
    # Test various analysis scenarios
    test_cases = [
        {
            "name": "Single Stock Analysis",
            "prompt": "Analyze Apple (AAPL) stock and provide investment recommendation based on current financial performance, market position, and growth prospects."
        },
        {
            "name": "Stock Comparison",
            "prompt": "Compare Apple (AAPL), Microsoft (MSFT), and Google (GOOGL) as technology investments. Which is the best choice for a long-term investor?"
        },
        {
            "name": "Market Analysis",
            "prompt": "What are the biggest gainers in the stock market today? Analyze the top 3 performers and explain what's driving their growth."
        },
        {
            "name": "Custom Analysis",
            "prompt": "Is Tesla (TSLA) a good investment right now considering the EV market competition and recent financial performance?"
        }
    ]
    
    analyzer = StockAnalyzer()
    await analyzer.initialize()
    
    try:
        for test_case in test_cases:
            print(f"\n📊 {test_case['name']}")
            print("-" * 30)
            print(f"Prompt: {test_case['prompt']}")
            print("\n🔍 Analyzing...")
            
            result = await analyzer.analyze(test_case['prompt'], enable_trace=True)
            
            print(f"\n📋 Result:")
            print("=" * 80)
            print(result)
            print("=" * 80)
            
            # Wait a bit between requests
            await asyncio.sleep(2)
            
    finally:
        await analyzer.cleanup()


async def test_simple_usage():
    """Test the convenience functions"""
    print("🧪 Testing Simple Usage")
    print("=" * 30)
    
    # Test quick analysis
    result1 = await quick_analysis("What is the current price and basic analysis of Apple stock?")
    print("Quick Analysis Result:")
    print(result1[:200] + "..." if len(result1) > 200 else result1)
    
    # Test stock analysis
    result2 = await analyze_stock("AAPL", "quick")
    print("\nStock Analysis Result:")
    print(result2[:200] + "..." if len(result2) > 200 else result2)
    
    # Test comparison
    result3 = await compare_stocks(["AAPL", "MSFT"], "valuation")
    print("\nComparison Result:")
    print(result3[:200] + "..." if len(result3) > 200 else result3)


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    if not os.getenv("FMP_API_KEY"):
        print("❌ Error: FMP_API_KEY not set in environment") 
        sys.exit(1)
    
    print("✅ Environment check passed")
    
    # Run demo
    try:
        # Run simple test first
        print("Running simple usage test...")
        asyncio.run(test_simple_usage())
        
        print("\n\nRunning full demo...")
        asyncio.run(demo())
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")