"""
Financial Modeling Prep API client
"""
import os
import httpx
from typing import Dict, Any, Optional

# FMP API Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

async def fmp_api_request(endpoint: str, params: Dict = None, api_key: str = None) -> Dict:
    """
    Make a request to the Financial Modeling Prep API
    
    Args:
        endpoint: API endpoint path (without the base URL)
        params: Query parameters for the request
        api_key: API key for authentication (uses env var or default if None)
        
    Returns:
        JSON response data or error information
    """
    url = f"{FMP_BASE_URL}/{endpoint}"
    
    # Add API key to params
    if params is None:
        params = {}
    
    # Use provided API key or get from environment dynamically
    if api_key is None:
        api_key = os.environ.get("FMP_API_KEY", "demo")
    
    params["apikey"] = api_key
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()  # Remove await here, httpx Response.raise_for_status() is not a coroutine
            return response.json()  # Remove await here, httpx Response.json() is not a coroutine
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code}", "message": str(e)}
    except httpx.RequestError as e:
        return {"error": "Request error", "message": str(e)}
    except Exception as e:
        return {"error": "Unknown error", "message": str(e)}