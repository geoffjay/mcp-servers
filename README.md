# MCP Servers Collection

A collection of Model Context Protocol (MCP) servers for enhancing AI tooling capabilities. These servers provide structured interfaces for AI assistants to interact with various development tools and services.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that enables AI assistants to securely connect to external data sources and tools. MCP servers expose specific functionality as tools that AI assistants can discover and use.

## Available Servers

### 🔄 Overmind Server

**Path**: `overmind/`  
**Purpose**: Process management for Procfile-based applications using [Overmind](https://github.com/DarthSim/overmind)

**Installation**:

```bash
uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind
```

**Key Features**:

- Start, stop, and restart processes defined in Procfiles
- Monitor process status and health
- Execute commands within the Overmind environment
- Socket-based detection of running instances
- Support for custom Procfile locations and formations

**Tools Available**:

- `overmind_start` - Start Overmind with optional configuration
- `overmind_stop` - Stop specific processes or all processes
- `overmind_restart` - Restart specified processes
- `overmind_status` - Get status of all processes
- `overmind_quit` - Gracefully quit Overmind
- `overmind_kill` - Forcefully kill all processes
- `overmind_run` - Run commands in Overmind environment
- `overmind_connect` - Get connection instructions for processes
- `overmind_is_running` - Check if Overmind is running
- `overmind_check_procfile` - Validate Procfile existence and contents
- `overmind_find_procfiles` - Find all Procfiles in a directory tree

**Requirements**: Overmind and tmux must be installed on the system.

**Testing**: The `overmind/test_environment/` directory contains a complete test setup with sample processes and testing utilities. Run `./overmind/test_environment/run_tests.sh` for comprehensive testing.

## Quick Start

### Using with Claude Desktop

Add any of these servers to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "overmind": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind",
        "mcp-server-overmind"
      ]
    }
  }
}
```

### Using with Other MCP Clients

Each server can be executed directly:

```bash
# Overmind server
uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind
```

## Development

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management
- [direnv](https://direnv.net/) (optional, for automatic environment activation)

### Project Structure

```
mcp-servers/
├── README.md                 # This file
├── overmind/                 # Overmind process manager server
│   ├── src/mcp_server_overmind/
│   ├── tests/
│   ├── pyproject.toml
│   ├── .envrc
│   └── README.md
└── [future-servers]/         # Additional servers will be added here
```

### Adding a New Server

1. Create a new directory for your server
2. Set up the project structure:
   ```
   your-server/
   ├── src/mcp_server_yourname/
   │   ├── __init__.py
   │   └── server.py
   ├── tests/
   ├── pyproject.toml
   ├── .envrc
   └── README.md
   ```
3. Configure `pyproject.toml` with:
   - Package name: `mcp-server-yourname`
   - Entry point: `mcp-server-yourname = "mcp_server_yourname.server:main"`
   - Dependencies including `mcp>=1.2.0`
4. Implement your server using the FastMCP framework
5. Add comprehensive tests
6. Document your server in its README.md
7. Update this main README.md to include your server

### Running Tests

Each server includes its own test suite:

```bash
cd your-server-directory
uv run --extra dev pytest tests/ -v
```

### Building and Testing Locally

```bash
cd your-server-directory
uv build
uv run your-entry-point
```

## Contributing

We welcome contributions! Please:

1. Follow the existing project structure and patterns
2. Include comprehensive tests for new functionality
3. Add thorough documentation
4. Ensure your server follows MCP best practices
5. Update this README when adding new servers

### Code Style

- Use Python type hints throughout
- Follow async/await patterns for I/O operations
- Include docstrings for all public functions
- Use descriptive tool names and clear parameter documentation

### Testing Requirements

- Achieve high test coverage (aim for >90%)
- Include both unit and integration tests
- Mock external dependencies appropriately
- Test both success and failure scenarios

## License

This project is licensed under the MIT License. See individual server directories for specific license information.

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Framework](https://github.com/modelcontextprotocol/python-sdk/tree/main/src/mcp/server/fastmcp)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/desktop)

## Support

For issues with specific servers, please refer to their individual README files. For general project issues or questions, please open an issue in this repository.

---

## Server Status

| Server   | Status    | Version | Last Updated |
| -------- | --------- | ------- | ------------ |
| overmind | ✅ Stable | 0.1.0   | January 2025 |

## Roadmap

Future servers under consideration:

- Development environment setup
- Audio processing (MIDI/OSC)
