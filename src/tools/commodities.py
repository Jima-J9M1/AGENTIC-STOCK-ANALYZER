"""
Commodities-related tools for the FMP MCP server

This module contains tools related to the Commodities section of the Financial Modeling Prep API:
https://site.financialmodelingprep.com/developer/docs/stable/commodities-list
https://site.financialmodelingprep.com/developer/docs/stable/commodities-prices
https://site.financialmodelingprep.com/developer/docs/stable/commodities-historical-price-eod-light
"""
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from src.api.client import fmp_api_request
from src.tools.statements import format_number


async def get_commodities_list() -> str:
    """
    Get a list of available commodities
    
    Returns:
        List of available commodities with their symbols
    """
    data = await fmp_api_request("commodities-list", {})
    
    if isinstance(data, dict) and "error" in data:
        return f"Error fetching commodities list: {data.get('message', 'Unknown error')}"
    
    if not data or not isinstance(data, list) or len(data) == 0:
        return "No commodities data found"
    
    # Format the response
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result = [
        "# Available Commodities",
        f"*Data as of {current_time}*",
        "",
        "| Symbol | Name | Currency | Group |",
        "|--------|------|----------|-------|"
    ]
    
    # Group commodities by type
    commodity_groups = {}
    for commodity in data:
        symbol = commodity.get('symbol', 'N/A')
        name = commodity.get('name', 'N/A')
        currency = commodity.get('currency', 'USD')
        
        # Determine the commodity group
        if any(metal in name.lower() for metal in ['gold', 'silver', 'platinum', 'palladium', 'copper']):
            group = "Metals"
        elif any(energy in name.lower() for energy in ['oil', 'gas', 'gasoline', 'diesel', 'propane', 'ethanol']):
            group = "Energy"
        elif any(agri in name.lower() for agri in ['corn', 'wheat', 'soybean', 'sugar', 'coffee', 'cotton', 'rice']):
            group = "Agricultural"
        else:
            group = "Other"
        
        result.append(f"| {symbol} | {name} | {currency} | {group} |")
    
    # Add a note about usage
    result.append("")
    result.append("*Note: Use these symbols with the get_commodities_prices function to get current values.*")
    
    return "\n".join(result)


async def get_commodities_prices(symbol: str = None) -> str:
    """
    Get current prices for commodities
    
    Args:
        symbols: Comma-separated list of commodity symbols (e.g., "OUSX,GCUSD")
                If not provided, returns all available commodities
    
    Returns:
        Current prices for the specified commodities
    """
    params = {"symbol": symbol} if symbol else {}
    data = await fmp_api_request("quote", params)
    
    if isinstance(data, dict) and "error" in data:
        return f"Error fetching commodities prices: {data.get('message', 'Unknown error')}"
    
    if not data or not isinstance(data, list) or len(data) == 0:
        return f"No price data found for commodities: {symbol if symbol else 'all'}"
    
    # Format the response
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result = [
        "# Commodities Prices",
        f"*Data as of {current_time}*",
        "",
        "| Symbol | Name | Price | Change | Change % | Day Range | Year Range |",
        "|--------|------|-------|--------|----------|-----------|------------|"
    ]
    
    # Group commodities by type for better organization
    commodities_by_group = {}
    
    for commodity in data:
        symbol = commodity.get('symbol', 'N/A')
        name = commodity.get('name', 'N/A')
        price = format_number(commodity.get('price', 'N/A'))
        change = commodity.get('change', 0)
        change_percent = commodity.get('changesPercentage', 0)
        
        # Determine change emoji
        change_emoji = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
        
        # Format the values
        change_str = f"{change_emoji} {format_number(abs(change))}"
        change_percent_str = f"{change_percent}%"
        
        day_low = format_number(commodity.get('dayLow', 'N/A'))
        day_high = format_number(commodity.get('dayHigh', 'N/A'))
        day_range = f"{day_low} - {day_high}"
        
        year_low = format_number(commodity.get('yearLow', 'N/A'))
        year_high = format_number(commodity.get('yearHigh', 'N/A'))
        year_range = f"{year_low} - {year_high}"
        
        # Determine the commodity group
        if any(metal in name.lower() for metal in ['gold', 'silver', 'platinum', 'palladium', 'copper']):
            group = "Metals"
        elif any(energy in name.lower() for energy in ['oil', 'gas', 'gasoline', 'diesel', 'propane', 'ethanol']):
            group = "Energy"
        elif any(agri in name.lower() for agri in ['corn', 'wheat', 'soybean', 'sugar', 'coffee', 'cotton', 'rice']):
            group = "Agricultural"
        else:
            group = "Other"
        
        if group not in commodities_by_group:
            commodities_by_group[group] = []
        
        commodities_by_group[group].append({
            'symbol': symbol,
            'name': name,
            'price': price,
            'change': change_str,
            'change_percent': change_percent_str,
            'day_range': day_range,
            'year_range': year_range
        })
    
    # Add commodities to the table, grouped by type
    groups_order = ["Energy", "Metals", "Agricultural", "Other"]
    
    for group in groups_order:
        if group in commodities_by_group and commodities_by_group[group]:
            result.append(f"### {group}")
            
            for commodity in commodities_by_group[group]:
                result.append(
                    f"| {commodity['symbol']} | {commodity['name']} | "
                    f"{commodity['price']} | {commodity['change']} | "
                    f"{commodity['change_percent']} | {commodity['day_range']} | "
                    f"{commodity['year_range']} |"
                )
            
            result.append("")
    
    return "\n".join(result)


async def get_historical_price_eod_light(
    symbol: str,
    limit: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> str:
    """
    Get historical price data for a commodity from the EOD light API
    
    Args:
        symbol: The commodity symbol (e.g., "GCUSD" for Gold)
        limit: Optional number of results to return
        from_date: Optional start date in format "YYYY-MM-DD"
        to_date: Optional end date in format "YYYY-MM-DD"
    
    Returns:
        Historical price data formatted as markdown
    """
    # Validate parameters
    if not symbol:
        return "Error: Symbol parameter is required"
    
    # Prepare parameters
    params = {"symbol": symbol}
    if limit is not None:
        params["limit"] = limit
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    # Make API request
    data = await fmp_api_request("historical-price-eod/light", params)
    
    # Check for errors
    if isinstance(data, dict) and "error" in data:
        return f"Error fetching historical price data: {data.get('message', 'Unknown error')}"
    
    # Check for empty response
    if not data or not isinstance(data, list) or len(data) == 0:
        return f"No historical price data found for {symbol}"
    
    # Format the response
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result = [
        f"# Historical Price Data for {symbol}",
        f"*Data as of {current_time}*",
    ]
    
    # Add date range info if provided
    if from_date and to_date:
        result.append(f"From: {from_date} To: {to_date}")
    elif from_date:
        result.append(f"From: {from_date}")
    elif to_date:
        result.append(f"To: {to_date}")
    
    # Add table header
    result.extend([
        "",
        "| Date | Price | Volume | Daily Change | Daily Change % |",
        "|------|-------|--------|-------------|----------------|"
    ])
    
    # Sort data by date (newest first)
    sorted_data = sorted(data, key=lambda x: x.get('date', ''), reverse=True)
    
    # Process each data point and calculate daily changes
    for i, entry in enumerate(sorted_data):
        date = entry.get('date', 'N/A')
        price = format_number(entry.get('price', 'N/A'))
        volume = format_number(entry.get('volume', 'N/A'))
        
        # Calculate daily change if we have data for the previous day
        if i < len(sorted_data) - 1:
            current_price = entry.get('price', 0)
            prev_price = sorted_data[i + 1].get('price', 0)
            
            if prev_price and current_price:
                daily_change = current_price - prev_price
                daily_change_pct = (daily_change / prev_price) * 100
                
                # Determine change emoji
                change_emoji = "🔺" if daily_change > 0 else "🔻" if daily_change < 0 else "➖"
                
                # Format the values
                daily_change_str = f"{change_emoji} {format_number(abs(daily_change))}"
                daily_change_pct_str = f"{change_emoji} {format_number(abs(daily_change_pct))}%"
            else:
                daily_change_str = "N/A"
                daily_change_pct_str = "N/A"
        else:
            daily_change_str = "N/A"
            daily_change_pct_str = "N/A"
        
        # Add to results
        result.append(f"| {date} | {price} | {volume} | {daily_change_str} | {daily_change_pct_str} |")
    
    # Add a note about usage
    result.extend([
        "",
        f"*Note: Historical price data shows the closing price for {symbol} on each trading day.*"
    ])
    
    return "\n".join(result)