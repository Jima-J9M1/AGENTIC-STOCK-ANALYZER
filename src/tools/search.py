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


async def search(query: str, limit: int = 10) -> str:
    """
    GPT-compatible search action for ChatGPT integration.
    Searches for financial instruments (stocks, ETFs, etc.) by symbol or name.
    
    Args:
        query: Search query (symbol or company name)
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        JSON string containing search results with resource IDs
    """
    if not query:
        return json.dumps({"error": "query parameter is required"})
    
    if not 1 <= limit <= 100:
        return json.dumps({"error": "limit must be between 1 and 100"})
    
    try:
        # Try symbol search first
        symbol_data = await fmp_api_request("search-symbol", {"query": query, "limit": limit})
        
        # Try name search as well
        name_data = await fmp_api_request("search-name", {"query": query, "limit": limit})
        
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
                        "description": f"Stock on {item.get('exchangeFullName', item.get('exchange', 'Unknown'))} exchange",
                        "symbol": symbol,
                        "name": item.get('name', 'Unknown'),
                        "exchange": item.get('exchange', 'Unknown'),
                        "currency": item.get('currency', 'Unknown'),
                        "type": "stock"
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
                        "description": f"Stock on {item.get('exchangeShortName', item.get('exchange', 'Unknown'))} exchange",
                        "symbol": symbol,
                        "name": item.get('name', 'Unknown'),
                        "exchange": item.get('exchangeShortName', item.get('exchange', 'Unknown')),
                        "currency": item.get('currency', 'Unknown'),
                        "type": item.get('stockType', item.get('type', 'stock'))
                    })
        
        # Limit results
        all_results = all_results[:limit]
        
        return json.dumps({
            "results": all_results,
            "query": query,
            "total": len(all_results)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})


async def fetch(resource_id: str) -> str:
    """
    GPT-compatible fetch action for ChatGPT integration.
    Fetches detailed information for a specific resource.
    
    Args:
        resource_id: Resource ID in format "stock-{symbol}" or "market-{type}"
        
    Returns:
        JSON string containing detailed resource information
    """
    if not resource_id:
        return json.dumps({"error": "resource_id parameter is required"})
    
    try:
        # Parse resource ID
        if resource_id.startswith("stock-"):
            symbol = resource_id[6:]  # Remove "stock-" prefix
            
            # Get comprehensive stock information
            profile_data = await fmp_api_request("profile", {"symbol": symbol})
            quote_data = await fmp_api_request("quote", {"symbol": symbol})
            
            result = {
                "id": resource_id,
                "symbol": symbol,
                "type": "stock"
            }
            
            # Add profile information
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile = profile_data[0]
                result.update({
                    "name": profile.get('companyName', 'Unknown'),
                    "description": profile.get('description', ''),
                    "sector": profile.get('sector', 'Unknown'),
                    "industry": profile.get('industry', 'Unknown'),
                    "ceo": profile.get('ceo', 'Unknown'),
                    "website": profile.get('website', ''),
                    "employees": profile.get('fullTimeEmployees', 0),
                    "market_cap": profile.get('mktCap', 0),
                    "exchange": profile.get('exchangeShortName', 'Unknown'),
                    "currency": profile.get('currency', 'USD'),
                    "country": profile.get('country', 'Unknown'),
                    "city": profile.get('city', 'Unknown'),
                    "state": profile.get('state', 'Unknown'),
                    "zip": profile.get('zip', ''),
                    "phone": profile.get('phone', ''),
                    "address": profile.get('address', ''),
                    "image": profile.get('image', ''),
                    "beta": profile.get('beta', 0),
                    "vol_avg": profile.get('volAvg', 0),
                    "last_div": profile.get('lastDiv', 0),
                    "range": profile.get('range', ''),
                    "changes": profile.get('changes', 0),
                    "dcf_diff": profile.get('dcfDiff', 0),
                    "dcf": profile.get('dcf', 0),
                    "ipo_date": profile.get('ipoDate', ''),
                    "default_image": profile.get('defaultImage', False),
                    "is_etf": profile.get('isEtf', False),
                    "is_actively_trading": profile.get('isActivelyTrading', True)
                })
            
            # Add quote information
            if isinstance(quote_data, list) and len(quote_data) > 0:
                quote = quote_data[0]
                result.update({
                    "price": quote.get('price', 0),
                    "change": quote.get('change', 0),
                    "change_percent": quote.get('changesPercentage', 0),
                    "day_low": quote.get('dayLow', 0),
                    "day_high": quote.get('dayHigh', 0),
                    "year_low": quote.get('yearLow', 0),
                    "year_high": quote.get('yearHigh', 0),
                    "market_cap": quote.get('marketCap', 0),
                    "price_avg50": quote.get('priceAvg50', 0),
                    "price_avg200": quote.get('priceAvg200', 0),
                    "volume": quote.get('volume', 0),
                    "avg_volume": quote.get('avgVolume', 0),
                    "exchange": quote.get('exchange', 'Unknown'),
                    "open": quote.get('open', 0),
                    "previous_close": quote.get('previousClose', 0),
                    "eps": quote.get('eps', 0),
                    "pe": quote.get('pe', 0),
                    "earnings_announcement": quote.get('earningsAnnouncement', ''),
                    "shares_outstanding": quote.get('sharesOutstanding', 0),
                    "timestamp": quote.get('timestamp', 0)
                })
            
            return json.dumps(result)
            
        elif resource_id.startswith("market-"):
            market_type = resource_id[7:]  # Remove "market-" prefix
            
            if market_type == "gainers":
                data = await fmp_api_request("gainers", {})
            elif market_type == "losers":
                data = await fmp_api_request("losers", {})
            elif market_type == "active":
                data = await fmp_api_request("actives", {})
            else:
                return json.dumps({"error": f"Unknown market type: {market_type}"})
            
            if isinstance(data, list):
                return json.dumps({
                    "id": resource_id,
                    "type": "market",
                    "market_type": market_type,
                    "data": data
                })
            else:
                return json.dumps({"error": "Failed to fetch market data"})
        
        else:
            return json.dumps({"error": f"Unknown resource type: {resource_id}"})
            
    except Exception as e:
        return json.dumps({"error": f"Fetch failed: {str(e)}"})