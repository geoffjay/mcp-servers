"""Tests for the fundamental analysis server."""

import asyncio
import json
import os
import pytest
from unittest.mock import MagicMock, patch

from mcp_server_fundamental_analysis.server import get_fundamental_analysis

@pytest.mark.asyncio
async def test_get_fundamental_analysis_with_key_as_arg():
    """Test successful analysis with API key passed as an argument."""
    mock_analysis = {"ticker": "AAPL", "peRatio": 30.0}
    mock_manager_instance = MagicMock()
    mock_manager_instance.get_fundamental_analysis.return_value = mock_analysis

    with patch('mcp_server_fundamental_analysis.server.FundamentalAnalysisManager') as mock_manager_class:
        mock_manager_class.return_value = mock_manager_instance
        result_str = await get_fundamental_analysis(ticker="AAPL", finnhub_api_key="arg_key")
        result = json.loads(result_str)
        mock_manager_class.assert_called_once_with(api_key="arg_key")
        assert result == mock_analysis

@pytest.mark.asyncio
@patch.dict(os.environ, {"FINNHUB_API_KEY": "env_key"})
async def test_get_fundamental_analysis_with_key_from_env():
    """Test successful analysis with API key from environment variable."""
    mock_analysis = {"ticker": "GOOG", "peRatio": 25.0}
    mock_manager_instance = MagicMock()
    mock_manager_instance.get_fundamental_analysis.return_value = mock_analysis

    with patch('mcp_server_fundamental_analysis.server.FundamentalAnalysisManager') as mock_manager_class:
        mock_manager_class.return_value = mock_manager_instance
        result_str = await get_fundamental_analysis(ticker="GOOG")
        result = json.loads(result_str)
        mock_manager_class.assert_called_once_with(api_key="env_key")
        assert result == mock_analysis

@pytest.mark.asyncio
async def test_get_fundamental_analysis_no_key():
    """Test call with no API key provided."""
    result_str = await get_fundamental_analysis(ticker="MSFT")
    result = json.loads(result_str)
    assert "error" in result
    assert "API key not found" in result["error"]

@pytest.mark.asyncio
@patch.dict(os.environ, {"FINNHUB_API_KEY": "env_key"})
async def test_arg_key_precedence():
    """Test that the argument key takes precedence over the environment variable."""
    mock_analysis = {"ticker": "TSLA", "peRatio": 100.0}
    mock_manager_instance = MagicMock()
    mock_manager_instance.get_fundamental_analysis.return_value = mock_analysis

    with patch('mcp_server_fundamental_analysis.server.FundamentalAnalysisManager') as mock_manager_class:
        mock_manager_class.return_value = mock_manager_instance
        result_str = await get_fundamental_analysis(ticker="TSLA", finnhub_api_key="arg_key_override")
        result = json.loads(result_str)
        mock_manager_class.assert_called_once_with(api_key="arg_key_override")
        assert result == mock_analysis
