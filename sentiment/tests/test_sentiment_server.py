import pytest
import json
from mcp_server_sentiment.server import get_stock_sentiment
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch('mcp_server_sentiment.server.SentimentManager')
async def test_get_stock_sentiment_success(MockSentimentManager):
    # Arrange
    mock_manager_instance = MockSentimentManager.return_value

    # Mock the async method get_news
    async def mock_get_news(stock_symbol):
        return {
            "status": "ok",
            "articles": [
                {"title": "Great news for Tesla!", "description": "Stock is going up."},
                {"title": "Positive outlook for Tesla", "description": "Analysts are happy."}
            ]
        }
    mock_manager_instance.get_news = mock_get_news

    # Mock the sync method analyze_sentiment
    mock_manager_instance.analyze_sentiment.return_value = {
        "overall_sentiment": "positive",
        "positive_articles": 2,
        "negative_articles": 0,
        "neutral_articles": 0
    }

    # Act
    result_str = await get_stock_sentiment("TSLA", "fake_api_key")
    result = json.loads(result_str)

    # Assert
    assert result['overall_sentiment'] == 'positive'
    assert result['summary']['positive_articles'] == 2
    assert len(result['top_headlines']) == 2
    assert result['top_headlines'][0]['title'] == "Great news for Tesla!"

@pytest.mark.asyncio
async def test_get_stock_sentiment_no_api_key():
    # Act
    result_str = await get_stock_sentiment("TSLA") # No api_key provided
    result = json.loads(result_str)

    # Assert
    assert "error" in result
    assert "API key not provided" in result["error"]

@pytest.mark.asyncio
@patch('mcp_server_sentiment.server.SentimentManager')
async def test_get_stock_sentiment_api_error(MockSentimentManager):
    # Arrange
    mock_manager_instance = MockSentimentManager.return_value
    async def mock_get_news_error(stock_symbol):
        return {"status": "error", "message": "API Key Invalid"}
    mock_manager_instance.get_news = mock_get_news_error

    # Act
    result_str = await get_stock_sentiment("TSLA", "invalid_api_key")
    result = json.loads(result_str)

    # Assert
    assert "error" in result
    assert "API Key Invalid" in result["error"]

@pytest.mark.asyncio
@patch('mcp_server_sentiment.server.SentimentManager')
async def test_get_stock_sentiment_no_articles(MockSentimentManager):
    # Arrange
    mock_manager_instance = MockSentimentManager.return_value
    async def mock_get_news_empty(stock_symbol):
        return {"status": "ok", "articles": []}
    mock_manager_instance.get_news = mock_get_news_empty

    # Act
    result_str = await get_stock_sentiment("TSLA", "fake_api_key")
    result = json.loads(result_str)

    # Assert
    assert result['overall_sentiment'] == 'neutral'
    assert "No news articles found" in result["message"]
