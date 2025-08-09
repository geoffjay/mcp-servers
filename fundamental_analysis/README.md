# Fundamental Analysis MCP Server

An MCP server for performing fundamental analysis of stocks using the [Finnhub API](https://finnhub.io/).

## Features

- Fetches key fundamental metrics for a given stock ticker.
- Provides data such as P/E ratio, P/B ratio, debt-to-equity, and more.

## API Key Setup

This server requires a Finnhub API key. There are two ways to provide the key:

1.  **Environment Variable (recommended)**: Set the `FINNHUB_API_KEY` environment variable. The server will automatically use this key.
    ```bash
    export FINNHUB_API_KEY="your_finnhub_api_key"
    ```

2.  **Tool Argument**: Pass the key as the `finnhub_api_key` argument when calling the tool. This will override the environment variable if it is set.

## Tools

### `get_fundamental_analysis`

Performs fundamental analysis for a given stock code.

**Arguments**:

- `ticker` (str): The stock ticker symbol (e.g., `AAPL`).
- `finnhub_api_key` (str, optional): Your Finnhub API key. If not provided, the server will try to use the `FINNHUB_API_KEY` environment variable.

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

## Development

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management

### Running Tests

To run the tests for this server:

```bash
cd fundamental_analysis
uv run pytest tests/ -v
```
