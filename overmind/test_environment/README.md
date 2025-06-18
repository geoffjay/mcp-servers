# Test Environment for MCP Overmind Server

This directory contains a test environment for the MCP Overmind server with sample processes and testing utilities.

## Files

- `Procfile` - Sample Procfile defining 4 test processes
- `test_web.py` - Simulates a web server with periodic output
- `test_worker.py` - Simulates a background worker processing jobs
- `test_logger.py` - Simulates a logging service with various log levels
- `test_counter.py` - Simple counter that outputs incrementing numbers
- `test_server.py` - Test script to verify MCP server functionality
- `run_tests.sh` - Shell script to run all tests

## Test Processes

### Web Server (`test_web.py`)
- Simulates a web server listening on port 8000
- Logs request handling with timestamps
- Outputs every 5-10 seconds

### Worker (`test_worker.py`)
- Simulates background job processing
- Shows job progress and completion
- Random processing times between 2-8 seconds

### Logger (`test_logger.py`)
- Generates log entries with different levels (INFO, DEBUG, WARN, ERROR)
- Simulates various system components
- Outputs every 1-4 seconds

### Counter (`test_counter.py`)
- Simple incrementing counter
- Shows milestones and periodic maintenance
- Outputs every second

## Usage

### Prerequisites

1. Install Overmind and tmux:
   ```bash
   # On macOS
   brew install overmind tmux
   
   # On Ubuntu/Debian
   sudo apt-get install tmux
   # Install overmind from GitHub releases
   ```

2. Make sure Python 3.10+ is available

### Running Tests

1. **Basic functionality test:**
   ```bash
   cd overmind/test_environment
   python test_server.py
   ```

2. **Manual testing with Overmind:**
   ```bash
   cd overmind/test_environment
   overmind start
   ```
   
   In another terminal:
   ```bash
   overmind status
   overmind connect web    # Connect to web process
   overmind stop worker    # Stop just the worker
   overmind quit           # Stop all processes
   ```

3. **Testing with MCP server:**
   ```bash
   cd overmind
   uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind
   ```

### Expected Output

When running the test processes, you should see output like:

```
[WEB:8000] 2025-01-03 10:30:15 - Server listening on port 8000
[WORKER] 2025-01-03 10:30:16 - Processing job #1 (estimated 5s)
[LOGGER] 2025-01-03 10:30:17 [INFO] auth: User logged in
[COUNTER] 2025-01-03 10:30:18 - Count: 1
```

### Troubleshooting

1. **Overmind not found:** Make sure Overmind is installed and in your PATH
2. **tmux not found:** Install tmux package
3. **Processes not starting:** Check that Python files are executable (`chmod +x *.py`)
4. **MCP server issues:** Ensure the server is built and the working directory is correct

### Testing Different Scenarios

1. **Test with custom Procfile location:**
   - Copy Procfile to different location
   - Use `overmind_start(procfile="/path/to/Procfile")`

2. **Test with custom working directory:**
   - Use `overmind_start(working_dir="/path/to/dir")`

3. **Test process management:**
   - Start all processes
   - Stop individual processes
   - Restart specific processes
   - Check status and logs

This test environment helps verify that the MCP Overmind server can properly:
- Detect Procfiles in various locations
- Start and manage multiple processes
- Handle process lifecycle operations
- Provide meaningful output and error messages 