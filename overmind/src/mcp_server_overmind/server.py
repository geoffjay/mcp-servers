"""MCP server for managing Overmind processes."""

import asyncio
import json
import os
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("overmind")

class OvermindManager:
    """Manager for Overmind processes and operations."""
    
    def __init__(self, procfile_path: Optional[str] = None, working_dir: Optional[str] = None):
        """Initialize the Overmind manager.
        
        Args:
            procfile_path: Path to the Procfile (defaults to ./Procfile)
            working_dir: Working directory for overmind operations (defaults to current dir)
        """
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.procfile_path = Path(procfile_path) if procfile_path else self.working_dir / "Procfile"
        self.socket_path = self.working_dir / ".overmind.sock"
    
    def is_running(self) -> bool:
        """Check if Overmind is currently running by checking for the socket file."""
        return self.socket_path.exists()
    
    async def run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run an overmind command and return the result."""
        try:
            # Change to working directory for the command
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8').strip() if stdout else "",
                "stderr": stderr.decode('utf-8').strip() if stderr else "",
                "return_code": process.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "return_code": -1
            }

    async def start_overmind_background(self, command: List[str]) -> Dict[str, Any]:
        """Start overmind in the background and return immediately."""
        try:
            # Start the process but don't wait for it to complete
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Give it a moment to start and check if it fails immediately
            await asyncio.sleep(2)
            
            # Check if the process is still running
            if process.returncode is None:
                # Process is still running, which is good for overmind start
                return {
                    "success": True,
                    "stdout": f"Overmind started in background with PID {process.pid}",
                    "stderr": "",
                    "return_code": 0,
                    "process": process
                }
            else:
                # Process exited quickly, probably an error
                stdout, stderr = await process.communicate()
                return {
                    "success": False,
                    "stdout": stdout.decode('utf-8').strip() if stdout else "",
                    "stderr": stderr.decode('utf-8').strip() if stderr else "",
                    "return_code": process.returncode
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error starting overmind: {str(e)}",
                                 "return_code": -1
             }

# Global manager instance
overmind_manager = OvermindManager()

@mcp.tool()
async def overmind_start(
    procfile: Optional[str] = None,
    working_dir: Optional[str] = None,
    formation: Optional[str] = None,
    port: Optional[int] = None,
    timeout: Optional[int] = None,
    auto_restart: bool = False
) -> str:
    """Start Overmind with the specified Procfile.
    
    Args:
        procfile: Path to the Procfile (optional, defaults to ./Procfile)
        working_dir: Working directory to run overmind in (optional)
        formation: Process formation (e.g., 'web=1,worker=2')
        port: Port number to start from
        timeout: Timeout for process startup in seconds
        auto_restart: Enable auto-restart of failed processes
    """
    global overmind_manager
    
    # Update manager if working directory or procfile specified
    if working_dir or procfile:
        overmind_manager = OvermindManager(procfile, working_dir)
    
    if overmind_manager.is_running():
        return f"Overmind is already running in {overmind_manager.working_dir}."
    
    # More detailed Procfile detection and error reporting
    if not overmind_manager.procfile_path.exists():
        # Try to provide helpful suggestions
        error_msg = f"Procfile not found at {overmind_manager.procfile_path}."
        
        # Check if there's a Procfile in common locations
        suggestions = []
        
        # Check current directory
        current_procfile = Path.cwd() / "Procfile"
        if current_procfile.exists() and current_procfile != overmind_manager.procfile_path:
            suggestions.append(f"Found Procfile at {current_procfile}")
        
        # Check parent directories
        for parent in Path.cwd().parents[:3]:  # Check up to 3 parent directories
            parent_procfile = parent / "Procfile"
            if parent_procfile.exists():
                suggestions.append(f"Found Procfile at {parent_procfile}")
                break
        
        if suggestions:
            error_msg += f"\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
            error_msg += f"\n\nUse overmind_start(procfile='path/to/Procfile') or overmind_start(working_dir='path/to/directory')"
        
        return error_msg
    
    command = ["overmind", "start"]
    
    if procfile:
        command.extend(["-f", procfile])
    if formation:
        command.extend(["-c", formation])
    if port:
        command.extend(["-p", str(port)])
    if timeout:
        command.extend(["-t", str(timeout)])
    if auto_restart:
        command.append("-r")
    
    # Use the background start method for overmind start
    result = await overmind_manager.start_overmind_background(command)
    
    if result["success"]:
        # Wait a bit more and check if it's actually running
        await asyncio.sleep(3)
        if overmind_manager.is_running():
            return f"Overmind started successfully and is running.\n{result['stdout']}"
        else:
            return f"Overmind appeared to start but is not running. Check for errors."
    else:
        return f"Failed to start Overmind: {result['stderr']}"

@mcp.tool()
async def overmind_stop(processes: Optional[str] = None) -> str:
    """Stop specified processes or interrupt all processes.
    
    Args:
        processes: Comma-separated list of process names to stop (optional, stops all if not specified)
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    command = ["overmind", "stop"]
    if processes:
        command.extend(processes.split(","))
    
    result = await overmind_manager.run_command(command)
    
    if result["success"]:
        return f"Processes stopped successfully.\n{result['stdout']}"
    else:
        return f"Failed to stop processes: {result['stderr']}"

@mcp.tool()
async def overmind_restart(processes: str) -> str:
    """Restart specified processes.
    
    Args:
        processes: Comma-separated list of process names to restart
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running. Use overmind_start first."
    
    command = ["overmind", "restart"] + processes.split(",")
    result = await overmind_manager.run_command(command)
    
    if result["success"]:
        return f"Processes restarted successfully.\n{result['stdout']}"
    else:
        return f"Failed to restart processes: {result['stderr']}"

@mcp.tool()
async def overmind_status() -> str:
    """Get the status of all processes."""
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    command = ["overmind", "status"]
    result = await overmind_manager.run_command(command)
    
    if result["success"]:
        return f"Process status:\n{result['stdout']}"
    else:
        return f"Failed to get process status: {result['stderr']}"

@mcp.tool()
async def overmind_connect(process_name: str) -> str:
    """Connect to a specific process (this will provide connection info since actual connection requires terminal).
    
    Args:
        process_name: Name of the process to connect to
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    return f"To connect to process '{process_name}', run the following command in your terminal:\n\novermind connect {process_name}\n\nThis will attach to the tmux session for that process."

@mcp.tool()
async def overmind_run(command: str, process_name: Optional[str] = None) -> str:
    """Run a command within the Overmind environment.
    
    Args:
        command: Command to run
        process_name: Optional process name context
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    cmd = ["overmind", "run"]
    if process_name:
        cmd.extend(["-p", process_name])
    cmd.append(command)
    
    result = await overmind_manager.run_command(cmd)
    
    if result["success"]:
        return f"Command executed successfully.\nOutput:\n{result['stdout']}"
    else:
        return f"Command failed: {result['stderr']}"

@mcp.tool()
async def overmind_quit() -> str:
    """Gracefully quit Overmind."""
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    command = ["overmind", "quit"]
    result = await overmind_manager.run_command(command)
    
    if result["success"]:
        return f"Overmind quit successfully.\n{result['stdout']}"
    else:
        return f"Failed to quit Overmind: {result['stderr']}"

@mcp.tool()
async def overmind_kill() -> str:
    """Forcefully kill all processes."""
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    command = ["overmind", "kill"]
    result = await overmind_manager.run_command(command)
    
    if result["success"]:
        return f"All processes killed.\n{result['stdout']}"
    else:
        return f"Failed to kill processes: {result['stderr']}"

@mcp.tool()
async def overmind_echo() -> str:
    """Echo output from master Overmind instance."""
    if not overmind_manager.is_running():
        return "Overmind is not currently running."
    
    command = ["overmind", "echo"]
    result = await overmind_manager.run_command(command)
    
    if result["success"]:
        return f"Overmind output:\n{result['stdout']}"
    else:
        return f"Failed to echo output: {result['stderr']}"

@mcp.tool()
async def overmind_check_procfile(path: Optional[str] = None) -> str:
    """Check if a Procfile exists and show its contents.
    
    Args:
        path: Path to check for Procfile (optional, defaults to current directory)
    """
    procfile_path = Path(path) / "Procfile" if path else overmind_manager.procfile_path
    
    if procfile_path.exists():
        try:
            content = procfile_path.read_text()
            return f"Procfile found at {procfile_path}:\n\n{content}"
        except Exception as e:
            return f"Procfile exists at {procfile_path} but couldn't read it: {str(e)}"
    else:
        return f"No Procfile found at {procfile_path}"

@mcp.tool()
async def overmind_find_procfiles(start_path: Optional[str] = None) -> str:
    """Find all Procfiles in the specified directory and its subdirectories.
    
    Args:
        start_path: Path to start searching from (optional, defaults to current directory)
    """
    search_path = Path(start_path) if start_path else Path.cwd()
    
    if not search_path.exists():
        return f"Search path does not exist: {search_path}"
    
    procfiles = []
    
    try:
        # Search current directory and up to 2 levels of subdirectories
        for procfile in search_path.rglob("Procfile"):
            try:
                # Limit depth to avoid searching too deep
                if len(procfile.parts) - len(search_path.parts) <= 2:
                    content_preview = procfile.read_text()[:200]  # First 200 chars
                    if len(content_preview) == 200:
                        content_preview += "..."
                    procfiles.append({
                        "path": str(procfile),
                        "size": procfile.stat().st_size,
                        "preview": content_preview
                    })
            except Exception as e:
                procfiles.append({
                    "path": str(procfile),
                    "error": str(e)
                })
    except Exception as e:
        return f"Error searching for Procfiles: {str(e)}"
    
    if not procfiles:
        return f"No Procfiles found in {search_path} or its subdirectories"
    
    result = f"Found {len(procfiles)} Procfile(s):\n\n"
    for i, pf in enumerate(procfiles, 1):
        result += f"{i}. {pf['path']}\n"
        if "error" in pf:
            result += f"   Error: {pf['error']}\n"
        else:
            result += f"   Size: {pf['size']} bytes\n"
            result += f"   Preview: {pf['preview']}\n"
        result += "\n"
    
    return result

@mcp.tool()
async def overmind_is_running(working_dir: Optional[str] = None) -> str:
    """Check if Overmind is currently running in the specified directory.
    
    Args:
        working_dir: Directory to check (optional, defaults to current directory)
    """
    if working_dir:
        temp_manager = OvermindManager(working_dir=working_dir)
        running = temp_manager.is_running()
        socket_path = temp_manager.socket_path
    else:
        running = overmind_manager.is_running()
        socket_path = overmind_manager.socket_path
    
    if running:
        return f"Overmind is running (socket found at {socket_path})"
    else:
        return f"Overmind is not running (no socket at {socket_path})"

def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main() 