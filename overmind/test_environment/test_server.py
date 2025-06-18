#!/usr/bin/env python3
"""Test script for the MCP Overmind server."""

import asyncio
import os
import sys
from pathlib import Path

# Add the server module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_overmind.server import (
    OvermindManager,
    overmind_start,
    overmind_stop,
    overmind_status,
    overmind_check_procfile,
    overmind_is_running,
    overmind_quit
)

async def test_overmind_server():
    """Test the overmind server functionality."""
    print("=" * 60)
    print("Testing MCP Overmind Server")
    print("=" * 60)
    
    # Get the test environment directory
    test_dir = Path(__file__).parent
    print(f"Test directory: {test_dir}")
    
    # Test 1: Check if Procfile exists
    print("\n1. Checking for Procfile...")
    result = await overmind_check_procfile(str(test_dir))
    print(result)
    
    # Test 2: Check if Overmind is running
    print("\n2. Checking if Overmind is running...")
    result = await overmind_is_running(str(test_dir))
    print(result)
    
    # Test 3: Try to start Overmind
    print("\n3. Starting Overmind...")
    result = await overmind_start(
        procfile=str(test_dir / "Procfile"),
        working_dir=str(test_dir)
    )
    print(result)
    
    # Wait a bit for processes to initialize
    if "successfully" in result:
        print("\n4. Waiting for processes to initialize...")
        await asyncio.sleep(3)
        
        # Test 4: Check status
        print("\n5. Checking process status...")
        result = await overmind_status()
        print(result)
        
        # Test 5: Let it run for a bit to see output
        print("\n6. Letting processes run for 10 seconds...")
        await asyncio.sleep(10)
        
        # Test 6: Check status again
        print("\n7. Checking process status again...")
        result = await overmind_status()
        print(result)
        
        # Test 7: Stop Overmind
        print("\n8. Stopping Overmind...")
        result = await overmind_quit()
        print(result)
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

async def test_manager_directly():
    """Test the OvermindManager directly."""
    print("\n" + "=" * 60)
    print("Testing OvermindManager directly")
    print("=" * 60)
    
    test_dir = Path(__file__).parent
    manager = OvermindManager(
        procfile_path=str(test_dir / "Procfile"),
        working_dir=str(test_dir)
    )
    
    print(f"Working directory: {manager.working_dir}")
    print(f"Procfile path: {manager.procfile_path}")
    print(f"Socket path: {manager.socket_path}")
    print(f"Procfile exists: {manager.procfile_path.exists()}")
    print(f"Is running: {manager.is_running()}")
    
    # Test a simple command
    print("\nTesting simple command (ls)...")
    result = await manager.run_command(["ls", "-la"])
    print(f"Success: {result['success']}")
    print(f"Return code: {result['return_code']}")
    if result['stdout']:
        print(f"Output:\n{result['stdout']}")
    if result['stderr']:
        print(f"Error:\n{result['stderr']}")

if __name__ == "__main__":
    # Change to the test directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    print("Running OvermindManager tests...")
    asyncio.run(test_manager_directly())
    
    print("\nRunning full server tests...")
    asyncio.run(test_overmind_server()) 