#!/bin/bash
set -e

echo "=============================================="
echo "MCP Fundamental Analysis Server Test Suite"
echo "=============================================="

# Change to the script's directory, then to the project root
cd "$(dirname "$0")"

echo "Running tests in $(pwd)..."

uv run pytest tests/ -v
