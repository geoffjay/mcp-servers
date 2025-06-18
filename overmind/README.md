# MCP Server for Overmind

An MCP (Model Context Protocol) server that provides tools for managing [Overmind](https://github.com/DarthSim/overmind) processes. This server allows AI assistants to interact with Overmind-managed development environments through a standardized interface.

## Overview

Overmind is a process manager for Procfile-based applications, built on top of tmux. This MCP server exposes all major Overmind functionality as tools that can be used by AI assistants and other MCP clients.

## Features

- **Process Management**: Start, stop, restart, and monitor processes
- **Status Monitoring**: Check process status and Overmind running state
- **Environment Execution**: Run commands within the Overmind environment
- **Procfile Support**: Check for and validate Procfile configurations
- **Socket Detection**: Automatically detect running Overmind instances
- **Custom Paths**: Support for custom Procfile and working directory paths

## Installation

### Using uvx (Recommended)

```bash
uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind
```

### Development Installation

```bash
git clone https://github.com/geoffjay/mcp-servers.git
cd mcp-servers/overmind
uv sync --dev
```

## Usage

### As an MCP Server

The server can be used with any MCP-compatible client. For Claude Desktop, add the following to your configuration:

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

### Available Tools

#### Process Management

- **`overmind_start`**: Start Overmind with optional configuration
  - `procfile`: Path to Procfile (optional)
  - `working_dir`: Working directory (optional)
  - `formation`: Process formation (e.g., "web=1,worker=2")
  - `port`: Starting port number
  - `timeout`: Process startup timeout
  - `auto_restart`: Enable auto-restart

- **`overmind_stop`**: Stop specific processes or all processes
  - `processes`: Comma-separated process names (optional)

- **`overmind_restart`**: Restart specific processes
  - `processes`: Comma-separated process names (required)

- **`overmind_quit`**: Gracefully quit Overmind

- **`overmind_kill`**: Forcefully kill all processes

#### Monitoring and Status

- **`overmind_status`**: Get status of all processes

- **`overmind_is_running`**: Check if Overmind is running
  - `working_dir`: Directory to check (optional)

- **`overmind_echo`**: Echo output from master Overmind instance

#### Environment and Execution

- **`overmind_run`**: Run command in Overmind environment
  - `command`: Command to execute (required)
  - `process_name`: Process context (optional)

- **`overmind_connect`**: Get connection instructions for a process
  - `process_name`: Process to connect to (required)

#### Configuration

- **`overmind_check_procfile`**: Check Procfile existence and contents
  - `path`: Directory path to check (optional)

## Examples

### Starting a Development Environment

```python
# Check if Procfile exists
result = await overmind_check_procfile()

# Start Overmind with custom formation
result = await overmind_start(
    formation="web=1,worker=2",
    port=3000,
    auto_restart=True
)

# Check status
status = await overmind_status()
```

### Managing Processes

```python
# Restart specific processes
await overmind_restart("web,worker")

# Stop a specific process
await overmind_stop("worker")

# Run a command in the environment
await overmind_run("rails console", "web")
```

### Monitoring

```python
# Check if Overmind is running
running = await overmind_is_running()

# Get process status
status = await overmind_status()

# Echo recent output
output = await overmind_echo()
```

## Architecture

### OvermindManager Class

The core `OvermindManager` class handles:
- Process state detection via socket file monitoring
- Command execution with proper working directory context
- Error handling and response formatting

### Socket-based Detection

The server detects running Overmind instances by checking for the `.overmind.sock` file in the working directory. This approach is reliable and doesn't require parsing process lists or making network connections.

### Command Execution

All Overmind commands are executed as subprocesses with:
- Proper working directory context
- Async execution for non-blocking operation
- Comprehensive error handling
- Structured response formatting

## Development

### Setup

```bash
# Clone and setup development environment
git clone https://github.com/geoffjay/mcp-servers.git
cd mcp-servers/overmind

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

# Run with coverage
uv run pytest --cov=src/mcp_server_overmind

# Run specific test file
uv run pytest tests/test_overmind_server.py
```

### Project Structure

```
overmind/
├── src/
│   └── mcp_server_overmind/
│       ├── __init__.py
│       └── server.py          # Main server implementation
├── tests/
│   ├── __init__.py
│   └── test_overmind_server.py  # Comprehensive tests
├── .envrc                     # direnv configuration
├── .python-version           # Python version specification
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## Requirements

- Python 3.10 or higher
- [Overmind](https://github.com/DarthSim/overmind) installed and available in PATH
- [tmux](https://github.com/tmux/tmux) (required by Overmind)

## Troubleshooting

### Common Issues

1. **"Overmind command not found"**
   - Ensure Overmind is installed and in your PATH
   - Check installation: `which overmind`

2. **"No Procfile found"**
   - Ensure you're in a directory with a Procfile
   - Use the `procfile` parameter to specify a custom path

3. **"Overmind is not running"**
   - Check if processes are actually running: `overmind status`
   - Look for the `.overmind.sock` file in your project directory

4. **Socket permission issues**
   - Ensure the working directory is writable
   - Check for stale socket files from previous runs

### Debugging

Enable debug logging by setting the environment variable:
```bash
export MCP_LOG_LEVEL=debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See the parent repository for full license details.

## Related

- [Overmind](https://github.com/DarthSim/overmind) - The process manager this server interfaces with
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
- [tmux](https://github.com/tmux/tmux) - Terminal multiplexer used by Overmind
