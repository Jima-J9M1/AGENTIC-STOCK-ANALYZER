"""
Financial Modeling Prep MCP Server

This server provides tools, resources, and prompts for interacting with
the Financial Modeling Prep API via the Model Context Protocol.
"""
import os
import sys
import pathlib
from dotenv import load_dotenv

# Add the parent directory to Python path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
from mcp.server.fastmcp import FastMCP, Context

# Import tools
from src.tools.company import get_company_profile, get_company_notes
from src.tools.statements import get_income_statement
from src.tools.search import search_by_symbol, search_by_name, search, fetch
from src.tools.quote import get_quote, get_quote_change, get_aftermarket_quote
from src.tools.charts import get_price_change
from src.tools.analyst import get_ratings_snapshot, get_financial_estimates, get_price_target_news, get_price_target_latest_news
from src.tools.calendar import get_company_dividends, get_dividends_calendar
from src.tools.indices import get_index_list, get_index_quote
from src.tools.market_performers import get_biggest_gainers, get_biggest_losers, get_most_active
from src.tools.market_hours import get_market_hours
from src.tools.etf import get_etf_sectors, get_etf_countries, get_etf_holdings
from src.tools.commodities import get_commodities_list, get_commodities_prices, get_historical_price_eod_light
from src.tools.crypto import get_crypto_list, get_crypto_quote
from src.tools.forex import get_forex_list, get_forex_quotes
from src.tools.technical_indicators import get_ema

# Import resources
from src.resources.company import get_stock_info_resource, get_financial_statement_resource, get_stock_peers_resource, get_price_targets_resource
from src.resources.market import get_market_snapshot_resource

# Import prompts
from src.prompts.templates import (
    company_analysis, financial_statement_analysis, stock_comparison,
    market_outlook, investment_idea_generation, technical_analysis,
    economic_indicator_analysis
)

# Create the MCP server
mcp = FastMCP(
    name="FMP Financial Data",
    dependencies=["httpx"]
)

# Register tools
mcp.tool()(get_company_profile)
mcp.tool()(get_company_notes)
mcp.tool()(get_quote)
mcp.tool()(get_quote_change)
mcp.tool()(get_aftermarket_quote)
mcp.tool()(get_price_change)
mcp.tool()(get_income_statement)
mcp.tool()(search_by_symbol)
mcp.tool()(search_by_name)
mcp.tool()(search)
mcp.tool()(fetch)
mcp.tool()(get_ratings_snapshot)
mcp.tool()(get_financial_estimates)
mcp.tool()(get_price_target_news)
mcp.tool()(get_price_target_latest_news)
mcp.tool()(get_company_dividends)
mcp.tool()(get_dividends_calendar)
mcp.tool()(get_index_list)
mcp.tool()(get_index_quote)
mcp.tool()(get_biggest_gainers)
mcp.tool()(get_biggest_losers)
mcp.tool()(get_most_active)
mcp.tool()(get_market_hours)
# TODO  fix tool
#mcp.tool()(get_etf_sectors)
# TODO  fix tool
#mcp.tool()(get_etf_countries)
# TODO  fix tool
#mcp.tool()(get_etf_holdings)
mcp.tool()(get_commodities_list)
mcp.tool()(get_commodities_prices)
mcp.tool()(get_historical_price_eod_light)
mcp.tool()(get_crypto_list)
mcp.tool()(get_crypto_quote)
mcp.tool()(get_forex_list)
mcp.tool()(get_forex_quotes)
mcp.tool()(get_ema)

# Register resources
mcp.resource("stock-info://{symbol}")(get_stock_info_resource)
mcp.resource("market-snapshot://current")(get_market_snapshot_resource)
mcp.resource("stock-peers://{symbol}")(get_stock_peers_resource)
mcp.resource("price-targets://{symbol}")(get_price_targets_resource)

# Register prompts
mcp.prompt()(company_analysis)
mcp.prompt()(financial_statement_analysis)
mcp.prompt()(stock_comparison)
mcp.prompt()(market_outlook)
mcp.prompt()(investment_idea_generation)
mcp.prompt()(technical_analysis)
mcp.prompt()(economic_indicator_analysis)

# Run the server if executed directly
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Run the FMP MCP Server")
    parser.add_argument("--sse", action="store_true", help="Run as an SSE server")
    parser.add_argument("--streamable-http", action="store_true", help="Run as a Streamable HTTP server")
    parser.add_argument("--stateless", action="store_true", help="Run in stateless mode (for Streamable HTTP)")
    parser.add_argument("--json-response", action="store_true", help="Use JSON responses instead of SSE streams")
    default_port = int(os.environ.get("PORT", 8000))
    parser.add_argument("--port", type=int, default=default_port, help=f"Port for server (default: {default_port})")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for server (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    # Check for conflicting transport options
    if args.sse and args.streamable_http:
        print("Error: Cannot specify both --sse and --streamable-http")
        sys.exit(1)
    
    if args.sse:
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import JSONResponse
        
        # Health check endpoint
        async def health_check(request):
            _ = request  # Suppress unused parameter warning
            return JSONResponse({"status": "healthy", "service": "fmp-mcp-server"})
        
        # Create Starlette app with health check and MCP server mounted as SSE app
        app = Starlette(
            routes=[
                Route("/health", health_check, methods=["GET"]),
                Mount("/", app=mcp.sse_app()),
            ]
        )
        
        # Print information message
        print(f"Starting FMP MCP Server (SSE mode) on http://{args.host}:{args.port}")
        print(f"API Key configured: {'Yes' if os.environ.get('FMP_API_KEY') else 'No - using demo mode'}")
        
        # Run the server
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.streamable_http:
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import JSONResponse
        
        # Determine mode description
        if args.stateless:
            mode_desc = "stateless" + (" JSON" if args.json_response else " SSE")
        else:
            mode_desc = "stateful" + (" JSON" if args.json_response else " SSE")
        
        print(f"Starting FMP MCP Server (Streamable HTTP {mode_desc} mode) on http://{args.host}:{args.port}")
        print(f"API Key configured: {'Yes' if os.environ.get('FMP_API_KEY') else 'No - using demo mode'}")
        print(f"Streamable HTTP endpoint: http://{args.host}:{args.port}/mcp/")
        print(f"Note: Use the endpoint URL with trailing slash in MCP Inspector")
        
        # Configure the main mcp instance for the requested mode
        # We need to recreate the FastMCP instance with the correct configuration
        from mcp.server.fastmcp import FastMCP
        
        # Create new FastMCP instance with desired configuration
        streamable_mcp = FastMCP(
            "FMP Financial Data",
            dependencies=["httpx"],
            stateless_http=args.stateless,
            json_response=args.json_response
        )
        
        # Re-register all tools using the same decorators approach
        # Import tools
        from src.tools.company import get_company_profile, get_company_notes
        from src.tools.statements import get_income_statement
        from src.tools.search import search_by_symbol, search_by_name, search, fetch
        from src.tools.quote import get_quote, get_quote_change, get_aftermarket_quote
        from src.tools.charts import get_price_change
        from src.tools.analyst import get_ratings_snapshot, get_financial_estimates, get_price_target_news, get_price_target_latest_news
        from src.tools.calendar import get_company_dividends, get_dividends_calendar
        from src.tools.indices import get_index_list, get_index_quote
        from src.tools.market_performers import get_biggest_gainers, get_biggest_losers, get_most_active
        from src.tools.market_hours import get_market_hours
        # ETF tools temporarily disabled in server registration
        # from src.tools.etf import get_etf_sectors, get_etf_countries, get_etf_holdings
        from src.tools.commodities import get_commodities_list, get_commodities_prices, get_historical_price_eod_light
        from src.tools.crypto import get_crypto_list, get_crypto_quote
        from src.tools.forex import get_forex_list, get_forex_quotes
        from src.tools.technical_indicators import get_ema
        
        # Import resources
        from src.resources.company import get_stock_info_resource, get_stock_peers_resource, get_price_targets_resource
        # get_financial_statement_resource not currently used
        from src.resources.market import get_market_snapshot_resource
        
        # Import prompts
        from src.prompts.templates import (
            company_analysis, financial_statement_analysis, stock_comparison,
            market_outlook, investment_idea_generation, technical_analysis,
            economic_indicator_analysis
        )
        
        # Register tools
        streamable_mcp.tool()(get_company_profile)
        streamable_mcp.tool()(get_company_notes)
        streamable_mcp.tool()(get_quote)
        streamable_mcp.tool()(get_quote_change)
        streamable_mcp.tool()(get_aftermarket_quote)
        streamable_mcp.tool()(get_price_change)
        streamable_mcp.tool()(get_income_statement)
        streamable_mcp.tool()(search_by_symbol)
        streamable_mcp.tool()(search_by_name)
        streamable_mcp.tool()(search)
        streamable_mcp.tool()(fetch)
        streamable_mcp.tool()(get_ratings_snapshot)
        streamable_mcp.tool()(get_financial_estimates)
        streamable_mcp.tool()(get_price_target_news)
        streamable_mcp.tool()(get_price_target_latest_news)
        streamable_mcp.tool()(get_company_dividends)
        streamable_mcp.tool()(get_dividends_calendar)
        streamable_mcp.tool()(get_index_list)
        streamable_mcp.tool()(get_index_quote)
        streamable_mcp.tool()(get_biggest_gainers)
        streamable_mcp.tool()(get_biggest_losers)
        streamable_mcp.tool()(get_most_active)
        streamable_mcp.tool()(get_market_hours)
        streamable_mcp.tool()(get_commodities_list)
        streamable_mcp.tool()(get_commodities_prices)
        streamable_mcp.tool()(get_historical_price_eod_light)
        streamable_mcp.tool()(get_crypto_list)
        streamable_mcp.tool()(get_crypto_quote)
        streamable_mcp.tool()(get_forex_list)
        streamable_mcp.tool()(get_forex_quotes)
        streamable_mcp.tool()(get_ema)
        
        # Register resources
        streamable_mcp.resource("stock-info://{symbol}")(get_stock_info_resource)
        streamable_mcp.resource("market-snapshot://current")(get_market_snapshot_resource)
        streamable_mcp.resource("stock-peers://{symbol}")(get_stock_peers_resource)
        streamable_mcp.resource("price-targets://{symbol}")(get_price_targets_resource)
        
        # Register prompts
        streamable_mcp.prompt()(company_analysis)
        streamable_mcp.prompt()(financial_statement_analysis)
        streamable_mcp.prompt()(stock_comparison)
        streamable_mcp.prompt()(market_outlook)
        streamable_mcp.prompt()(investment_idea_generation)
        streamable_mcp.prompt()(technical_analysis)
        streamable_mcp.prompt()(economic_indicator_analysis)
        
        # Get the FastMCP streamable HTTP app
        app = streamable_mcp.streamable_http_app()
        
        # Add health check route to the FastMCP app
        from starlette.routing import Route
        async def health_check(request):
            _ = request  # Suppress unused parameter warning
            return JSONResponse({"status": "healthy", "service": "fmp-mcp-server"})
        
        # Insert health check route at the beginning
        health_route = Route("/health", health_check, methods=["GET"])
        app.router.routes.insert(0, health_route)
        
        # Run the server
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # Run as stdio server
        mcp.run()