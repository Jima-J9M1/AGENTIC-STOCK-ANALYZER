"""
Stock Analysis Client - Custom client for comprehensive stock analysis

This client provides a simplified interface for stock analysis using the FMP MCP server
and GPT integration. Users can input analysis prompts and receive comprehensive results.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

class StockAnalysisClient:
    """
    A comprehensive stock analysis client that provides structured financial analysis
    using FMP data and GPT intelligence.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/sse"):
        """
        Initialize the Stock Analysis Client
        
        Args:
            server_url: URL of the MCP server (default: http://localhost:8000/sse)
        """
        self.server_url = server_url
        self.agent = None
        self.server = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.server = MCPServerSse(
            name="FMP Financial Analysis Server",
            params={"url": self.server_url}
        )
        await self.server.__aenter__()
        
        # Create specialized financial analysis agent
        self.agent = Agent(
            name="Financial Analysis Expert",
            instructions="""You are a professional financial analyst with expertise in:
            - Fundamental analysis using financial statements and key metrics
            - Market analysis and trend identification
            - Investment recommendation generation
            - Risk assessment and valuation
            
            Use the available FMP tools to gather comprehensive data, then provide
            detailed, well-structured analysis with clear reasoning and actionable insights.
            
            Always structure your analysis with:
            1. Executive Summary
            2. Company Overview
            3. Financial Analysis
            4. Market Position
            5. Investment Recommendation
            6. Risk Assessment
            
            Be objective, data-driven, and provide specific reasoning for all conclusions.""",
            mcp_servers=[self.server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.server:
            await self.server.__aexit__(exc_type, exc_val, exc_tb)
    
    async def analyze_stock(self, symbol: str, analysis_type: str = "comprehensive") -> str:
        """
        Perform comprehensive stock analysis
        
        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
            analysis_type: Type of analysis - 'comprehensive', 'fundamental', 'technical', 'quick'
        
        Returns:
            Detailed analysis report as formatted string
        """
        if not self.agent:
            raise RuntimeError("Client not properly initialized. Use 'async with' syntax.")
        
        # Define analysis prompts based on type
        analysis_prompts = {
            "comprehensive": f"""
            Perform a comprehensive investment analysis of {symbol}. Please:
            
            1. Get the company profile to understand the business
            2. Analyze the latest financial statements (income statement, balance sheet)
            3. Review current stock quote and recent price performance
            4. Check analyst ratings and price targets
            5. Assess key financial metrics and ratios
            6. Evaluate market position and competitive landscape
            
            Provide a structured analysis with clear buy/sell/hold recommendation based on:
            - Financial health and performance
            - Valuation metrics
            - Growth prospects
            - Risk factors
            - Market conditions
            
            Include specific data points and reasoning for your conclusions.
            """,
            
            "fundamental": f"""
            Conduct a fundamental analysis of {symbol} focusing on:
            
            1. Company profile and business model
            2. Financial statements analysis (revenue, profitability, debt levels)
            3. Key financial ratios and metrics
            4. Growth trends and financial health
            5. Competitive position
            
            Provide investment recommendation based purely on fundamental factors.
            """,
            
            "technical": f"""
            Perform technical analysis of {symbol} including:
            
            1. Current price and recent performance trends
            2. Technical indicators (EMA, price changes)
            3. Chart analysis and price momentum
            4. Support and resistance levels
            5. Trading volume analysis
            
            Focus on price action and technical signals for trading decisions.
            """,
            
            "quick": f"""
            Provide a quick investment snapshot of {symbol}:
            
            1. Current price and basic company info
            2. Key financial metrics
            3. Analyst consensus
            4. Brief investment thesis
            
            Keep it concise but informative - 1-2 paragraphs maximum.
            """
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["comprehensive"])
        
        # Generate trace ID for debugging
        trace_id = gen_trace_id()
        
        try:
            with trace(workflow_name=f"Stock Analysis - {symbol}", trace_id=trace_id):
                print(f"🔍 Analyzing {symbol.upper()} ({analysis_type} analysis)...")
                print(f"📊 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=prompt
                )
                
                return result.final_output
                
        except Exception as e:
            return f"❌ Analysis failed for {symbol}: {str(e)}"
    
    async def compare_stocks(self, symbols: list, focus_area: str = "overall") -> str:
        """
        Compare multiple stocks side by side
        
        Args:
            symbols: List of stock ticker symbols to compare
            focus_area: Focus area - 'overall', 'valuation', 'growth', 'profitability'
        
        Returns:
            Comparative analysis report
        """
        if not self.agent:
            raise RuntimeError("Client not properly initialized. Use 'async with' syntax.")
        
        symbols_str = ", ".join(symbols)
        
        comparison_prompt = f"""
        Compare these stocks: {symbols_str} with focus on {focus_area} metrics.
        
        For each stock, gather:
        1. Company profile and key business information
        2. Current stock quote and market performance
        3. Key financial metrics and ratios
        4. Financial statements data
        5. Analyst ratings and price targets
        
        Then provide a detailed comparison analyzing:
        - Relative valuation (P/E, P/B, EV/EBITDA ratios)
        - Growth prospects and historical performance
        - Financial strength and stability
        - Market position and competitive advantages
        - Risk factors and investment outlook
        
        Conclude with a ranking of investment attractiveness and specific
        reasons why one might be preferred over others.
        """
        
        trace_id = gen_trace_id()
        
        try:
            with trace(workflow_name=f"Stock Comparison - {symbols_str}", trace_id=trace_id):
                print(f"⚖️  Comparing: {symbols_str}")
                print(f"📊 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=comparison_prompt
                )
                
                return result.final_output
                
        except Exception as e:
            return f"❌ Comparison failed: {str(e)}"
    
    async def market_analysis(self, analysis_focus: str = "general") -> str:
        """
        Perform market analysis
        
        Args:
            analysis_focus: Focus area - 'general', 'indices', 'performers', 'sectors'
        
        Returns:
            Market analysis report
        """
        if not self.agent:
            raise RuntimeError("Client not properly initialized. Use 'async with' syntax.")
        
        market_prompts = {
            "general": """
            Provide a comprehensive market analysis including:
            1. Major market indices performance and trends
            2. Biggest gainers and losers today
            3. Most active stocks and trading volume
            4. Market sentiment and key drivers
            5. Overall market outlook and recommendations
            """,
            
            "indices": """
            Focus on market indices analysis:
            1. Get current quotes for major indices
            2. Analyze recent performance trends
            3. Compare different market segments
            4. Provide market direction insights
            """,
            
            "performers": """
            Analyze market performers today:
            1. Identify biggest gainers and why they're moving
            2. Review biggest losers and potential causes
            3. Examine most active stocks and volume patterns
            4. Find trading opportunities and market themes
            """,
            
            "sectors": """
            Provide sector-based market analysis:
            1. Identify leading and lagging sectors
            2. Analyze sector rotation patterns
            3. Review ETF performance across sectors
            4. Recommend sector allocation strategies
            """
        }
        
        prompt = market_prompts.get(analysis_focus, market_prompts["general"])
        trace_id = gen_trace_id()
        
        try:
            with trace(workflow_name=f"Market Analysis - {analysis_focus}", trace_id=trace_id):
                print(f"📈 Market Analysis ({analysis_focus})...")
                print(f"📊 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=prompt
                )
                
                return result.final_output
                
        except Exception as e:
            return f"❌ Market analysis failed: {str(e)}"
    
    async def custom_analysis(self, prompt: str) -> str:
        """
        Perform custom analysis based on user prompt
        
        Args:
            prompt: Custom analysis request from user
        
        Returns:
            Analysis response
        """
        if not self.agent:
            raise RuntimeError("Client not properly initialized. Use 'async with' syntax.")
        
        trace_id = gen_trace_id()
        
        try:
            with trace(workflow_name="Custom Analysis", trace_id=trace_id):
                print(f"🔍 Custom Analysis: {prompt[:50]}...")
                print(f"📊 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=prompt
                )
                
                return result.final_output
                
        except Exception as e:
            return f"❌ Custom analysis failed: {str(e)}"


async def main():
    """Interactive demo of the Stock Analysis Client"""
    print("🚀 Stock Analysis Client - Interactive Demo")
    print("=" * 50)
    
    async with StockAnalysisClient() as client:
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


if __name__ == "__main__":
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in the .env file")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")