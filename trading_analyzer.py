"""
Trading Alert Analyzer - Specialized agent for trading decision analysis

This module provides intelligent analysis of trading alerts with Trade/Monitor/Ignore decisions
based on real-time market data and technical analysis.
"""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings

class TradingAlertAnalyzer:
    """
    Specialized analyzer for trading alerts that provides Trade/Monitor/Ignore decisions
    based on real-time market data and intelligent tool selection.
    """
    
    def __init__(self, server_url: str = "http://localhost:8001/sse"):
        self.server_url = server_url
        self._agent = None
        self._server = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the trading analyzer"""
        if self._initialized:
            return
            
        self._server = MCPServerSse(
            name="FMP Trading Analysis Server",
            params={"url": self.server_url}
        )
        await self._server.__aenter__()
        
        # Create specialized trading decision agent
        self._agent = Agent(
            name="Trading Decision Expert",
            instructions="""You are a professional day trader and technical analyst with expertise in:
            
            CORE RESPONSIBILITIES:
            - Analyzing trading alerts against real-time market data
            - Making binary trading decisions: Trade, Monitor, or Ignore
            - Using FMP financial tools to gather comprehensive market data
            - Providing data-driven reasoning for all decisions
            
            DECISION FRAMEWORK:
            
            🟢 TRADE: When conditions strongly favor immediate action
            - Strong price momentum with volume confirmation
            - Clear technical breakout with follow-through
            - Alert aligns with broader market trend
            - Risk/reward ratio is favorable (minimum 2:1)
            - Multiple timeframes confirm the setup
            
            🟡 MONITOR: When setup is developing but needs confirmation
            - Price approaching key levels but no breakout yet
            - Volume is building but not confirmed
            - Mixed signals across timeframes
            - Waiting for market open or key level test
            - Alert is early/premature but has potential
            
            🔴 IGNORE: When conditions don't support action
            - Price action contradicts alert
            - Volume is weak or declining
            - Against broader market trend
            - Poor risk/reward ratio
            - Alert appears to be noise/false signal
            
            REQUIRED RESPONSE FORMAT:
            1. Start with EXACTLY one word: "Trade", "Monitor", or "Ignore"
            2. Follow with 2-4 sentences explaining your reasoning
            3. Include specific data points from FMP tools (price, volume, indicators)
            4. Mention key levels or risk factors
            
            TOOL USAGE STRATEGY:
            Always gather comprehensive data using available FMP tools:
            - get_quote: Current price, volume, market cap
            - get_price_change: Recent price performance across timeframes  
            - get_aftermarket_quote: Pre/post market activity if relevant
            - get_company_profile: Business context for fundamental alerts
            - get_biggest_gainers/losers: Market context and sector rotation
            - get_technical_indicators: EMA, momentum indicators
            - get_index_quote: Broader market sentiment
            
            Be decisive, data-driven, and always start with the single decision word.""",
            mcp_servers=[self._server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        
        self._initialized = True
    
    async def analyze_alert(
        self, 
        ticker: str, 
        alert_text: str, 
        timeframe: str = "1D",
        context: Optional[str] = None,
        enable_trace: bool = False
    ) -> str:
        """
        Analyze a trading alert and provide Trade/Monitor/Ignore decision
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, TSLA)
            alert_text: The actual alert text describing the price action
            timeframe: Timeframe for analysis (1D, 1H, 5M, etc.)
            context: Additional context about market conditions
            enable_trace: Enable OpenAI tracing for debugging
            
        Returns:
            Trading decision starting with Trade/Monitor/Ignore followed by reasoning
            
        Example:
            result = await analyzer.analyze_alert(
                ticker="AAPL",
                alert_text="Breaking above key resistance at $195 with strong volume",
                timeframe="1D"
            )
            # Returns: "Trade Apple has broken above key resistance at $195.50 with volume..."
        """
        if not self._initialized:
            await self.initialize()
        
        # Build comprehensive analysis prompt
        prompt = self._build_alert_analysis_prompt(ticker, alert_text, timeframe, context)
        
        trace_id = gen_trace_id() if enable_trace else None
        
        try:
            if enable_trace and trace_id:
                with trace(workflow_name=f"Trading Alert Analysis - {ticker}", trace_id=trace_id):
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
            return f"ERROR: Trading analysis failed for {ticker}: {str(e)}"
    
    def _build_alert_analysis_prompt(
        self, 
        ticker: str, 
        alert_text: str, 
        timeframe: str, 
        context: Optional[str]
    ) -> str:
        """Build comprehensive prompt for alert analysis"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""
TRADING ALERT ANALYSIS REQUEST
==============================

TICKER: {ticker.upper()}
ALERT TEXT: {alert_text}
TIMEFRAME: {timeframe}
ANALYSIS TIME: {current_time}
{f"ADDITIONAL CONTEXT: {context}" if context else ""}

TASK:
Analyze this trading alert for {ticker.upper()} and determine whether to Trade, Monitor, or Ignore.

REQUIRED ANALYSIS PROCESS:
1. Use FMP tools to gather comprehensive current market data for {ticker}:
   - Current price, volume, and market conditions
   - Recent price performance and trends
   - Technical indicators and momentum
   - Market context (indices, sector performance)
   - Pre/post market activity if relevant

2. Compare the alert information with actual market data:
   - Verify claims in the alert text
   - Check if price action supports the alert
   - Assess volume confirmation
   - Evaluate risk/reward potential

3. Make trading decision based on:
   - Strength of price momentum and volume
   - Technical setup quality
   - Market context and timing
   - Risk management considerations

REQUIRED OUTPUT FORMAT:
- First word MUST be: Trade, Monitor, or Ignore
- Follow with 2-4 sentences explaining reasoning
- Include specific data points (current price, volume, key levels)
- Mention primary risk factors or catalysts

EXAMPLE GOOD RESPONSES:
"Trade AAPL broke above $195.50 resistance with 2.3x average volume, confirming the breakout. Current price $196.20 shows strong follow-through with market indices supporting. Risk below $194 offers good reward potential to $200 target."

"Monitor TSLA approaching $250 resistance mentioned in alert, but volume is only 0.8x average. Current price $248.90 needs volume confirmation above $250 for entry. Wait for breakout with volume or rejection for short setup."

"Ignore NVDA alert claims breakout at $140, but current price $138.50 shows no breakout occurred. Volume declining and broader tech sector weak. Alert appears premature or incorrect based on actual market data."

Begin analysis now using all available FMP tools to gather current market data for {ticker}.
        """
        
        return prompt.strip()
    
    async def analyze_multiple_alerts(self, alerts: list) -> Dict[str, str]:
        """
        Analyze multiple trading alerts in batch
        
        Args:
            alerts: List of dicts with keys: ticker, alert_text, timeframe, context
            
        Returns:
            Dict mapping ticker to analysis result
        """
        if not self._initialized:
            await self.initialize()
        
        results = {}
        
        for alert in alerts:
            ticker = alert.get('ticker', 'UNKNOWN')
            try:
                result = await self.analyze_alert(
                    ticker=ticker,
                    alert_text=alert.get('alert_text', ''),
                    timeframe=alert.get('timeframe', '1D'),
                    context=alert.get('context')
                )
                results[ticker] = result
            except Exception as e:
                results[ticker] = f"ERROR: Failed to analyze {ticker}: {str(e)}"
        
        return results
    
    async def cleanup(self):
        """Clean up resources"""
        if self._server:
            await self._server.__aexit__(None, None, None)
        self._initialized = False


# Convenience functions for direct usage
async def analyze_trading_alert(
    ticker: str, 
    alert_text: str, 
    timeframe: str = "1D", 
    context: Optional[str] = None,
    enable_trace: bool = False
) -> str:
    """
    Quick trading alert analysis - handles initialization and cleanup automatically
    
    Args:
        ticker: Stock ticker symbol
        alert_text: Alert description
        timeframe: Analysis timeframe
        context: Additional context
        enable_trace: Enable tracing
        
    Returns:
        Trading decision with reasoning
    """
    analyzer = TradingAlertAnalyzer()
    try:
        await analyzer.initialize()
        result = await analyzer.analyze_alert(ticker, alert_text, timeframe, context, enable_trace)
        return result
    finally:
        await analyzer.cleanup()


async def demo_trading_alerts():
    """Demo various trading alert scenarios"""
    
    print("🚀 Trading Alert Analyzer Demo")
    print("=" * 50)
    
    # Sample alerts to test
    test_alerts = [
        {
            "name": "Breakout Alert",
            "ticker": "AAPL",
            "alert_text": "Apple breaking above key resistance at $195 with strong volume spike",
            "timeframe": "1D"
        },
        {
            "name": "Support Test",
            "ticker": "TSLA", 
            "alert_text": "Tesla testing critical support at $240 level with high volume",
            "timeframe": "4H"
        },
        {
            "name": "Gap Alert",
            "ticker": "NVDA",
            "alert_text": "NVIDIA gapping up 3% pre-market on earnings beat, resistance at $150",
            "timeframe": "1D",
            "context": "Earnings announcement after market close"
        },
        {
            "name": "Momentum Alert",
            "ticker": "MSFT",
            "alert_text": "Microsoft showing momentum divergence, price making new highs but RSI declining",
            "timeframe": "1D"
        }
    ]
    
    analyzer = TradingAlertAnalyzer()
    await analyzer.initialize()
    
    try:
        for alert in test_alerts:
            print(f"\n📊 {alert['name']} - {alert['ticker']}")
            print("-" * 40)
            print(f"Alert: {alert['alert_text']}")
            print(f"Timeframe: {alert['timeframe']}")
            
            print(f"\n🔍 Analyzing {alert['ticker']}...")
            
            result = await analyzer.analyze_alert(
                ticker=alert['ticker'],
                alert_text=alert['alert_text'],
                timeframe=alert['timeframe'],
                context=alert.get('context'),
                enable_trace=True
            )
            
            print(f"\n📋 Decision:")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
            # Brief pause between requests
            await asyncio.sleep(2)
            
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    if not os.getenv("FMP_API_KEY"):
        print("ERROR: FMP_API_KEY not set in environment") 
        sys.exit(1)
    
    print("Environment check passed")
    
    # Run demo
    try:
        print("Running trading alert analysis demo...")
        asyncio.run(demo_trading_alerts())
        
    except KeyboardInterrupt:
        print("\nDemo interrupted!")
    except Exception as e:
        print(f"Demo error: {e}")