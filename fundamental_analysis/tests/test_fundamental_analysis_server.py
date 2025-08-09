"""Tests for the fundamental analysis server."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from mcp_server_fundamental_analysis.server import get_fundamental_analysis

@pytest.mark.asyncio
async def test_get_fundamental_analysis_success():
    """Test successful fundamental analysis retrieval."""
    mock_analysis = {
        "ticker": "AAPL",
        "companyName": "Apple Inc",
        "peRatio": 30.0,
    }

    # Create a mock for the manager instance
    mock_manager_instance = MagicMock()
    mock_manager_instance.get_fundamental_analysis.return_value = mock_analysis

    # Patch the class to return our mock instance
    with patch('mcp_server_fundamental_analysis.server.FundamentalAnalysisManager') as mock_manager_class:
        mock_manager_class.return_value = mock_manager_instance

        # Call the tool function
        result_str = await get_fundamental_analysis(ticker="AAPL", finnhub_api_key="test_key")
        result = json.loads(result_str)

        # Assertions
        mock_manager_class.assert_called_once_with(api_key="test_key")
        mock_manager_instance.get_fundamental_analysis.assert_called_once_with("AAPL")
        assert result == mock_analysis

@pytest.mark.asyncio
async def test_get_fundamental_analysis_no_api_key():
    """Test call with no Finnhub API key."""
    result_str = await get_fundamental_analysis(ticker="AAPL", finnhub_api_key="")
    result = json.loads(result_str)

    assert "error" in result
    assert "API key is required" in result["error"]

@pytest.mark.asyncio
async def test_get_fundamental_analysis_api_error():
    """Test handling of an API error from the manager."""
    error_message = {"error": "Finnhub API error: Invalid API key"}

    mock_manager_instance = MagicMock()
    mock_manager_instance.get_fundamental_analysis.return_value = error_message

    with patch('mcp_server_fundamental_analysis.server.FundamentalAnalysisManager') as mock_manager_class:
        mock_manager_class.return_value = mock_manager_instance

        result_str = await get_fundamental_analysis(ticker="AAPL", finnhub_api_key="invalid_key")
        result = json.loads(result_str)

        assert result == error_message
