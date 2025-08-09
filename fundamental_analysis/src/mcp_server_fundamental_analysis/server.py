"""MCP server for performing fundamental analysis of stocks."""

import asyncio
import json
import finnhub
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any

# Initialize FastMCP server
mcp = FastMCP("fundamental_analysis")

class FundamentalAnalysisManager:
    """Manager for fetching and analyzing stock fundamental data."""

    def __init__(self, api_key: str):
        """Initialize the FundamentalAnalysisManager.

        Args:
            api_key: The API key for the Finnhub API.
        """
        self.finnhub_client = finnhub.Client(api_key=api_key)

    def get_fundamental_analysis(self, ticker: str) -> Dict[str, Any]:
        """Get fundamental analysis for a given stock ticker.

        Args:
            ticker: The stock ticker symbol (e.g., AAPL).

        Returns:
            A dictionary containing fundamental analysis data.
        """
        try:
            # Fetch basic financials
            basic_financials = self.finnhub_client.company_basic_financials(ticker, 'all')

            # Fetch company profile
            profile = self.finnhub_client.company_profile2(symbol=ticker)

            if not basic_financials or not profile:
                return {"error": f"Could not retrieve data for ticker {ticker}. It might be an invalid symbol."}

            # Extract key metrics
            metric = basic_financials.get('metric', {})

            # Prepare the result
            analysis = {
                "ticker": profile.get('ticker'),
                "companyName": profile.get('name'),
                "exchange": profile.get('exchange'),
                "marketCap": profile.get('marketCapitalization'),
                "sharesOutstanding": profile.get('shareOutstanding'),
                "peRatio": metric.get('peNormalizedAnnual'),
                "psRatio": metric.get('psAnnual'),
                "pbRatio": metric.get('pbAnnual'),
                "debtToEquity": metric.get('debt/equityAnnual'),
                "roe": metric.get('roeTTM'),
                "eps": metric.get('epsNormalizedAnnual'),
                "dividendYield": metric.get('dividendYieldIndicatedAnnual'),
            }

            return analysis

        except finnhub.FinnhubAPIException as e:
            return {"error": f"Finnhub API error: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

@mcp.tool()
async def get_fundamental_analysis(ticker: str, finnhub_api_key: str) -> str:
    """
    Performs fundamental analysis for a given stock code using the Finnhub API.

    Args:
        ticker: The stock ticker symbol (e.g., AAPL).
        finnhub_api_key: Your Finnhub API key.

    Returns:
        A JSON string containing the fundamental analysis report.
    """
    if not finnhub_api_key:
        return json.dumps({"error": "Finnhub API key is required."})

    manager = FundamentalAnalysisManager(api_key=finnhub_api_key)

    # Running the synchronous get_fundamental_analysis in a separate thread
    # to avoid blocking the asyncio event loop.
    loop = asyncio.get_event_loop()
    analysis_result = await loop.run_in_executor(
        None, manager.get_fundamental_analysis, ticker
    )

    return json.dumps(analysis_result, indent=2)

def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
