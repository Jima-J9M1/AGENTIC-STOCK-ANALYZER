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
                text_parts.append(f"\\nCurrent Price: ${quote.get('price', 0)}")
                text_parts.append(f"Change: ${quote.get('change', 0)} ({quote.get('changesPercentage', 0)}%)")
                text_parts.append(f"Day Range: ${quote.get('dayLow', 0)} - ${quote.get('dayHigh', 0)}")
                text_parts.append(f"52-Week Range: ${quote.get('yearLow', 0)} - ${quote.get('yearHigh', 0)}")
                text_parts.append(f"Volume: {quote.get('volume', 0):,}")
                text_parts.append(f"Average Volume: {quote.get('avgVolume', 0):,}")
                text_parts.append(f"P/E Ratio: {quote.get('pe', 'N/A')}")
                text_parts.append(f"EPS: ${quote.get('eps', 0)}")
            
            # Combine all text
            full_text = "\\n".join(text_parts) if text_parts else "No information available"
            
            # Build metadata
            metadata = {}
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile = profile_data[0]
                metadata.update({
                    "sector": profile.get('sector'),
                    "industry": profile.get('industry'),
                    "exchange": profile.get('exchangeShortName'),
                    "currency": profile.get('currency', 'USD'),
                    "country": profile.get('country'),
                    "is_etf": profile.get('isEtf', False)
                })
            
            if isinstance(quote_data, list) and len(quote_data) > 0:
                quote = quote_data[0]
                metadata.update({
                    "price": quote.get('price'),
                    "market_cap": quote.get('marketCap'),
                    "pe_ratio": quote.get('pe'),
                    "volume": quote.get('volume')
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