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
        
        # Try ETF search for broader coverage
        etf_data = await fmp_api_request("etf-list", {"limit": 10})
        
        # Try crypto search
        crypto_data = await fmp_api_request("crypto", {"limit": 10})
        
        # Try forex search
        forex_data = await fmp_api_request("forex", {"limit": 10})
        
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
        
        # Process ETF search results
        if isinstance(etf_data, list):
            for item in etf_data:
                symbol = item.get('symbol', '')
                if symbol and symbol not in seen_symbols and query.lower() in symbol.lower():
                    seen_symbols.add(symbol)
                    all_results.append({
                        "id": f"etf-{symbol}",
                        "title": f"{item.get('name', 'Unknown')} ({symbol}) - ETF",
                        "url": f"https://financialmodelingprep.com/company/{symbol}"
                    })
        
        # Process crypto search results
        if isinstance(crypto_data, list):
            for item in crypto_data:
                symbol = item.get('symbol', '')
                if symbol and symbol not in seen_symbols and query.lower() in symbol.lower():
                    seen_symbols.add(symbol)
                    all_results.append({
                        "id": f"crypto-{symbol}",
                        "title": f"{item.get('name', 'Unknown')} ({symbol}) - Crypto",
                        "url": f"https://financialmodelingprep.com/company/{symbol}"
                    })
        
        # Process forex search results
        if isinstance(forex_data, list):
            for item in forex_data:
                symbol = item.get('symbol', '')
                if symbol and symbol not in seen_symbols and query.lower() in symbol.lower():
                    seen_symbols.add(symbol)
                    all_results.append({
                        "id": f"forex-{symbol}",
                        "title": f"{item.get('name', 'Unknown')} ({symbol}) - Forex",
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
        # Parse resource ID and determine asset type
        asset_type = "stock"
        symbol = id
        
        if id.startswith("stock-"):
            symbol = id[6:]  # Remove "stock-" prefix
            asset_type = "stock"
        elif id.startswith("etf-"):
            symbol = id[4:]  # Remove "etf-" prefix
            asset_type = "etf"
        elif id.startswith("crypto-"):
            symbol = id[7:]  # Remove "crypto-" prefix
            asset_type = "crypto"
        elif id.startswith("forex-"):
            symbol = id[6:]  # Remove "forex-" prefix
            asset_type = "forex"
        
        # Get comprehensive information based on asset type
        if asset_type == "stock":
            profile_data = await fmp_api_request("profile", {"symbol": symbol})
            quote_data = await fmp_api_request("quote", {"symbol": symbol})
        elif asset_type == "etf":
            profile_data = await fmp_api_request("etf-profile", {"symbol": symbol})
            quote_data = await fmp_api_request("etf-quote", {"symbol": symbol})
        elif asset_type == "crypto":
            profile_data = await fmp_api_request("crypto-profile", {"symbol": symbol})
            quote_data = await fmp_api_request("crypto-quote", {"symbol": symbol})
        elif asset_type == "forex":
            profile_data = await fmp_api_request("forex-profile", {"symbol": symbol})
            quote_data = await fmp_api_request("forex-quote", {"symbol": symbol})
        
        # Get additional financial data for trading analysis
        try:
            # Get real-time intraday data (last 5 days for short-term analysis)
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                
                # Get recent price history for technical analysis
                historical_data = await fmp_api_request("historical-price-full", {"symbol": symbol, "from": start_date, "to": end_date})
                
                # Get real-time intraday data (1-minute intervals for last 2 days)
                intraday_data = await fmp_api_request("historical-chart/1min", {"symbol": symbol, "from": start_date, "to": end_date})
                
                # Get aftermarket trading data
                aftermarket_data = await fmp_api_request("after-market-quote", {"symbol": symbol})
                
                # Get real-time technical indicators
                rsi_data = await fmp_api_request("rsi", {"symbol": symbol, "period": 14})
                macd_data = await fmp_api_request("macd", {"symbol": symbol})
                bollinger_data = await fmp_api_request("bbands", {"symbol": symbol, "period": 20})
                stochastic_data = await fmp_api_request("stoch", {"symbol": symbol})
                
                # Get real-time analyst ratings and price targets
                ratings_data = await fmp_api_request("rating", {"symbol": symbol})
                
                # Get real-time news for sentiment analysis
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
                
                # Get real-time market sentiment indicators
                market_sentiment = await fmp_api_request("market-sentiment", {"symbol": symbol})
                
                # Get real-time earnings calendar
                earnings_calendar = await fmp_api_request("earning_calendar", {"symbol": symbol, "from": start_date, "to": end_date})
                
                # Get additional analyst data
                ratings_snapshot = await fmp_api_request("ratings-snapshot", {"symbol": symbol})
                financial_estimates = await fmp_api_request("financial-estimates", {"symbol": symbol, "period": "annual", "limit": 1})
                price_target_news = await fmp_api_request("price-target-latest-news", {"symbol": symbol, "limit": 3})
                
                # Get additional technical indicators
                ema_data = await fmp_api_request("ema", {"symbol": symbol, "periodLength": 20, "timeframe": "1day"})
                
                # Get company-specific data
                company_notes = await fmp_api_request("company-notes", {"symbol": symbol})
                
                # Get dividend information
                dividends = await fmp_api_request("dividends", {"symbol": symbol, "limit": 5})
                
                # Get market context data
                biggest_gainers = await fmp_api_request("biggest-gainers", {"limit": 5})
                biggest_losers = await fmp_api_request("biggest-losers", {"limit": 5})
                most_active = await fmp_api_request("most-active", {"limit": 5})
                
                # Get market hours status
                market_hours = await fmp_api_request("market-hours", {"exchange": "NASDAQ"})
                
            except Exception as e:
                # If additional data fails, continue with basic data
                historical_data = None
                intraday_data = None
                aftermarket_data = None
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
                market_sentiment = None
                earnings_calendar = None
                ratings_snapshot = None
                financial_estimates = None
                price_target_news = None
                ema_data = None
                company_notes = None
                dividends = None
                biggest_gainers = None
                biggest_losers = None
                most_active = None
                market_hours = None
            
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
            
            # Add aftermarket data
            if aftermarket_data and isinstance(aftermarket_data, list) and len(aftermarket_data) > 0:
                text_parts.append(f"\\n=== AFTERMARKET TRADING ===")
                aftermarket = aftermarket_data[0]
                text_parts.append(f"Aftermarket Price: ${aftermarket.get('price', 'N/A')}")
                text_parts.append(f"Aftermarket Change: ${aftermarket.get('change', 'N/A')} ({aftermarket.get('changesPercentage', 'N/A')}%)")
                text_parts.append(f"Aftermarket Volume: {aftermarket.get('volume', 'N/A')}")
                text_parts.append(f"Aftermarket Timestamp: {aftermarket.get('timestamp', 'N/A')}")
            
            # Add intraday data analysis
            if intraday_data and isinstance(intraday_data, list) and len(intraday_data) > 0:
                text_parts.append(f"\\n=== INTRADAY PRICE ACTION ===")
                # Get last few intraday data points
                recent_intraday = intraday_data[:5]
                text_parts.append("Recent Intraday Prices (1-min intervals):")
                for i, minute_data in enumerate(recent_intraday):
                    text_parts.append(f"  {minute_data.get('date', 'N/A')}: ${minute_data.get('close', 'N/A')} (Vol: {minute_data.get('volume', 'N/A')})")
                
                # Calculate intraday volatility
                if len(intraday_data) >= 2:
                    prices = [float(day['close']) for day in intraday_data[:10] if day.get('close')]
                    if len(prices) >= 2:
                        high = max(prices)
                        low = min(prices)
                        volatility = ((high - low) / low) * 100
                        text_parts.append(f"Intraday Volatility: {volatility:.2f}%")
            
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
            
            # Add market sentiment data
            if market_sentiment and isinstance(market_sentiment, list) and len(market_sentiment) > 0:
                text_parts.append(f"\\n=== MARKET SENTIMENT ===")
                sentiment = market_sentiment[0]
                text_parts.append(f"Sentiment Score: {sentiment.get('sentiment', 'N/A')}")
                text_parts.append(f"Sentiment Label: {sentiment.get('sentimentLabel', 'N/A')}")
                text_parts.append(f"Sentiment Date: {sentiment.get('date', 'N/A')}")
            
            # Add earnings calendar
            if earnings_calendar and isinstance(earnings_calendar, list) and len(earnings_calendar) > 0:
                text_parts.append(f"\\n=== UPCOMING EARNINGS ===")
                for i, earnings in enumerate(earnings_calendar[:3]):
                    text_parts.append(f"Earnings {i+1}:")
                    text_parts.append(f"  Date: {earnings.get('date', 'N/A')}")
                    text_parts.append(f"  EPS Estimate: ${earnings.get('epsEstimate', 'N/A')}")
                    text_parts.append(f"  Revenue Estimate: ${earnings.get('revenueEstimate', 'N/A')}")
                    text_parts.append("")
            
            # Add comprehensive analyst data
            if ratings_snapshot and isinstance(ratings_snapshot, list) and len(ratings_snapshot) > 0:
                text_parts.append(f"\\n=== COMPREHENSIVE ANALYST RATINGS ===")
                snapshot = ratings_snapshot[0]
                text_parts.append(f"Overall Score: {snapshot.get('overallScore', 'N/A')}/5")
                text_parts.append(f"Rating: {snapshot.get('rating', 'N/A')}")
                text_parts.append(f"Analyst Count: {snapshot.get('analystCount', 'N/A')}")
                text_parts.append(f"Target Price: ${snapshot.get('targetPrice', 'N/A')}")
                text_parts.append(f"Rating Date: {snapshot.get('date', 'N/A')}")
            
            if financial_estimates and isinstance(financial_estimates, list) and len(financial_estimates) > 0:
                text_parts.append(f"\\n=== FINANCIAL ESTIMATES ===")
                estimates = financial_estimates[0]
                text_parts.append(f"Revenue Estimate: ${estimates.get('revenueEstimate', 'N/A')}")
                text_parts.append(f"EPS Estimate: ${estimates.get('epsEstimate', 'N/A')}")
                text_parts.append(f"Estimate Date: {estimates.get('date', 'N/A')}")
            
            if price_target_news and isinstance(price_target_news, list) and len(price_target_news) > 0:
                text_parts.append(f"\\n=== PRICE TARGET UPDATES ===")
                for i, target in enumerate(price_target_news[:3]):
                    text_parts.append(f"Target Update {i+1}:")
                    text_parts.append(f"  Target Price: ${target.get('targetPrice', 'N/A')}")
                    text_parts.append(f"  Analyst: {target.get('analyst', 'N/A')}")
                    text_parts.append(f"  Date: {target.get('date', 'N/A')}")
                    text_parts.append("")
            
            # Add EMA technical indicator
            if ema_data and isinstance(ema_data, list) and len(ema_data) > 0:
                text_parts.append(f"\\n=== EXPONENTIAL MOVING AVERAGE ===")
                latest_ema = ema_data[0]
                text_parts.append(f"EMA (20): {latest_ema.get('ema', 'N/A')}")
                text_parts.append(f"Price vs EMA: {latest_ema.get('price', 'N/A')}")
                text_parts.append(f"EMA Date: {latest_ema.get('date', 'N/A')}")
            
            # Add company notes
            if company_notes and isinstance(company_notes, list) and len(company_notes) > 0:
                text_parts.append(f"\\n=== COMPANY NOTES ===")
                for i, note in enumerate(company_notes[:3]):
                    text_parts.append(f"Note {i+1}: {note.get('title', 'N/A')}")
                    text_parts.append(f"Date: {note.get('date', 'N/A')}")
                    if note.get('content'):
                        content = note['content'][:200] + "..." if len(note['content']) > 200 else note['content']
                        text_parts.append(f"Content: {content}")
                    text_parts.append("")
            
            # Add dividend information
            if dividends and isinstance(dividends, list) and len(dividends) > 0:
                text_parts.append(f"\\n=== DIVIDEND INFORMATION ===")
                for i, dividend in enumerate(dividends[:3]):
                    text_parts.append(f"Dividend {i+1}:")
                    text_parts.append(f"  Amount: ${dividend.get('dividend', 'N/A')}")
                    text_parts.append(f"  Ex-Date: {dividend.get('exDate', 'N/A')}")
                    text_parts.append(f"  Record Date: {dividend.get('recordDate', 'N/A')}")
                    text_parts.append(f"  Payment Date: {dividend.get('paymentDate', 'N/A')}")
                    text_parts.append("")
            
            # Add market context
            if biggest_gainers and isinstance(biggest_gainers, list) and len(biggest_gainers) > 0:
                text_parts.append(f"\\n=== MARKET CONTEXT ===")
                text_parts.append("Top Market Gainers:")
                for i, gainer in enumerate(biggest_gainers[:3]):
                    text_parts.append(f"  {i+1}. {gainer.get('symbol', 'N/A')}: {gainer.get('changesPercentage', 'N/A')}%")
                
            if biggest_losers and isinstance(biggest_losers, list) and len(biggest_losers) > 0:
                text_parts.append("Top Market Losers:")
                for i, loser in enumerate(biggest_losers[:3]):
                    text_parts.append(f"  {i+1}. {loser.get('symbol', 'N/A')}: {loser.get('changesPercentage', 'N/A')}%")
                
            if most_active and isinstance(most_active, list) and len(most_active) > 0:
                text_parts.append("Most Active Stocks:")
                for i, active in enumerate(most_active[:3]):
                    text_parts.append(f"  {i+1}. {active.get('symbol', 'N/A')}: Vol {active.get('volume', 'N/A')}")
            
            # Add market hours status
            if market_hours and isinstance(market_hours, dict):
                text_parts.append(f"\\n=== MARKET STATUS ===")
                text_parts.append(f"Market Status: {market_hours.get('status', 'N/A')}")
                text_parts.append(f"Market Hours: {market_hours.get('hours', 'N/A')}")
                text_parts.append(f"Current Time: {market_hours.get('currentTime', 'N/A')}")
            
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
            
            # Add aftermarket data to metadata
            if aftermarket_data and isinstance(aftermarket_data, list) and len(aftermarket_data) > 0:
                aftermarket = aftermarket_data[0]
                metadata.update({
                    "aftermarket_price": aftermarket.get('price'),
                    "aftermarket_change": aftermarket.get('change'),
                    "aftermarket_change_percent": aftermarket.get('changesPercentage'),
                    "aftermarket_volume": aftermarket.get('volume'),
                    "aftermarket_timestamp": aftermarket.get('timestamp')
                })
            
            # Add intraday data to metadata
            if intraday_data and isinstance(intraday_data, list) and len(intraday_data) > 0:
                # Calculate intraday volatility
                prices = [float(day['close']) for day in intraday_data[:10] if day.get('close')]
                if len(prices) >= 2:
                    high = max(prices)
                    low = min(prices)
                    volatility = ((high - low) / low) * 100
                    metadata.update({
                        "intraday_volatility": volatility,
                        "intraday_high": high,
                        "intraday_low": low,
                        "intraday_data_points": len(intraday_data)
                    })
            
            # Add market sentiment to metadata
            if market_sentiment and isinstance(market_sentiment, list) and len(market_sentiment) > 0:
                sentiment = market_sentiment[0]
                metadata.update({
                    "market_sentiment_score": sentiment.get('sentiment'),
                    "market_sentiment_label": sentiment.get('sentimentLabel'),
                    "sentiment_date": sentiment.get('date')
                })
            
            # Add earnings calendar to metadata
            if earnings_calendar and isinstance(earnings_calendar, list) and len(earnings_calendar) > 0:
                next_earnings = earnings_calendar[0] if earnings_calendar else None
                if next_earnings:
                    metadata.update({
                        "next_earnings_date": next_earnings.get('date'),
                        "next_earnings_eps_estimate": next_earnings.get('epsEstimate'),
                        "next_earnings_revenue_estimate": next_earnings.get('revenueEstimate')
                    })
            
            # Add comprehensive analyst data to metadata
            if ratings_snapshot and isinstance(ratings_snapshot, list) and len(ratings_snapshot) > 0:
                snapshot = ratings_snapshot[0]
                metadata.update({
                    "analyst_overall_score": snapshot.get('overallScore'),
                    "analyst_rating": snapshot.get('rating'),
                    "analyst_count": snapshot.get('analystCount'),
                    "analyst_target_price": snapshot.get('targetPrice'),
                    "analyst_rating_date": snapshot.get('date')
                })
            
            if financial_estimates and isinstance(financial_estimates, list) and len(financial_estimates) > 0:
                estimates = financial_estimates[0]
                metadata.update({
                    "revenue_estimate": estimates.get('revenueEstimate'),
                    "eps_estimate": estimates.get('epsEstimate'),
                    "estimate_date": estimates.get('date')
                })
            
            # Add EMA to metadata
            if ema_data and isinstance(ema_data, list) and len(ema_data) > 0:
                latest_ema = ema_data[0]
                metadata.update({
                    "ema_20": latest_ema.get('ema'),
                    "ema_date": latest_ema.get('date')
                })
            
            # Add dividend data to metadata
            if dividends and isinstance(dividends, list) and len(dividends) > 0:
                latest_dividend = dividends[0]
                metadata.update({
                    "latest_dividend": latest_dividend.get('dividend'),
                    "dividend_ex_date": latest_dividend.get('exDate'),
                    "dividend_payment_date": latest_dividend.get('paymentDate')
                })
            
            # Add market context to metadata
            if biggest_gainers and isinstance(biggest_gainers, list) and len(biggest_gainers) > 0:
                top_gainer = biggest_gainers[0]
                metadata.update({
                    "top_gainer_symbol": top_gainer.get('symbol'),
                    "top_gainer_percentage": top_gainer.get('changesPercentage')
                })
            
            if biggest_losers and isinstance(biggest_losers, list) and len(biggest_losers) > 0:
                top_loser = biggest_losers[0]
                metadata.update({
                    "top_loser_symbol": top_loser.get('symbol'),
                    "top_loser_percentage": top_loser.get('changesPercentage')
                })
            
            if most_active and isinstance(most_active, list) and len(most_active) > 0:
                most_active_stock = most_active[0]
                metadata.update({
                    "most_active_symbol": most_active_stock.get('symbol'),
                    "most_active_volume": most_active_stock.get('volume')
                })
            
            # Add market hours to metadata
            if market_hours and isinstance(market_hours, dict):
                metadata.update({
                    "market_status": market_hours.get('status'),
                    "market_hours": market_hours.get('hours'),
                    "market_current_time": market_hours.get('currentTime')
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