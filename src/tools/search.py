"""
Search-related tools for the FMP MCP server

This module contains tools related to the Search section of the Financial Modeling Prep API:
https://site.financialmodelingprep.com/developer/docs/stable/search-symbol
https://site.financialmodelingprep.com/developer/docs/stable/search-name

Also includes GPT-compatible search and fetch actions for ChatGPT integration.
"""
from typing import Dict, Any, Optional, List, Union
import json

from src.api.client import fmp_api_request


async def search_by_symbol(query: str, limit: int = 10, exchange: str = None) -> str:
    """
    Search for stocks by ticker symbol
    
    Args:
        query: Symbol to search for (e.g., "AAPL", "MSFT")
        limit: Maximum number of results to return (default: 10)
        exchange: Filter by specific exchange (e.g., "NASDAQ", "NYSE")
        
    Returns:
        List of matching stocks with their details
    """
    # Validate inputs
    if not query:
        return "Error: query parameter is required"
    
    if not 1 <= limit <= 100:
        return "Error: limit must be between 1 and 100"
    
    # Prepare parameters
    params = {"query": query, "limit": limit}
    if exchange:
        params["exchange"] = exchange
    
    # Make API request
    data = await fmp_api_request("search-symbol", params)
    
    if isinstance(data, dict) and "error" in data:
        return f"Error searching for symbol '{query}': {data.get('message', 'Unknown error')}"
    
    if not data or not isinstance(data, list):
        if exchange:
            return f"# Symbol Search Results for '{query}' on {exchange}\nNo matching symbols found"
        else:
            return f"# Symbol Search Results for '{query}'\nNo matching symbols found"
    
    # Format the response
    if exchange:
        result = [f"# Symbol Search Results for '{query}' on {exchange}"]
    else:
        result = [f"# Symbol Search Results for '{query}'"]
    
    if len(data) == 0:
        result.append("No matching symbols found")
        return "\n".join(result)
    
    # Add results to the response
    for item in data:
        symbol = item.get('symbol', 'Unknown')
        name = item.get('name', 'Unknown')
        exchange = item.get('exchange', 'Unknown')
        exchange_full_name = item.get('exchangeFullName', exchange)
        currency = item.get('currency', 'Unknown')
        
        result.append(f"## {symbol} - {name}")
        result.append(f"**Exchange**: {exchange_full_name} ({exchange})")
        result.append(f"**Currency**: {currency}")
        result.append("")
    
    return "\n".join(result)


async def search_by_name(query: str, limit: int = 10, exchange: str = None) -> str:
    """
    Search for stocks by company name
    
    Args:
        query: Company name to search for (e.g., "Apple", "Microsoft")
        limit: Maximum number of results to return (default: 10)
        exchange: Filter by specific exchange (e.g., "NASDAQ", "NYSE")
        
    Returns:
        List of matching companies with their details
    """
    # Validate inputs
    if not query:
        return "Error: query parameter is required"
    
    if not 1 <= limit <= 100:
        return "Error: limit must be between 1 and 100"
    
    # Prepare parameters
    params = {"query": query, "limit": limit}
    if exchange:
        params["exchange"] = exchange
    
    # Make API request
    data = await fmp_api_request("search-name", params)
    
    if isinstance(data, dict) and "error" in data:
        return f"Error searching for company '{query}': {data.get('message', 'Unknown error')}"
    
    if not data or not isinstance(data, list):
        if exchange:
            return f"# Company Name Search Results for '{query}' on {exchange}\nNo matching companies found"
        else:
            return f"# Company Name Search Results for '{query}'\nNo matching companies found"
    
    # Format the response
    if exchange:
        result = [f"# Company Name Search Results for '{query}' on {exchange}"]
    else:
        result = [f"# Company Name Search Results for '{query}'"]
    
    if len(data) == 0:
        result.append("No matching companies found")
        return "\n".join(result)
    
    # Add results to the response
    for item in data:
        symbol = item.get('symbol', 'Unknown')
        name = item.get('name', 'Unknown')
        exchange_name = item.get('exchangeShortName', item.get('exchange', 'Unknown'))
        currency = item.get('currency', 'Unknown')
        stock_type = item.get('stockType', item.get('type', 'Unknown'))
        
        result.append(f"## {name} ({symbol})")
        result.append(f"**Exchange**: {exchange_name}")
        result.append(f"**Currency**: {currency}")
        result.append(f"**Type**: {stock_type}")
        result.append("")
    
    return "\n".join(result)


async def search(query: str) -> Dict[str, Any]:
    """
    GPT-compatible search action for ChatGPT integration.
    Searches for financial instruments (stocks, ETFs, etc.) by symbol or name.
    
    Args:
        query: Search query (symbol or company name)
        
    Returns:
        Dictionary with 'results' key containing list of matching documents.
        Each result includes id, title, and url as required by GPT spec.
    """
    if not query or not query.strip():
        return {"results": []}
    
    try:
        # Try symbol search first
        symbol_data = await fmp_api_request("search-symbol", {"query": query, "limit": 10})
        
        # Try name search as well
        name_data = await fmp_api_request("search-name", {"query": query, "limit": 10})
        
        # Combine and deduplicate results
        all_results = []
        seen_symbols = set()
        
        # Process symbol search results
        if isinstance(symbol_data, list):
            for item in symbol_data:
                symbol = item.get('symbol', '')
                if symbol and symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    all_results.append({
                        "id": f"stock-{symbol}",
                        "title": f"{symbol} - {item.get('name', 'Unknown')}",
                        "url": f"https://financialmodelingprep.com/company/{symbol}"
                    })
        
        # Process name search results
        if isinstance(name_data, list):
            for item in name_data:
                symbol = item.get('symbol', '')
                if symbol and symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    all_results.append({
                        "id": f"stock-{symbol}",
                        "title": f"{item.get('name', 'Unknown')} ({symbol})",
                        "url": f"https://financialmodelingprep.com/company/{symbol}"
                    })
        
        # Limit results to 10
        all_results = all_results[:10]
        
        return {"results": all_results}
        
    except Exception as e:
        # Return empty results on error to match GPT spec
        return {"results": []}


async def fetch(id: str) -> Dict[str, Any]:
    """
    GPT-compatible fetch action for ChatGPT integration.
    Fetches detailed information for a specific resource.
    
    Args:
        id: Resource ID in format "stock-{symbol}"
        
    Returns:
        Dictionary with id, title, text, url, and metadata as required by GPT spec.
    """
    if not id or not id.strip():
        raise ValueError("Document ID is required")
    
    try:
        # Parse resource ID
        if id.startswith("stock-"):
            symbol = id[6:]  # Remove "stock-" prefix
            
            # Get comprehensive stock information
            profile_data = await fmp_api_request("profile", {"symbol": symbol})
            quote_data = await fmp_api_request("quote", {"symbol": symbol})
            
            # Get additional financial data for trading analysis
            try:
                # Get recent price history for technical analysis
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                
                historical_data = await fmp_api_request("historical-price-full", {"symbol": symbol, "from": start_date, "to": end_date})
                
                # Get technical indicators
                rsi_data = await fmp_api_request("rsi", {"symbol": symbol, "period": 14})
                macd_data = await fmp_api_request("macd", {"symbol": symbol})
                bollinger_data = await fmp_api_request("bbands", {"symbol": symbol, "period": 20})
                stochastic_data = await fmp_api_request("stoch", {"symbol": symbol})
                
                # Get analyst ratings and price targets
                ratings_data = await fmp_api_request("rating", {"symbol": symbol})
                
                # Get recent news for sentiment analysis
                news_data = await fmp_api_request("stock_news", {"tickers": symbol, "limit": 5})
                
                # Get financial statements for fundamental analysis
                income_statement = await fmp_api_request("income-statement", {"symbol": symbol, "period": "annual", "limit": 1})
                balance_sheet = await fmp_api_request("balance-sheet-statement", {"symbol": symbol, "period": "annual", "limit": 1})
                cash_flow = await fmp_api_request("cash-flow-statement", {"symbol": symbol, "period": "annual", "limit": 1})
                
                # Get key financial ratios
                ratios_data = await fmp_api_request("ratios", {"symbol": symbol, "period": "annual", "limit": 1})
                
                # Get insider trading data
                insider_trading = await fmp_api_request("insider-trading", {"symbol": symbol, "limit": 5})
                
                # Get institutional ownership
                institutional_holders = await fmp_api_request("institutional-holder", {"symbol": symbol})
                
                # Get short interest data
                short_interest = await fmp_api_request("short-interest", {"symbol": symbol, "limit": 1})
                
            except Exception as e:
                # If additional data fails, continue with basic data
                historical_data = None
                rsi_data = None
                macd_data = None
                bollinger_data = None
                stochastic_data = None
                ratings_data = None
                news_data = None
                income_statement = None
                balance_sheet = None
                cash_flow = None
                ratios_data = None
                insider_trading = None
                institutional_holders = None
                short_interest = None
            
            # Build title and text content
            title = f"Stock Information for {symbol}"
            text_parts = []
            
            # Add profile information
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile = profile_data[0]
                company_name = profile.get('companyName', 'Unknown')
                title = f"{company_name} ({symbol})"
                
                text_parts.append(f"Company: {company_name}")
                text_parts.append(f"Symbol: {symbol}")
                text_parts.append(f"Sector: {profile.get('sector', 'Unknown')}")
                text_parts.append(f"Industry: {profile.get('industry', 'Unknown')}")
                text_parts.append(f"CEO: {profile.get('ceo', 'Unknown')}")
                text_parts.append(f"Website: {profile.get('website', 'N/A')}")
                text_parts.append(f"Employees: {profile.get('fullTimeEmployees', 'N/A')}")
                text_parts.append(f"Market Cap: ${profile.get('mktCap', 0):,}")
                text_parts.append(f"Exchange: {profile.get('exchangeShortName', 'Unknown')}")
                text_parts.append(f"Country: {profile.get('country', 'Unknown')}")
                
                if profile.get('description'):
                    text_parts.append(f"Description: {profile.get('description')}")
            
            # Add quote information
            if isinstance(quote_data, list) and len(quote_data) > 0:
                quote = quote_data[0]
                text_parts.append(f"\\n=== REAL-TIME MARKET DATA ===")
                text_parts.append(f"Current Price: ${quote.get('price', 0)}")
                text_parts.append(f"Change: ${quote.get('change', 0)} ({quote.get('changesPercentage', 0)}%)")
                text_parts.append(f"Day Range: ${quote.get('dayLow', 0)} - ${quote.get('dayHigh', 0)}")
                text_parts.append(f"52-Week Range: ${quote.get('yearLow', 0)} - ${quote.get('yearHigh', 0)}")
                text_parts.append(f"Volume: {quote.get('volume', 0):,}")
                text_parts.append(f"Average Volume: {quote.get('avgVolume', 0):,}")
                text_parts.append(f"P/E Ratio: {quote.get('pe', 'N/A')}")
                text_parts.append(f"EPS: ${quote.get('eps', 0)}")
                text_parts.append(f"Market Cap: ${quote.get('marketCap', 0):,}")
                text_parts.append(f"Beta: {quote.get('beta', 'N/A')}")
                text_parts.append(f"Last Update: {quote.get('timestamp', 'N/A')}")
            
            # Add technical indicators
            if rsi_data and isinstance(rsi_data, list) and len(rsi_data) > 0:
                text_parts.append(f"\\n=== TECHNICAL INDICATORS ===")
                latest_rsi = rsi_data[0]
                text_parts.append(f"RSI (14): {latest_rsi.get('rsi', 'N/A')}")
                if latest_rsi.get('rsi'):
                    rsi_val = float(latest_rsi['rsi'])
                    if rsi_val > 70:
                        text_parts.append("RSI Signal: Overbought (>70)")
                    elif rsi_val < 30:
                        text_parts.append("RSI Signal: Oversold (<30)")
                    else:
                        text_parts.append("RSI Signal: Neutral")
            
            if macd_data and isinstance(macd_data, list) and len(macd_data) > 0:
                latest_macd = macd_data[0]
                text_parts.append(f"MACD: {latest_macd.get('macd', 'N/A')}")
                text_parts.append(f"MACD Signal: {latest_macd.get('signal', 'N/A')}")
                text_parts.append(f"MACD Histogram: {latest_macd.get('histogram', 'N/A')}")
            
            if bollinger_data and isinstance(bollinger_data, list) and len(bollinger_data) > 0:
                latest_bb = bollinger_data[0]
                text_parts.append(f"Bollinger Bands Upper: {latest_bb.get('upperBand', 'N/A')}")
                text_parts.append(f"Bollinger Bands Middle: {latest_bb.get('middleBand', 'N/A')}")
                text_parts.append(f"Bollinger Bands Lower: {latest_bb.get('lowerBand', 'N/A')}")
            
            if stochastic_data and isinstance(stochastic_data, list) and len(stochastic_data) > 0:
                latest_stoch = stochastic_data[0]
                text_parts.append(f"Stochastic %K: {latest_stoch.get('k', 'N/A')}")
                text_parts.append(f"Stochastic %D: {latest_stoch.get('d', 'N/A')}")
            
            # Add analyst ratings
            if ratings_data and isinstance(ratings_data, list) and len(ratings_data) > 0:
                text_parts.append(f"\\n=== ANALYST RATINGS ===")
                latest_rating = ratings_data[0]
                text_parts.append(f"Rating: {latest_rating.get('rating', 'N/A')}")
                text_parts.append(f"Target Price: ${latest_rating.get('targetPrice', 'N/A')}")
                text_parts.append(f"Rating Date: {latest_rating.get('date', 'N/A')}")
            
            # Add recent news for sentiment
            if news_data and isinstance(news_data, list) and len(news_data) > 0:
                text_parts.append(f"\\n=== RECENT NEWS & SENTIMENT ===")
                for i, article in enumerate(news_data[:3]):  # Show top 3 news items
                    text_parts.append(f"News {i+1}: {article.get('title', 'N/A')}")
                    text_parts.append(f"Date: {article.get('publishedDate', 'N/A')}")
                    text_parts.append(f"Source: {article.get('site', 'N/A')}")
                    if article.get('text'):
                        # Truncate long text
                        text = article['text'][:200] + "..." if len(article['text']) > 200 else article['text']
                        text_parts.append(f"Summary: {text}")
                    text_parts.append("")
            
            # Add price action analysis
            if historical_data and isinstance(historical_data, dict) and 'historical' in historical_data:
                text_parts.append(f"\\n=== PRICE ACTION ANALYSIS ===")
                historical = historical_data['historical']
                if len(historical) >= 5:
                    # Get last 5 days of data
                    recent_prices = historical[:5]
                    prices = [float(day['close']) for day in recent_prices]
                    
                    # Calculate price momentum
                    if len(prices) >= 2:
                        price_change = prices[0] - prices[-1]
                        price_change_pct = (price_change / prices[-1]) * 100
                        text_parts.append(f"5-Day Price Change: ${price_change:.2f} ({price_change_pct:.2f}%)")
                        
                        # Determine trend
                        if price_change_pct > 2:
                            text_parts.append("Short-term Trend: Bullish (>2% gain)")
                        elif price_change_pct < -2:
                            text_parts.append("Short-term Trend: Bearish (>2% loss)")
                        else:
                            text_parts.append("Short-term Trend: Sideways")
                    
                    # Add recent daily data
                    text_parts.append("Recent Daily Prices:")
                    for i, day in enumerate(recent_prices[:3]):
                        text_parts.append(f"  {day['date']}: Open ${day['open']}, High ${day['high']}, Low ${day['low']}, Close ${day['close']}")
            
            # Add fundamental analysis
            if income_statement and isinstance(income_statement, list) and len(income_statement) > 0:
                text_parts.append(f"\\n=== FUNDAMENTAL ANALYSIS ===")
                income = income_statement[0]
                text_parts.append(f"Revenue (TTM): ${income.get('revenue', 0):,}")
                text_parts.append(f"Net Income (TTM): ${income.get('netIncome', 0):,}")
                text_parts.append(f"Gross Profit (TTM): ${income.get('grossProfit', 0):,}")
                text_parts.append(f"Operating Income (TTM): ${income.get('operatingIncome', 0):,}")
                text_parts.append(f"EBITDA (TTM): ${income.get('ebitda', 0):,}")
            
            if ratios_data and isinstance(ratios_data, list) and len(ratios_data) > 0:
                ratios = ratios_data[0]
                text_parts.append(f"\\n=== KEY FINANCIAL RATIOS ===")
                text_parts.append(f"Return on Equity (ROE): {ratios.get('returnOnEquity', 'N/A')}")
                text_parts.append(f"Return on Assets (ROA): {ratios.get('returnOnAssets', 'N/A')}")
                text_parts.append(f"Debt-to-Equity: {ratios.get('debtEquityRatio', 'N/A')}")
                text_parts.append(f"Current Ratio: {ratios.get('currentRatio', 'N/A')}")
                text_parts.append(f"Quick Ratio: {ratios.get('quickRatio', 'N/A')}")
                text_parts.append(f"Price-to-Book: {ratios.get('priceToBookRatio', 'N/A')}")
                text_parts.append(f"Price-to-Sales: {ratios.get('priceToSalesRatio', 'N/A')}")
            
            # Add insider trading activity
            if insider_trading and isinstance(insider_trading, list) and len(insider_trading) > 0:
                text_parts.append(f"\\n=== INSIDER TRADING ACTIVITY ===")
                for i, trade in enumerate(insider_trading[:3]):
                    text_parts.append(f"Insider Trade {i+1}:")
                    text_parts.append(f"  Name: {trade.get('filingName', 'N/A')}")
                    text_parts.append(f"  Type: {trade.get('transactionType', 'N/A')}")
                    text_parts.append(f"  Shares: {trade.get('shares', 'N/A')}")
                    text_parts.append(f"  Price: ${trade.get('price', 'N/A')}")
                    text_parts.append(f"  Date: {trade.get('filingDate', 'N/A')}")
                    text_parts.append("")
            
            # Add institutional ownership
            if institutional_holders and isinstance(institutional_holders, list) and len(institutional_holders) > 0:
                text_parts.append(f"\\n=== INSTITUTIONAL OWNERSHIP ===")
                total_shares = sum(float(holder.get('shares', 0)) for holder in institutional_holders)
                for i, holder in enumerate(institutional_holders[:5]):
                    shares = float(holder.get('shares', 0))
                    percentage = (shares / total_shares * 100) if total_shares > 0 else 0
                    text_parts.append(f"{i+1}. {holder.get('holder', 'N/A')}: {shares:,.0f} shares ({percentage:.1f}%)")
            
            # Add short interest data
            if short_interest and isinstance(short_interest, list) and len(short_interest) > 0:
                text_parts.append(f"\\n=== SHORT INTEREST ===")
                short_data = short_interest[0]
                text_parts.append(f"Short Interest: {short_data.get('shortInterest', 'N/A')}")
                text_parts.append(f"Short Interest %: {short_data.get('shortInterestPercent', 'N/A')}")
                text_parts.append(f"Days to Cover: {short_data.get('daysToCover', 'N/A')}")
                text_parts.append(f"Short Interest Date: {short_data.get('date', 'N/A')}")
            
            # Combine all text
            full_text = "\\n".join(text_parts) if text_parts else "No information available"
            
            # Build metadata with comprehensive trading data
            metadata = {}
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile = profile_data[0]
                metadata.update({
                    "sector": profile.get('sector'),
                    "industry": profile.get('industry'),
                    "exchange": profile.get('exchangeShortName'),
                    "currency": profile.get('currency', 'USD'),
                    "country": profile.get('country'),
                    "is_etf": profile.get('isEtf', False),
                    "beta": profile.get('beta'),
                    "market_cap": profile.get('mktCap')
                })
            
            if isinstance(quote_data, list) and len(quote_data) > 0:
                quote = quote_data[0]
                metadata.update({
                    "current_price": quote.get('price'),
                    "price_change": quote.get('change'),
                    "price_change_percent": quote.get('changesPercentage'),
                    "day_high": quote.get('dayHigh'),
                    "day_low": quote.get('dayLow'),
                    "year_high": quote.get('yearHigh'),
                    "year_low": quote.get('yearLow'),
                    "volume": quote.get('volume'),
                    "avg_volume": quote.get('avgVolume'),
                    "pe_ratio": quote.get('pe'),
                    "eps": quote.get('eps'),
                    "market_cap": quote.get('marketCap')
                })
            
            # Add technical indicators to metadata
            if rsi_data and isinstance(rsi_data, list) and len(rsi_data) > 0:
                latest_rsi = rsi_data[0]
                metadata["rsi"] = latest_rsi.get('rsi')
                if latest_rsi.get('rsi'):
                    rsi_val = float(latest_rsi['rsi'])
                    if rsi_val > 70:
                        metadata["rsi_signal"] = "overbought"
                    elif rsi_val < 30:
                        metadata["rsi_signal"] = "oversold"
                    else:
                        metadata["rsi_signal"] = "neutral"
            
            if macd_data and isinstance(macd_data, list) and len(macd_data) > 0:
                latest_macd = macd_data[0]
                metadata.update({
                    "macd": latest_macd.get('macd'),
                    "macd_signal": latest_macd.get('signal'),
                    "macd_histogram": latest_macd.get('histogram')
                })
            
            if bollinger_data and isinstance(bollinger_data, list) and len(bollinger_data) > 0:
                latest_bb = bollinger_data[0]
                metadata.update({
                    "bollinger_upper": latest_bb.get('upperBand'),
                    "bollinger_middle": latest_bb.get('middleBand'),
                    "bollinger_lower": latest_bb.get('lowerBand')
                })
            
            if stochastic_data and isinstance(stochastic_data, list) and len(stochastic_data) > 0:
                latest_stoch = stochastic_data[0]
                metadata.update({
                    "stochastic_k": latest_stoch.get('k'),
                    "stochastic_d": latest_stoch.get('d')
                })
            
            # Add analyst rating to metadata
            if ratings_data and isinstance(ratings_data, list) and len(ratings_data) > 0:
                latest_rating = ratings_data[0]
                metadata.update({
                    "analyst_rating": latest_rating.get('rating'),
                    "target_price": latest_rating.get('targetPrice'),
                    "rating_date": latest_rating.get('date')
                })
            
            # Add price action analysis to metadata
            if historical_data and isinstance(historical_data, dict) and 'historical' in historical_data:
                historical = historical_data['historical']
                if len(historical) >= 5:
                    recent_prices = historical[:5]
                    prices = [float(day['close']) for day in recent_prices]
                    if len(prices) >= 2:
                        price_change = prices[0] - prices[-1]
                        price_change_pct = (price_change / prices[-1]) * 100
                        metadata.update({
                            "five_day_change": price_change,
                            "five_day_change_percent": price_change_pct,
                            "short_term_trend": "bullish" if price_change_pct > 2 else "bearish" if price_change_pct < -2 else "sideways"
                        })
            
            # Add fundamental analysis to metadata
            if income_statement and isinstance(income_statement, list) and len(income_statement) > 0:
                income = income_statement[0]
                metadata.update({
                    "revenue_ttm": income.get('revenue'),
                    "net_income_ttm": income.get('netIncome'),
                    "gross_profit_ttm": income.get('grossProfit'),
                    "operating_income_ttm": income.get('operatingIncome'),
                    "ebitda_ttm": income.get('ebitda')
                })
            
            if ratios_data and isinstance(ratios_data, list) and len(ratios_data) > 0:
                ratios = ratios_data[0]
                metadata.update({
                    "roe": ratios.get('returnOnEquity'),
                    "roa": ratios.get('returnOnAssets'),
                    "debt_to_equity": ratios.get('debtEquityRatio'),
                    "current_ratio": ratios.get('currentRatio'),
                    "quick_ratio": ratios.get('quickRatio'),
                    "price_to_book": ratios.get('priceToBookRatio'),
                    "price_to_sales": ratios.get('priceToSalesRatio')
                })
            
            # Add insider trading to metadata
            if insider_trading and isinstance(insider_trading, list) and len(insider_trading) > 0:
                recent_trades = insider_trading[:3]
                metadata["recent_insider_trades"] = len(recent_trades)
                metadata["latest_insider_trade_date"] = recent_trades[0].get('filingDate') if recent_trades else None
            
            # Add institutional ownership to metadata
            if institutional_holders and isinstance(institutional_holders, list) and len(institutional_holders) > 0:
                total_shares = sum(float(holder.get('shares', 0)) for holder in institutional_holders)
                metadata.update({
                    "institutional_holders_count": len(institutional_holders),
                    "total_institutional_shares": total_shares
                })
            
            # Add short interest to metadata
            if short_interest and isinstance(short_interest, list) and len(short_interest) > 0:
                short_data = short_interest[0]
                metadata.update({
                    "short_interest": short_data.get('shortInterest'),
                    "short_interest_percent": short_data.get('shortInterestPercent'),
                    "days_to_cover": short_data.get('daysToCover')
                })
            
            return {
                "id": id,
                "title": title,
                "text": full_text,
                "url": f"https://financialmodelingprep.com/company/{symbol}",
                "metadata": metadata if metadata else None
            }
        
        else:
            raise ValueError(f"Unknown resource type: {id}")
            
    except Exception as e:
        raise ValueError(f"Fetch failed: {str(e)}")
