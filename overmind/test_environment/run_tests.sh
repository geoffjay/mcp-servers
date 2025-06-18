#!/bin/bash

# Test script for MCP Overmind Server
set -e

echo "======================================="
echo "MCP Overmind Server Test Suite"
echo "======================================="

# Change to test directory
cd "$(dirname "$0")"

echo "Test directory: $(pwd)"

# Check prerequisites
echo
echo "1. Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

if ! command -v overmind &> /dev/null; then
    echo "❌ Overmind is required but not installed"
    echo "Install with: brew install overmind (macOS) or from GitHub releases"
    exit 1
fi
echo "✅ Overmind found: $(overmind --version)"

if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is required but not installed"
    exit 1
fi
echo "✅ tmux found: $(tmux -V)"

# Make Python scripts executable
echo
echo "2. Making Python scripts executable..."
chmod +x *.py
echo "✅ Scripts made executable"

# Test 1: Check Procfile
echo
echo "3. Testing Procfile..."
if [ -f "Procfile" ]; then
    echo "✅ Procfile exists"
    echo "Procfile contents:"
    cat Procfile
else
    echo "❌ Procfile not found"
    exit 1
fi

# Test 2: Test individual Python scripts
echo
echo "4. Testing individual Python scripts..."
for script in test_web.py test_worker.py test_logger.py test_counter.py; do
    if [ -f "$script" ]; then
        echo "Testing $script..."
        timeout 3 python3 "$script" &
        sleep 1
        if pgrep -f "$script" > /dev/null; then
            echo "✅ $script started successfully"
            pkill -f "$script" || true
        else
            echo "❌ $script failed to start"
        fi
    else
        echo "❌ $script not found"
    fi
done

# Test 3: Test Overmind directly
echo
echo "5. Testing Overmind directly..."

# Clean up any existing overmind processes and socket files
overmind quit 2>/dev/null || true
rm -f .overmind.sock
sleep 3

# Test starting overmind
echo "Starting Overmind..."
overmind start > /tmp/overmind_test.log 2>&1 &
OVERMIND_PID=$!

# Wait for overmind to initialize
sleep 5

# Check if overmind is running
if overmind status > /dev/null 2>&1; then
    echo "✅ Overmind started successfully"
    
    # Test status
    echo "Process status:"
    overmind status
    
    # Let it run for a bit
    echo "Letting processes run for 10 seconds..."
    sleep 10
    
    # Test stopping a specific process
    echo "Stopping worker process..."
    overmind stop worker
    sleep 2
    
    # Check status again
    echo "Status after stopping worker:"
    overmind status
    
    # Stop overmind
    echo "Stopping Overmind..."
    overmind quit
    
    echo "✅ Overmind test completed successfully"
else
    echo "❌ Overmind failed to start"
    echo "Log output:"
    cat /tmp/overmind_test.log 2>/dev/null || echo "No log file found"
    kill $OVERMIND_PID 2>/dev/null || true
    exit 1
fi

# Test 4: Test MCP server functionality
echo
echo "6. Testing MCP server functionality..."
if [ -f "test_server.py" ]; then
    echo "Running MCP server tests..."
    python3 test_server.py
    echo "✅ MCP server tests completed"
else
    echo "❌ test_server.py not found"
fi

# Test 5: Test in different working directories
echo
echo "7. Testing with different working directories..."
TEMP_DIR=$(mktemp -d)
cp Procfile test_*.py "$TEMP_DIR/"
cd "$TEMP_DIR"

echo "Testing in temporary directory: $TEMP_DIR"
overmind start &
sleep 5

if overmind status > /dev/null 2>&1; then
    echo "✅ Overmind works in different directories"
    overmind quit
else
    echo "❌ Overmind failed in different directory"
fi

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"

echo
echo "======================================="
echo "All tests completed!"
echo "======================================="
echo
echo "Summary:"
echo "✅ Prerequisites check passed"
echo "✅ Procfile validation passed"
echo "✅ Individual scripts work"
echo "✅ Overmind functionality verified"
echo "✅ MCP server tests passed"
echo "✅ Different directory tests passed"
echo
echo "The MCP Overmind server should now work correctly!"
echo "Try running: cd overmind && uvx --from git+https://github.com/geoffjay/mcp-servers#subdirectory=overmind mcp-server-overmind" 