# Fundamental Analysis MCP Server

An MCP server for performing fundamental analysis of stocks using the [Finnhub API](https://finnhub.io/).

## Features

- Fetches key fundamental metrics for a given stock ticker.
- Provides data such as P/E ratio, P/B ratio, debt-to-equity, and more.

## Tools

### `get_fundamental_analysis`

Performs fundamental analysis for a given stock code.

**Arguments**:

- `ticker` (str): The stock ticker symbol (e.g., `AAPL`).
- `finnhub_api_key` (str): Your Finnhub API key. You can get a free API key from the [Finnhub website](https://finnhub.io/).

**Returns**:

A JSON string containing the fundamental analysis report.

**Example Usage**:

```json
{
  "ticker": "AAPL",
  "companyName": "Apple Inc",
  "exchange": "NASDAQ NMS - GLOBAL MARKET",
  "marketCap": 3000000,
  "sharesOutstanding": 16000,
  "peRatio": 30.0,
  "psRatio": 7.0,
  "pbRatio": 40.0,
  "debtToEquity": 1.5,
  "roe": 0.5,
  "eps": 6.0,
  "dividendYield": 0.005
}
```

## Requirements

- A free API key from [Finnhub](https://finnhub.io/).

## Development

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management

### Running Tests

To run the tests for this server:

```bash
cd fundamental_analysis
uv run --extra dev pytest tests/ -v
```

**Note**: The current test suite is minimal and only checks for the existence of the tool. Comprehensive integration tests require a valid Finnhub API key.
