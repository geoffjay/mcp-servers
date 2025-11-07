# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of Model Context Protocol (MCP) servers built with Python and FastMCP. Each server is an independent Python package that exposes tools for AI assistants to interact with specific functionality. The repository uses a monorepo structure with multiple server implementations in separate subdirectories.

## Repository Structure

The repository follows a monorepo pattern where each MCP server is a self-contained package:

```
mcp-servers/
├── overmind/           # Overmind process manager server
│   ├── src/mcp_server_overmind/
│   │   └── server.py   # Main OvermindManager class and FastMCP tools
│   ├── tests/
│   ├── test_environment/  # Integration test setup with sample Procfiles
│   └── pyproject.toml
├── sentiment/          # Stock sentiment analysis server
│   ├── src/mcp_server_sentiment/
│   │   └── server.py   # SentimentManager class and FastMCP tools
│   ├── tests/
│   └── pyproject.toml
└── README.md          # Main documentation
```

## Development Commands

### Testing

Each server has its own test suite. Navigate to the server directory first:

```bash
# Run all tests for a server
cd overmind  # or cd sentiment
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_server_overmind

# Run specific test file
uv run pytest tests/test_overmind_server.py -v

# For overmind integration tests
cd overmind/test_environment
./run_tests.sh
```

### Building and Installation

```bash
# Build a server package
cd overmind  # or cd sentiment
uv build

# Install for local development
uv sync --dev

# Test the server locally
uv run mcp-server-overmind  # or mcp-server-sentiment
```

### Running Servers

Each server can be run directly via uvx or as a development install:

```bash
# Using uvx (production-like)
uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind

# Using local development install
cd overmind
uv run mcp-server-overmind
```

## Architecture Patterns

### FastMCP Server Pattern

All servers follow the FastMCP pattern:
1. Initialize with `mcp = FastMCP("server-name")`
2. Define tools using the `@mcp.tool()` decorator
3. Use a Manager class to encapsulate business logic
4. Tools are async functions that return structured data

### Manager Classes

Each server implements a Manager class that handles:
- **Initialization**: Setting up required resources (API clients, file paths, etc.)
- **Business Logic**: Core operations separated from MCP tool definitions
- **Error Handling**: Returning structured error responses
- **Async Operations**: Using `asyncio` for I/O operations

Example from overmind/src/mcp_server_overmind/server.py:712:
```python
class OvermindManager:
    def __init__(self, procfile_path: Optional[str] = None, working_dir: Optional[str] = None):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.socket_path = self.working_dir / ".overmind.sock"

    async def run_command(self, command: List[str]) -> Dict[str, Any]:
        # Execute commands with proper error handling
```

### Tool Response Pattern

Tools return structured responses, typically JSON strings or dictionaries:
- Success cases: Include relevant data and success indicators
- Error cases: Include error messages and failure indicators
- Consistent structure across all tools in a server

## Server-Specific Notes

### Overmind Server

**Key Concept**: Socket-based detection - The server detects running Overmind instances by checking for `.overmind.sock` in the working directory, not by parsing process lists.

**Working Directory Context**: All Overmind commands are executed with proper `cwd` set via the `OvermindManager.working_dir` attribute. This ensures commands work correctly regardless of where the MCP server itself is running.

**Background Process Handling**: The `start_overmind_background()` method starts Overmind asynchronously and returns immediately, allowing the server to remain responsive.

### Sentiment Server

**API Key Management**: The server supports both environment variable (`NEWS_API_KEY`) and direct parameter passing for the API key. Tools check environment first, then fall back to parameters.

**NLTK Dependency**: The `SentimentManager._ensure_vader_lexicon_is_downloaded()` method automatically downloads required NLTK data on first use.

**Async News Fetching**: Uses `asyncio.to_thread()` to run synchronous NewsAPI calls in a thread pool, maintaining async compatibility.

## Package Configuration

Each server's `pyproject.toml` follows these conventions:

- **Package name**: `mcp-server-{name}` (with hyphens)
- **Module name**: `mcp_server_{name}` (with underscores)
- **Entry point**: `mcp-server-{name} = "mcp_server_{name}.server:main"`
- **Build system**: hatchling
- **Minimum Python**: 3.10
- **Core dependency**: `mcp>=1.2.0`
- **Dev dependencies**: pytest, pytest-asyncio

## Adding New Servers

When creating a new server:

1. Create directory structure matching existing servers
2. Implement a Manager class for business logic
3. Use FastMCP decorators for tool definitions
4. Add comprehensive tests including both unit and integration tests
5. Document tools in the server's README.md
6. Update the main README.md with server details
7. Ensure proper async/await patterns throughout
8. Follow the established naming conventions

## Installation Methods

Servers can be installed via:
- **uvx with Git**: `uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind`
- **Local development**: `uv sync --dev` in server directory
- **Claude Desktop**: Add to `mcpServers` configuration in Claude Desktop settings

## Dependencies

- **uv**: Package manager and build tool (required for development)
- **direnv**: Optional, but .envrc files are provided for automatic venv activation
- **Python 3.10+**: Minimum required version
- **FastMCP**: Core framework for all servers (via mcp package)
