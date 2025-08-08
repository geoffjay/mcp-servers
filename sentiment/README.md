# MCP Server for Stock Sentiment Analysis

An MCP (Model Context Protocol) server that provides tools for performing sentiment analysis on news articles related to a given stock symbol.

## Overview

This server fetches recent news articles for a specified stock and analyzes their sentiment to provide an overall sentiment (positive, negative, or neutral). It uses the [News API](https://newsapi.org) to get news and the NLTK library for sentiment analysis.

## Features

- **Stock Sentiment Analysis**: Get the overall sentiment for a stock.
- **News Headlines**: See the top headlines that contributed to the sentiment score.
- **API Key Management**: Use an API key from an environment variable or pass it directly.

## Installation

### Using uvx (Recommended)

```bash
uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=sentiment mcp-server-sentiment
```

### Development Installation

```bash
git clone https://github.com/geoffjay/mcp-servers.git
cd mcp-servers/sentiment
uv sync --dev
```

## Usage

### As an MCP Server

The server can be used with any MCP-compatible client. For Claude Desktop, add the following to your configuration:

```json
{
  "mcpServers": {
    "sentiment": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/geoffjay/mcp-servers#subdirectory=sentiment",
        "mcp-server-sentiment"
      ],
      "env": {
        "NEWS_API_KEY": "<ENV Value>"
      }
    }
  }
}
```

### Getting a News API Key

This server requires an API key from [News API](https://newsapi.org).
1. Go to https://newsapi.org/register and register for a free account.
2. Once registered, you will find your API key on your account page.
3. You can either pass the API key as an argument to the tool or set it as an environment variable named `NEWS_API_KEY`.

### Available Tools

- **`get_stock_sentiment`**: Get sentiment analysis for a stock.
  - `stock_symbol`: The stock symbol (e.g., AAPL, TSLA).
  - `api_key`: Your News API key (optional if `NEWS_API_KEY` is set).

## Example

```python
# Get sentiment for Apple Inc.
sentiment_json = await get_stock_sentiment(
    stock_symbol="AAPL",
    api_key="YOUR_NEWS_API_KEY"
)

# The result is a JSON string
import json
sentiment = json.loads(sentiment_json)

print(f"Overall sentiment for AAPL: {sentiment['overall_sentiment']}")
```

## Development

### Setup

```bash
# Clone and setup development environment
git clone https://github.com/geoffjay/mcp-servers.git
cd mcp-servers/sentiment

# The .envrc file will automatically activate the virtual environment with direnv
# Or manually activate:
source .venv/bin/activate

# Install development dependencies
uv sync --dev
```

### Running Tests

```bash
# Run all tests
uv run pytest
```

## Requirements

- Python 3.10 or higher
- A News API key

## License

This project is licensed under the MIT License. See the parent repository for full license details.
