"""Tests for the commodities tools module"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_list(mock_request):
    """Test the get_commodities_list function"""
    # Sample response data
    mock_response = [
        {
            "symbol": "GCUSD",
            "name": "Gold",
            "currency": "USD"
        },
        {
            "symbol": "SIUSD",
            "name": "Silver",
            "currency": "USD"
        },
        {
            "symbol": "PTUSD",
            "name": "Platinum",
            "currency": "USD"
        },
        {
            "symbol": "OUSD",
            "name": "Crude Oil WTI",
            "currency": "USD"
        },
        {
            "symbol": "BUSD",
            "name": "Brent Crude Oil",
            "currency": "USD"
        }
    ]
    
    # Set up the mock
    mock_request.return_value = mock_response
    
    # Import after patching
    from src.tools.commodities import get_commodities_list
    
    # Execute the tool
    result = await get_commodities_list()
    
    # Check API was called with correct parameters
    mock_request.assert_called_once_with("commodities-list", {})
    
    # Check the result contains expected information
    assert "# Available Commodities" in result
    assert "Symbol | Name | Currency | Group" in result
    assert "GCUSD | Gold | USD |" in result
    assert "SIUSD | Silver | USD |" in result
    assert "OUSD | Crude Oil WTI | USD |" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_prices(mock_request):
    """Test the get_commodities_prices function"""
    # Sample response data
    mock_response = [
        {
            "symbol": "GCUSD",
            "name": "Gold",
            "price": 2362.45,
            "change": 24.75,
            "changesPercentage": 1.06,
            "previousClose": 2337.70,
            "dayLow": 2335.25,
            "dayHigh": 2365.80,
            "yearLow": 1825.30,
            "yearHigh": 2400.15
        }
    ]
    
    # Set up the mock
    mock_request.return_value = mock_response
    
    # Import after patching
    from src.tools.commodities import get_commodities_prices
    
    # Execute the tool
    result = await get_commodities_prices("GCUSD")
    
    # Check API was called with correct parameters
    mock_request.assert_called_once_with("quote", {"symbol": "GCUSD"})
    
    # Check the result contains expected information
    assert "# Commodities Prices" in result
    assert "Symbol | Name | Price | Change | Change % | Day Range | Year Range" in result
    assert "GCUSD | Gold | 2,362.45 | 🔺 24.75 | 1.06% | 2,335.25 - 2,365.8 | 1,825.3 - 2,400.15" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_historical_price_eod_light(mock_request):
    """Test the get_historical_price_eod_light function"""
    # Sample response data
    mock_response = [
        {
            "symbol": "GCUSD",
            "date": "2025-02-04",
            "price": 2873.7,
            "volume": 137844
        },
        {
            "symbol": "GCUSD",
            "date": "2025-02-03",
            "price": 2865.2,
            "volume": 142563
        },
        {
            "symbol": "GCUSD",
            "date": "2025-02-02",
            "price": 2857.5,
            "volume": 134912
        }
    ]
    
    # Set up the mock
    mock_request.return_value = mock_response
    
    # Import after patching
    from src.tools.commodities import get_historical_price_eod_light
    
    # Execute the tool
    result = await get_historical_price_eod_light(symbol="GCUSD", limit=3)
    
    # Check API was called with correct parameters
    mock_request.assert_called_once_with("historical-price-eod/light", {"symbol": "GCUSD", "limit": 3})
    
    # Check the result contains expected information
    assert "# Historical Price Data for GCUSD" in result
    assert "| Date | Price | Volume | Daily Change | Daily Change % |" in result
    assert "| 2025-02-04 | 2,873.7 | 137,844 |" in result
    assert "| 2025-02-03 | 2,865.2 | 142,563 |" in result
    assert "| 2025-02-02 | 2,857.5 | 134,912 |" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_historical_price_eod_light_with_date_range(mock_request):
    """Test the get_historical_price_eod_light function with date range"""
    # Sample response data
    mock_response = [
        {
            "symbol": "GCUSD",
            "date": "2025-01-15",
            "price": 2750.3,
            "volume": 142390
        },
        {
            "symbol": "GCUSD",
            "date": "2025-01-14",
            "price": 2745.6,
            "volume": 138972
        }
    ]
    
    # Set up the mock
    mock_request.return_value = mock_response
    
    # Import after patching
    from src.tools.commodities import get_historical_price_eod_light
    
    # Execute the tool with from_date and to_date
    result = await get_historical_price_eod_light(
        symbol="GCUSD", 
        from_date="2025-01-14", 
        to_date="2025-01-15"
    )
    
    # Check API was called with correct parameters
    mock_request.assert_called_once_with("historical-price-eod/light", {
        "symbol": "GCUSD", 
        "from": "2025-01-14", 
        "to": "2025-01-15"
    })
    
    # Check the result contains expected information
    assert "# Historical Price Data for GCUSD" in result
    assert "From: 2025-01-14 To: 2025-01-15" in result
    assert "| 2025-01-15 | 2,750.3 | 142,390 |" in result
    assert "| 2025-01-14 | 2,745.6 | 138,972 |" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_historical_price_eod_light_error(mock_request):
    """Test the get_historical_price_eod_light function with error response"""
    # Set up the mock
    mock_request.return_value = {"error": "API Error", "message": "Symbol not found"}
    
    # Import after patching
    from src.tools.commodities import get_historical_price_eod_light
    
    # Execute the tool
    result = await get_historical_price_eod_light(symbol="INVALID")
    
    # Check error handling
    assert "Error fetching historical price data: Symbol not found" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_historical_price_eod_light_empty(mock_request):
    """Test the get_historical_price_eod_light function with empty response"""
    # Set up the mock
    mock_request.return_value = []
    
    # Import after patching
    from src.tools.commodities import get_historical_price_eod_light
    
    # Execute the tool
    result = await get_historical_price_eod_light(symbol="GCUSD")
    
    # Check empty response handling
    assert "No historical price data found for GCUSD" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_historical_price_eod_light_invalid_params(mock_request):
    """Test the get_historical_price_eod_light function with invalid parameters"""
    # Import after patching
    from src.tools.commodities import get_historical_price_eod_light
    
    # Execute the tool with empty symbol
    result = await get_historical_price_eod_light(symbol="")
    
    # Check parameter validation
    assert "Error: Symbol parameter is required" in result
    mock_request.assert_not_called()


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_list_error(mock_request):
    """Test the get_commodities_list function with error response"""
    # Set up the mock
    mock_request.return_value = {"error": "API Error", "message": "Internal server error"}
    
    # Import after patching
    from src.tools.commodities import get_commodities_list
    
    # Execute the tool
    result = await get_commodities_list()
    
    # Check error handling
    assert "Error fetching commodities list: Internal server error" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_prices_error(mock_request):
    """Test the get_commodities_prices function with error response"""
    # Set up the mock
    mock_request.return_value = {"error": "API Error", "message": "Symbol not found"}
    
    # Import after patching
    from src.tools.commodities import get_commodities_prices
    
    # Execute the tool
    result = await get_commodities_prices("INVALID")
    
    # Check error handling
    assert "Error fetching commodities prices: Symbol not found" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_list_empty(mock_request):
    """Test the get_commodities_list function with empty response"""
    # Set up the mock
    mock_request.return_value = []
    
    # Import after patching
    from src.tools.commodities import get_commodities_list
    
    # Execute the tool
    result = await get_commodities_list()
    
    # Check empty response handling
    assert "No commodities data found" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_prices_empty(mock_request):
    """Test the get_commodities_prices function with empty response"""
    # Set up the mock
    mock_request.return_value = []
    
    # Import after patching
    from src.tools.commodities import get_commodities_prices
    
    # Execute the tool
    result = await get_commodities_prices("GCUSD")
    
    # Check empty response handling
    assert "No price data found for commodities: GCUSD" in result


@pytest.mark.asyncio
@patch('src.api.client.fmp_api_request')
async def test_get_commodities_prices_no_symbols(mock_request):
    """Test the get_commodities_prices function with no symbols"""
    # Sample response data
    mock_response = [
        {
            "symbol": "GCUSD",
            "name": "Gold",
            "price": 2362.45,
            "change": 24.75,
            "changesPercentage": 1.06,
            "previousClose": 2337.70,
            "dayLow": 2335.25,
            "dayHigh": 2365.80,
            "yearLow": 1825.30,
            "yearHigh": 2400.15
        }
    ]
    
    # Set up the mock
    mock_request.return_value = mock_response
    
    # Import after patching
    from src.tools.commodities import get_commodities_prices
    
    # Execute the tool
    result = await get_commodities_prices()
    
    # Check API was called with correct parameters
    mock_request.assert_called_once_with("quote", {})
    
    # Check the result contains expected information
    assert "# Commodities Prices" in result