"""
Analysis Workflows - Predefined analysis templates for common use cases

This module provides specialized analysis workflows that combine multiple FMP tools
to provide comprehensive insights for specific investment scenarios.
"""

from stock_analyzer import StockAnalyzer
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime


class AnalysisWorkflows:
    """
    Specialized analysis workflows for different investment scenarios
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/sse"):
        self.analyzer = StockAnalyzer(server_url)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the analyzer"""
        if not self._initialized:
            await self.analyzer.initialize()
            self._initialized = True
    
    async def value_investing_analysis(self, symbol: str) -> str:
        """
        Warren Buffett style value investing analysis
        
        Focuses on:
        - Business quality and competitive moats
        - Financial strength and stability
        - Valuation metrics (P/E, P/B, debt levels)
        - Management quality and dividend history
        - Long-term growth prospects
        """
        await self.initialize()
        
        prompt = f"""
        Conduct a comprehensive VALUE INVESTING analysis of {symbol} in the style of Warren Buffett.
        
        Please analyze:
        
        1. BUSINESS QUALITY:
           - Get company profile and understand the business model
           - Assess competitive advantages and economic moats
           - Evaluate market position and brand strength
           - Review industry dynamics and competitive landscape
        
        2. FINANCIAL STRENGTH:
           - Analyze balance sheet strength (debt levels, cash position)
           - Review income statement trends (revenue growth, profitability)
           - Examine cash flow generation and consistency
           - Check key financial ratios and metrics
        
        3. VALUATION:
           - Calculate intrinsic value using financial metrics
           - Compare P/E, P/B, and other valuation ratios to historical averages
           - Assess if the stock is trading below fair value
           - Consider margin of safety
        
        4. MANAGEMENT & DIVIDENDS:
           - Review dividend history and sustainability
           - Assess management's capital allocation decisions
           - Look at insider ownership and stock buybacks
        
        5. LONG-TERM PROSPECTS:
           - Evaluate growth runway and market opportunities
           - Consider regulatory and technological risks
           - Assess ESG factors if relevant
        
        Conclude with:
        - Is this a quality business trading at an attractive price?
        - What's the estimated intrinsic value range?
        - What are the key risks to the investment thesis?
        - Clear BUY/HOLD/PASS recommendation with reasoning
        
        Use specific numbers and ratios throughout your analysis.
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def growth_investing_analysis(self, symbol: str) -> str:
        """
        Growth investing analysis focusing on expansion potential
        
        Focuses on:
        - Revenue and earnings growth rates
        - Market opportunity and TAM
        - Innovation and competitive positioning
        - Management execution capability
        - Scalability and unit economics
        """
        await self.initialize()
        
        prompt = f"""
        Conduct a comprehensive GROWTH INVESTING analysis of {symbol}.
        
        Please analyze:
        
        1. GROWTH METRICS:
           - Get financial statements to analyze historical revenue growth
           - Calculate earnings growth rates over multiple periods
           - Compare growth rates to industry averages
           - Examine quarterly growth trends and consistency
        
        2. MARKET OPPORTUNITY:
           - Assess total addressable market (TAM) size
           - Evaluate market penetration and expansion opportunities
           - Review competitive landscape and market share trends
           - Consider geographic expansion potential
        
        3. BUSINESS MODEL & SCALABILITY:
           - Analyze unit economics and scalability
           - Review gross margins and operating leverage
           - Examine customer acquisition costs and lifetime value
           - Assess recurring revenue streams if applicable
        
        4. INNOVATION & COMPETITIVE POSITION:
           - Evaluate R&D spending and innovation pipeline
           - Assess competitive advantages and differentiation
           - Review patent portfolio and technological moats
           - Consider disruption risks and industry changes
        
        5. MANAGEMENT & EXECUTION:
           - Review management's track record of execution
           - Analyze capital allocation and reinvestment strategies
           - Examine insider ownership and alignment
           - Check analyst estimates and guidance trends
        
        6. VALUATION FOR GROWTH:
           - Calculate PEG ratio and growth-adjusted metrics
           - Compare valuation to high-growth peers
           - Assess if current price reflects future growth potential
           - Consider appropriate entry and exit points
        
        Conclude with:
        - Can this company sustain high growth rates?
        - What are the key growth drivers and catalysts?
        - Is the current valuation justified by growth prospects?
        - Clear BUY/HOLD/PASS recommendation with price targets
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def dividend_investing_analysis(self, symbol: str) -> str:
        """
        Dividend investing analysis for income-focused investors
        
        Focuses on:
        - Dividend yield and sustainability
        - Payout ratio and coverage
        - Dividend growth history
        - Financial stability
        - Sector-specific considerations
        """
        await self.initialize()
        
        prompt = f"""
        Conduct a comprehensive DIVIDEND INVESTING analysis of {symbol}.
        
        Please analyze:
        
        1. DIVIDEND FUNDAMENTALS:
           - Get current dividend yield and compare to historical averages
           - Review dividend history and consistency over 5-10 years
           - Calculate dividend growth rates (1Y, 3Y, 5Y, 10Y)
           - Analyze quarterly dividend payments and timing
        
        2. DIVIDEND SUSTAINABILITY:
           - Examine payout ratio (dividends/earnings)
           - Check free cash flow coverage of dividends
           - Analyze debt levels and impact on dividend capacity
           - Review earnings stability and predictability
        
        3. FINANCIAL STRENGTH:
           - Get financial statements to assess balance sheet health
           - Review debt-to-equity ratios and interest coverage
           - Examine cash flow generation and consistency
           - Check key financial metrics for dividend safety
        
        4. BUSINESS MODEL FOR DIVIDENDS:
           - Assess business model's cash generation capability
           - Review capital requirements and maintenance capex
           - Analyze competitive position and market stability
           - Consider cyclicality and economic sensitivity
        
        5. MANAGEMENT & CAPITAL ALLOCATION:
           - Review management's dividend policy and commitment
           - Analyze share buyback programs vs. dividend payments
           - Check insider ownership and alignment with shareholders
           - Examine capital allocation priorities
        
        6. SECTOR & PEER COMPARISON:
           - Compare dividend yield to sector averages
           - Review peer dividend policies and sustainability
           - Assess sector-specific dividend considerations
           - Consider regulatory or industry-specific risks
        
        7. TOTAL RETURN POTENTIAL:
           - Estimate dividend income over different time horizons
           - Consider potential for dividend growth
           - Assess capital appreciation potential
           - Calculate total expected return
        
        Conclude with:
        - Is the dividend safe and sustainable?
        - What's the likelihood of future dividend increases?
        - How does this compare to other dividend opportunities?
        - Clear BUY/HOLD/PASS recommendation for dividend investors
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def risk_assessment_analysis(self, symbol: str) -> str:
        """
        Comprehensive risk assessment for any investment
        
        Analyzes:
        - Financial risks (debt, liquidity, profitability)
        - Business risks (competition, market, operational)
        - External risks (regulatory, economic, technological)
        - Quantitative risk metrics
        """
        await self.initialize()
        
        prompt = f"""
        Conduct a comprehensive RISK ASSESSMENT analysis of {symbol}.
        
        Please analyze all major risk categories:
        
        1. FINANCIAL RISKS:
           - Review debt levels, debt-to-equity ratios, and debt maturity
           - Analyze interest coverage and debt service capability
           - Check liquidity ratios and working capital position
           - Examine profitability trends and margin stability
           - Assess cash flow volatility and consistency
        
        2. BUSINESS & OPERATIONAL RISKS:
           - Evaluate competitive position and market share trends
           - Assess customer concentration and dependency risks
           - Review supplier relationships and supply chain risks
           - Analyze operational leverage and fixed cost structure
           - Consider management risks and key person dependencies
        
        3. INDUSTRY & MARKET RISKS:
           - Assess industry cyclicality and economic sensitivity
           - Review competitive dynamics and threat of disruption
           - Consider regulatory risks and policy changes
           - Evaluate technological disruption potential
           - Analyze market maturity and growth prospects
        
        4. EXTERNAL & MACRO RISKS:
           - Consider interest rate sensitivity
           - Assess foreign exchange exposure if applicable
           - Review commodity price dependencies
           - Evaluate geopolitical and country-specific risks
           - Consider ESG and sustainability risks
        
        5. QUANTITATIVE RISK METRICS:
           - Analyze stock price volatility (beta, standard deviation)
           - Review correlation with market and sector indices
           - Examine drawdown history during market stress
           - Calculate value-at-risk if data available
           - Compare risk-adjusted returns
        
        6. SCENARIO ANALYSIS:
           - Model performance under different economic scenarios
           - Assess impact of industry-specific stress scenarios
           - Consider company-specific worst-case scenarios
           - Evaluate recovery potential from adverse events
        
        7. RISK MITIGATION:
           - Identify management's risk mitigation strategies
           - Review insurance coverage and hedging activities
           - Assess diversification within the business
           - Consider portfolio context and correlation risks
        
        Conclude with:
        - Overall risk rating (Low/Medium/High)
        - Top 3 most significant risks and their probability/impact
        - Risk-adjusted expected return assessment
        - Position sizing recommendations based on risk profile
        - Clear guidance on risk management for this investment
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def sector_rotation_analysis(self, sectors: List[str]) -> str:
        """
        Analyze sector rotation opportunities and trends
        
        Args:
            sectors: List of sectors to analyze (e.g., ['technology', 'healthcare', 'energy'])
        """
        await self.initialize()
        
        sectors_str = ", ".join(sectors)
        
        prompt = f"""
        Conduct a SECTOR ROTATION analysis focusing on these sectors: {sectors_str}.
        
        For each sector, please analyze:
        
        1. CURRENT SECTOR PERFORMANCE:
           - Get market performance data for key sector representatives
           - Review recent price trends and momentum
           - Compare performance to broader market indices
           - Identify leading and lagging stocks within each sector
        
        2. ECONOMIC CYCLE POSITIONING:
           - Assess where we are in the economic cycle
           - Determine which sectors typically outperform at this stage
           - Consider interest rate environment impact on each sector
           - Evaluate inflation effects and commodity dependencies
        
        3. FUNDAMENTAL SECTOR DRIVERS:
           - Analyze sector-specific fundamentals and catalysts
           - Review earnings trends and estimate revisions
           - Consider regulatory changes and policy impacts
           - Assess technological disruption risks/opportunities
        
        4. VALUATION COMPARISONS:
           - Compare sector valuations to historical averages
           - Analyze relative valuations between sectors
           - Identify over/undervalued sectors based on metrics
           - Consider forward-looking valuation multiples
        
        5. TECHNICAL SECTOR ANALYSIS:
           - Review sector ETF price trends and technical indicators
           - Analyze relative strength between sectors
           - Identify breakout patterns or trend reversals
           - Consider sector momentum and money flow
        
        6. ALLOCATION RECOMMENDATIONS:
           - Rank sectors from most attractive to least attractive
           - Suggest optimal sector allocation percentages
           - Identify specific sector ETFs or leading stocks
           - Consider timing for sector rotation trades
        
        Conclude with:
        - Top 2 sectors to overweight and why
        - Top 2 sectors to underweight or avoid and why
        - Specific ETF or stock recommendations for each sector
        - Timeline for potential sector rotation opportunities
        - Risk factors that could disrupt the sector rotation thesis
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def merger_arbitrage_analysis(self, target_symbol: str, acquirer_symbol: str) -> str:
        """
        Analyze merger arbitrage opportunity
        
        Args:
            target_symbol: Symbol of company being acquired
            acquirer_symbol: Symbol of acquiring company
        """
        await self.initialize()
        
        prompt = f"""
        Conduct a MERGER ARBITRAGE analysis for the acquisition of {target_symbol} by {acquirer_symbol}.
        
        Please analyze:
        
        1. DEAL STRUCTURE & TERMS:
           - Get current stock quotes for both companies
           - Analyze the deal structure (cash, stock, mixed)
           - Calculate the deal premium and current spread
           - Review deal timeline and expected closing date
        
        2. ARBITRAGE OPPORTUNITY:
           - Calculate current arbitrage spread and annualized return
           - Assess risk-adjusted return potential
           - Compare to risk-free rate and other arbitrage opportunities
           - Consider transaction costs and holding period
        
        3. DEAL COMPLETION PROBABILITY:
           - Review regulatory approval requirements
           - Assess antitrust concerns and regulatory risks
           - Analyze shareholder approval likelihood
           - Consider financing conditions and market environment
        
        4. COMPANY ANALYSIS:
           - Review financial profiles of both companies
           - Assess strategic rationale for the acquisition
           - Analyze synergy potential and integration risks
           - Consider management teams and cultural fit
        
        5. MARKET CONDITIONS:
           - Evaluate current M&A environment
           - Consider interest rate impact on deal financing
           - Assess broader market volatility effects
           - Review sector-specific consolidation trends
        
        6. DOWNSIDE SCENARIO ANALYSIS:
           - Model outcomes if deal fails
           - Assess target company standalone value
           - Consider alternative bidder possibilities
           - Evaluate breakup fee protections
        
        7. RISK FACTORS:
           - Identify key regulatory risks
           - Assess financing risks for the acquirer
           - Consider material adverse change clauses
           - Evaluate political/regulatory environment risks
        
        Conclude with:
        - Estimated probability of deal completion
        - Expected risk-adjusted return calculation
        - Optimal position sizing for the arbitrage trade
        - Key milestones and dates to monitor
        - Clear ENTER/PASS/EXIT recommendation with reasoning
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def earnings_preview_analysis(self, symbol: str) -> str:
        """
        Pre-earnings analysis to assess earnings surprise potential
        """
        await self.initialize()
        
        prompt = f"""
        Conduct an EARNINGS PREVIEW analysis for {symbol}'s upcoming earnings announcement.
        
        Please analyze:
        
        1. EARNINGS EXPECTATIONS:
           - Get latest analyst estimates for revenue and EPS
           - Review estimate revisions over the past 90 days
           - Compare current estimates to company guidance
           - Analyze consensus estimates vs. whisper numbers
        
        2. HISTORICAL EARNINGS PATTERNS:
           - Review past 8 quarters of earnings surprises
           - Analyze seasonal patterns in the business
           - Check historical post-earnings stock reactions
           - Identify patterns in guidance updates
        
        3. FUNDAMENTAL BUSINESS TRENDS:
           - Get recent financial statements and quarterly trends
           - Analyze key business metrics and drivers
           - Review management commentary from recent quarters
           - Consider industry and competitive dynamics
        
        4. LEADING INDICATORS:
           - Review relevant economic indicators for the sector
           - Analyze supplier/customer earnings for clues
           - Consider commodity prices or other input costs
           - Check any preliminary data or guidance updates
        
        5. OPTIONS MARKET SIGNALS:
           - Analyze implied volatility around earnings date
           - Review unusual options activity or positioning
           - Consider put/call ratios and options skew
           - Assess market expectations embedded in options
        
        6. TECHNICAL SETUP:
           - Review stock price trends leading into earnings
           - Analyze support/resistance levels
           - Consider relative strength vs. sector/market
           - Evaluate pre-earnings positioning by institutions
        
        7. KEY FOCUS AREAS:
           - Identify most important metrics to watch
           - Highlight potential positive/negative surprises
           - Consider guidance implications for future quarters
           - Assess conference call focus areas
        
        Conclude with:
        - Probability of earnings beat/miss/inline
        - Expected stock reaction scenarios
        - Key risk factors and opportunities
        - Recommended pre/post earnings strategy
        - Specific price targets based on earnings scenarios
        """
        
        return await self.analyzer.analyze(prompt, enable_trace=True)
    
    async def cleanup(self):
        """Clean up resources"""
        await self.analyzer.cleanup()
        self._initialized = False


# Convenience functions for direct usage
async def value_analysis(symbol: str) -> str:
    """Quick value investing analysis"""
    workflows = AnalysisWorkflows()
    try:
        return await workflows.value_investing_analysis(symbol)
    finally:
        await workflows.cleanup()


async def growth_analysis(symbol: str) -> str:
    """Quick growth investing analysis"""
    workflows = AnalysisWorkflows()
    try:
        return await workflows.growth_investing_analysis(symbol)
    finally:
        await workflows.cleanup()


async def dividend_analysis(symbol: str) -> str:
    """Quick dividend investing analysis"""
    workflows = AnalysisWorkflows()
    try:
        return await workflows.dividend_investing_analysis(symbol)
    finally:
        await workflows.cleanup()


async def risk_analysis(symbol: str) -> str:
    """Quick risk assessment analysis"""
    workflows = AnalysisWorkflows()
    try:
        return await workflows.risk_assessment_analysis(symbol)
    finally:
        await workflows.cleanup()


# Demo function
async def demo_workflows():
    """Demo the different analysis workflows"""
    print("🔍 Analysis Workflows Demo")
    print("=" * 50)
    
    test_symbol = "AAPL"
    
    workflows = AnalysisWorkflows()
    
    try:
        # Demo different workflow types
        print(f"\n1. 💎 Value Investing Analysis for {test_symbol}")
        print("-" * 40)
        result = await workflows.value_investing_analysis(test_symbol)
        print(result[:300] + "..." if len(result) > 300 else result)
        
        print(f"\n2. 📈 Growth Investing Analysis for {test_symbol}")
        print("-" * 40)
        result = await workflows.growth_investing_analysis(test_symbol)
        print(result[:300] + "..." if len(result) > 300 else result)
        
        print(f"\n3. 💰 Dividend Analysis for {test_symbol}")
        print("-" * 40)
        result = await workflows.dividend_investing_analysis(test_symbol)
        print(result[:300] + "..." if len(result) > 300 else result)
        
        print(f"\n4. ⚠️  Risk Assessment for {test_symbol}")
        print("-" * 40)
        result = await workflows.risk_assessment_analysis(test_symbol)
        print(result[:300] + "..." if len(result) > 300 else result)
        
    finally:
        await workflows.cleanup()


if __name__ == "__main__":
    import os
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("FMP_API_KEY"):
        print("❌ Please set API keys in environment")
        exit(1)
    
    try:
        asyncio.run(demo_workflows())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted!")
    except Exception as e:
        print(f"❌ Demo error: {e}")