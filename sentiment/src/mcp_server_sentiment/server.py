import asyncio
import nltk
from newsapi import NewsApiClient
from nltk.sentiment import SentimentIntensityAnalyzer
import os
from typing import Any, Dict, List, Optional

class SentimentManager:
    """Manager for sentiment analysis operations."""

    def __init__(self, api_key: str):
        """Initialize the Sentiment Manager.

        Args:
            api_key: The API key for NewsAPI.
        """
        self.newsapi = NewsApiClient(api_key=api_key)
        self._ensure_vader_lexicon_is_downloaded()

    def _ensure_vader_lexicon_is_downloaded(self):
        """Check if the VADER lexicon is downloaded, and if not, download it."""
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')

    async def get_news(self, stock_symbol: str) -> Optional[Dict[str, Any]]:
        """Get news for a given stock symbol."""
        try:
            return await asyncio.to_thread(
                self.newsapi.get_everything,
                q=stock_symbol,
                language='en',
                sort_by='publishedAt',
                page_size=20
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def analyze_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the sentiment of a list of articles."""
        sia = SentimentIntensityAnalyzer()
        sentiments = []
        for article in articles:
            text = article.get('title', '') + " " + article.get('description', '')
            if text.strip():
                sentiment = sia.polarity_scores(text)
                sentiments.append(sentiment)

        if not sentiments:
            return {"overall_sentiment": "neutral", "positive": 0, "negative": 0, "neutral": 0, "articles": []}

        avg_compound = sum(s['compound'] for s in sentiments) / len(sentiments)

        overall_sentiment = "neutral"
        if avg_compound > 0.05:
            overall_sentiment = "positive"
        elif avg_compound < -0.05:
            overall_sentiment = "negative"

        return {
            "overall_sentiment": overall_sentiment,
            "positive_articles": len([s for s in sentiments if s['compound'] > 0.05]),
            "negative_articles": len([s for s in sentiments if s['compound'] < -0.05]),
            "neutral_articles": len([s for s in sentiments if -0.05 <= s['compound'] <= 0.05]),
            "articles": articles
        }

from mcp.server.fastmcp import FastMCP
import json

# Initialize FastMCP server
mcp = FastMCP("sentiment")

@mcp.tool()
async def get_stock_sentiment(stock_symbol: str, api_key: Optional[str] = None) -> str:
    """Get sentiment analysis for a given stock symbol.

    Args:
        stock_symbol: The stock symbol (e.g., AAPL, GOOGL).
        api_key: Your NewsAPI API key. If not provided, it will try to use the NEWS_API_KEY environment variable.
    """
    if not api_key:
        api_key = os.environ.get("NEWS_API_KEY")

    if not api_key:
        return json.dumps({
            "error": "API key not provided. Please provide an API key directly or set the NEWS_API_KEY environment variable."
        })

    try:
        manager = SentimentManager(api_key=api_key)

        news = await manager.get_news(stock_symbol)
        if news.get("status") == "error":
            return json.dumps({"error": news.get("message")})

        articles = news.get('articles', [])
        if not articles:
            return json.dumps({"overall_sentiment": "neutral", "message": f"No news articles found for {stock_symbol}."})

        sentiment_result = manager.analyze_sentiment(articles)

        # Format the output
        top_articles = []
        for article in articles[:5]:
            top_articles.append({
                "title": article.get('title'),
                "url": article.get('url'),
                "source": article.get('source', {}).get('name')
            })

        response = {
            "overall_sentiment": sentiment_result["overall_sentiment"],
            "summary": {
                "positive_articles": sentiment_result["positive_articles"],
                "negative_articles": sentiment_result["negative_articles"],
                "neutral_articles": sentiment_result["neutral_articles"],
                "total_articles": len(articles)
            },
            "top_headlines": top_articles
        }

        return json.dumps(response, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
