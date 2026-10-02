"""MCP server for managing Overmind processes."""

import asyncio
import glob
import json
import os
import re
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from mcp.server.mcpserver import MCPServer

# Initialize MCP server
mcp = MCPServer("overmind")

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

    async def run_command_with_timeout(self, command: List[str], timeout: float = 5.0) -> Dict[str, Any]:
        """Run a command and capture output for a specified timeout period.

        This is useful for commands that stream continuously (like overmind echo)
        where we want to capture some output but not wait forever.

        Args:
            command: Command to execute
            timeout: How long to wait for output in seconds
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            output_lines = []
            error_lines = []

            try:
                # Read output for the specified timeout period
                async with asyncio.timeout(timeout):
                    while True:
                        line = await process.stdout.readline()
                        if not line:
                            break
                        output_lines.append(line.decode('utf-8'))
            except asyncio.TimeoutError:
                # Timeout is expected for streaming commands
                pass

            # Terminate the process since we're done reading
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

            # Try to read any stderr that was captured
            try:
                stderr_data = await asyncio.wait_for(process.stderr.read(), timeout=0.5)
                if stderr_data:
                    error_lines.append(stderr_data.decode('utf-8'))
            except asyncio.TimeoutError:
                pass

            stdout_text = ''.join(output_lines).strip()
            stderr_text = ''.join(error_lines).strip()

            return {
                "success": True if stdout_text or not stderr_text else False,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": 0 if stdout_text else -1
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

    def _get_tmux_session_name(self) -> str:
        """Get the tmux session name based on the working directory."""
        # Overmind uses the directory name as the session ID, with underscores converted to hyphens
        return self.working_dir.name.replace('_', '-')

    async def _find_tmux_socket(self) -> Optional[str]:
        """Find the tmux socket name for this overmind instance.

        Returns the socket name (without path) or None if not found.
        """
        session_name = self._get_tmux_session_name()

        # Try common tmux socket directories
        possible_dirs = [
            Path(f"/tmp/tmux-{os.getuid()}"),
            Path(f"/private/tmp/tmux-{os.getuid()}"),
            Path(tempfile.gettempdir()) / f"tmux-{os.getuid()}",
        ]

        socket_files = []
        for tmux_dir in possible_dirs:
            if tmux_dir.exists():
                # Look for sockets matching overmind-{dirname}-*
                pattern = f"overmind-{session_name}-*"
                socket_files.extend(list(tmux_dir.glob(pattern)))

        if not socket_files:
            return None

        # Try each socket to find one with an active session
        for socket_file in socket_files:
            socket_name = socket_file.name.rstrip('=')
            try:
                # Check if this socket has our session
                process = await asyncio.create_subprocess_exec(
                    "tmux", "-L", socket_name, "list-sessions",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, "TMUX": ""}  # Unset TMUX to avoid nesting issues
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    output = stdout.decode('utf-8')
                    if session_name in output:
                        return socket_name
            except Exception:
                continue

        return None

    async def get_process_list(self) -> List[str]:
        """Get list of process names from tmux panes.

        Returns empty list if overmind is not running or tmux session not found.
        """
        if not self.is_running():
            return []

        socket_name = await self._find_tmux_socket()
        if not socket_name:
            return []

        session_name = self._get_tmux_session_name()

        try:
            process = await asyncio.create_subprocess_exec(
                "tmux", "-L", socket_name, "list-panes", "-a",
                "-F", "#{window_name}",
                "-t", session_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "TMUX": ""}
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                processes = stdout.decode('utf-8').strip().split('\n')
                return [p for p in processes if p]

            return []
        except Exception:
            return []

    async def capture_process_logs(self, process_name: str, num_lines: int = 100) -> Dict[str, Any]:
        """Capture logs from a specific process's tmux pane.

        Args:
            process_name: Name of the process to capture logs from
            num_lines: Number of lines to capture from scrollback (default: 100)

        Returns:
            Dict with success, logs, and error information
        """
        if not self.is_running():
            return {
                "success": False,
                "logs": "",
                "error": "Overmind is not running"
            }

        socket_name = await self._find_tmux_socket()
        if not socket_name:
            return {
                "success": False,
                "logs": "",
                "error": "Could not find tmux session for overmind"
            }

        session_name = self._get_tmux_session_name()

        try:
            # Capture pane output
            process = await asyncio.create_subprocess_exec(
                "tmux", "-L", socket_name, "capture-pane", "-p",
                "-t", f"{session_name}:{process_name}",
                "-S", f"-{num_lines}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "TMUX": ""}
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logs = stdout.decode('utf-8')
                return {
                    "success": True,
                    "logs": logs,
                    "error": ""
                }
            else:
                error_msg = stderr.decode('utf-8').strip()
                return {
                    "success": False,
                    "logs": "",
                    "error": error_msg or f"Process '{process_name}' not found"
                }
        except Exception as e:
            return {
                "success": False,
                "logs": "",
                "error": f"Error capturing logs: {str(e)}"
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
async def overmind_echo(timeout: float = 5.0) -> str:
    """Echo output from master Overmind instance.

    Captures streaming output from all processes for the specified timeout period.

    Args:
        timeout: How many seconds to capture output (default: 5.0)
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running."

    command = ["overmind", "echo"]
    result = await overmind_manager.run_command_with_timeout(command, timeout)

    if result["success"]:
        if result['stdout']:
            return f"Overmind output (last {timeout}s):\n{result['stdout']}"
        else:
            return "No output received. Overmind may not be running in daemon mode or there's no recent activity."
    else:
        return f"Failed to echo output: {result['stderr']}"

@mcp.tool()
async def overmind_list_processes() -> str:
    """List all processes managed by Overmind.

    Returns a list of process names that can be used with overmind_logs.
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running."

    processes = await overmind_manager.get_process_list()

    if not processes:
        return "Could not retrieve process list. Overmind may not be using tmux or the session is not accessible."

    return f"Running processes ({len(processes)}):\n" + "\n".join(f"  - {p}" for p in processes)


@mcp.tool()
async def overmind_logs(process_name: str, num_lines: int = 100) -> str:
    """Get logs from a specific Overmind process.

    Captures output from the tmux pane for the specified process.

    Args:
        process_name: Name of the process to get logs from (e.g., 'web', 'worker')
        num_lines: Number of lines to retrieve from scrollback (default: 100)
    """
    if not overmind_manager.is_running():
        return "Overmind is not currently running."

    # Validate num_lines
    if num_lines < 1:
        return "num_lines must be at least 1"
    if num_lines > 10000:
        return "num_lines cannot exceed 10000 (requested too many lines)"

    result = await overmind_manager.capture_process_logs(process_name, num_lines)

    if result["success"]:
        if result["logs"]:
            return f"Logs for process '{process_name}' (last {num_lines} lines):\n{result['logs']}"
        else:
            return f"No logs available for process '{process_name}'"
    else:
        error = result["error"]
        # Provide helpful suggestions
        if "not found" in error.lower() or "can't find" in error.lower():
            # Try to list available processes
            processes = await overmind_manager.get_process_list()
            if processes:
                return f"Process '{process_name}' not found.\n\nAvailable processes:\n" + "\n".join(f"  - {p}" for p in processes)
            else:
                return f"Process '{process_name}' not found. Use overmind_list_processes to see available processes."
        return f"Failed to get logs: {error}"


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