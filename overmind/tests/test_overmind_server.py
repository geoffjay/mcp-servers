"""Tests for the MCP Overmind server."""

import asyncio
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_server_overmind.server import OvermindManager
from mcp_server_overmind.server import (
    overmind_start,
    overmind_stop,
    overmind_restart,
    overmind_status,
    overmind_connect,
    overmind_run,
    overmind_quit,
    overmind_kill,
    overmind_echo,
    overmind_check_procfile,
    overmind_find_procfiles,
    overmind_is_running,
)


class TestOvermindManager:
    """Test the OvermindManager class."""

    def test_init_default(self):
        """Test OvermindManager initialization with defaults."""
        manager = OvermindManager()
        assert manager.working_dir == Path.cwd()
        assert manager.procfile_path == Path.cwd() / "Procfile"
        assert manager.socket_path == Path.cwd() / ".overmind.sock"

    def test_init_with_paths(self):
        """Test OvermindManager initialization with custom paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            procfile_path = temp_path / "custom_procfile"
            
            manager = OvermindManager(
                procfile_path=str(procfile_path),
                working_dir=str(temp_path)
            )
            
            assert manager.working_dir == temp_path
            assert manager.procfile_path == procfile_path
            assert manager.socket_path == temp_path / ".overmind.sock"

    def test_is_running_true(self):
        """Test is_running when socket file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            socket_file = temp_path / ".overmind.sock"
            socket_file.touch()
            
            manager = OvermindManager(working_dir=str(temp_path))
            assert manager.is_running() is True

    def test_is_running_false(self):
        """Test is_running when socket file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = OvermindManager(working_dir=str(temp_path))
            assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_run_command_success(self):
        """Test successful command execution."""
        manager = OvermindManager()
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await manager.run_command(["echo", "test"])
            
            assert result["success"] is True
            assert result["stdout"] == "output"
            assert result["stderr"] == ""
            assert result["return_code"] == 0

    @pytest.mark.asyncio
    async def test_run_command_failure(self):
        """Test failed command execution."""
        manager = OvermindManager()
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"error message")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            result = await manager.run_command(["false"])
            
            assert result["success"] is False
            assert result["stdout"] == ""
            assert result["stderr"] == "error message"
            assert result["return_code"] == 1

    @pytest.mark.asyncio
    async def test_run_command_exception(self):
        """Test command execution with exception."""
        manager = OvermindManager()
        
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Test error")):
            result = await manager.run_command(["echo", "test"])
            
            assert result["success"] is False
            assert result["stdout"] == ""
            assert "Test error" in result["stderr"]
            assert result["return_code"] == -1


class TestOvermindTools:
    """Test the MCP tool functions."""

    @pytest.mark.asyncio
    async def test_overmind_start_already_running(self):
        """Test starting overmind when it's already running."""
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = True
            result = await overmind_start()
            assert "already running" in result

    @pytest.mark.asyncio
    async def test_overmind_start_no_procfile(self):
        """Test starting overmind when Procfile doesn't exist."""
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = False
            mock_manager.procfile_path.exists.return_value = False
            result = await overmind_start()
            assert "Procfile not found" in result

    @pytest.mark.asyncio
    async def test_overmind_start_success(self):
        """Test successful overmind start."""
        mock_result = {
            "success": True,
            "stdout": "Started successfully",
            "stderr": "",
            "return_code": 0
        }
        
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.side_effect = [False, True]  # First call: not running, second call: running
            mock_manager.procfile_path.exists.return_value = True
            mock_manager.start_overmind_background = AsyncMock(return_value=mock_result)
            result = await overmind_start()
            assert "successfully" in result
            assert "Started successfully" in result

    @pytest.mark.asyncio
    async def test_overmind_start_with_options(self):
        """Test overmind start with various options."""
        mock_result = {
            "success": True,
            "stdout": "Started with options",
            "stderr": "",
            "return_code": 0
        }
        
        with patch('mcp_server_overmind.server.OvermindManager') as mock_manager_class:
            # Create a mock instance
            mock_manager_instance = MagicMock()
            mock_manager_instance.is_running.side_effect = [False, True]  # First call: not running, second call: running
            mock_manager_instance.procfile_path.exists.return_value = True
            mock_manager_instance.start_overmind_background = AsyncMock(return_value=mock_result)
            mock_manager_class.return_value = mock_manager_instance
            
            await overmind_start(
                procfile="/custom/Procfile",
                formation="web=2,worker=1",
                port=5000,
                timeout=30,
                auto_restart=True
            )
            
            # Verify the manager was created with the right parameters
            mock_manager_class.assert_called_once_with("/custom/Procfile", None)
            
            # Verify the command was called
            mock_manager_instance.start_overmind_background.assert_called_once()
            called_command = mock_manager_instance.start_overmind_background.call_args[0][0]
            assert "overmind" in called_command
            assert "start" in called_command
            assert "-f" in called_command
            assert "/custom/Procfile" in called_command
            assert "-c" in called_command
            assert "web=2,worker=1" in called_command
            assert "-p" in called_command
            assert "5000" in called_command
            assert "-t" in called_command
            assert "30" in called_command
            assert "-r" in called_command

    @pytest.mark.asyncio
    async def test_overmind_stop_not_running(self):
        """Test stopping overmind when it's not running."""
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = False
            result = await overmind_stop()
            assert "not currently running" in result

    @pytest.mark.asyncio
    async def test_overmind_stop_success(self):
        """Test successful overmind stop."""
        mock_result = {
            "success": True,
            "stdout": "Stopped successfully",
            "stderr": "",
            "return_code": 0
        }
        
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = True
            mock_manager.run_command = AsyncMock(return_value=mock_result)
            result = await overmind_stop()
            assert "successfully" in result

    @pytest.mark.asyncio
    async def test_overmind_status_success(self):
        """Test getting overmind status."""
        mock_result = {
            "success": True,
            "stdout": "web: running\nworker: stopped",
            "stderr": "",
            "return_code": 0
        }
        
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = True
            mock_manager.run_command = AsyncMock(return_value=mock_result)
            result = await overmind_status()
            assert "Process status:" in result
            assert "web: running" in result

    @pytest.mark.asyncio
    async def test_overmind_connect(self):
        """Test overmind connect (provides instructions)."""
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = True
            result = await overmind_connect("web")
            assert "overmind connect web" in result
            assert "tmux session" in result

    @pytest.mark.asyncio
    async def test_overmind_run_success(self):
        """Test running a command in overmind environment."""
        mock_result = {
            "success": True,
            "stdout": "command output",
            "stderr": "",
            "return_code": 0
        }
        
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = True
            mock_manager.run_command = AsyncMock(return_value=mock_result)
            result = await overmind_run("ls -la", "web")
            
            # Verify command structure
            mock_manager.run_command.assert_called_once()
            called_command = mock_manager.run_command.call_args[0][0]
            assert "overmind" in called_command
            assert "run" in called_command
            assert "-p" in called_command
            assert "web" in called_command
            assert "ls -la" in called_command
            
            assert "successfully" in result
            assert "command output" in result

    @pytest.mark.asyncio
    async def test_overmind_check_procfile_exists(self):
        """Test checking for an existing Procfile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            procfile = temp_path / "Procfile"
            procfile.write_text("web: python app.py\nworker: python worker.py")
            
            result = await overmind_check_procfile(str(temp_path))
            assert "Procfile found" in result
            assert "web: python app.py" in result

    @pytest.mark.asyncio
    async def test_overmind_check_procfile_not_exists(self):
        """Test checking for a non-existent Procfile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await overmind_check_procfile(temp_dir)
            assert "No Procfile found" in result

    @pytest.mark.asyncio
    async def test_overmind_is_running_true(self):
        """Test checking if overmind is running (true case)."""
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = True
            mock_manager.socket_path = Path("/test/.overmind.sock")
            result = await overmind_is_running()
            assert "is running" in result
            assert "socket found" in result

    @pytest.mark.asyncio
    async def test_overmind_is_running_false(self):
        """Test checking if overmind is running (false case)."""
        with patch('mcp_server_overmind.server.overmind_manager') as mock_manager:
            mock_manager.is_running.return_value = False
            mock_manager.socket_path = Path("/test/.overmind.sock")
            result = await overmind_is_running()
            assert "is not running" in result
            assert "no socket" in result

    @pytest.mark.asyncio
    async def test_overmind_is_running_custom_dir(self):
        """Test checking if overmind is running in custom directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create socket file in temp directory
            socket_file = Path(temp_dir) / ".overmind.sock"
            socket_file.touch()
            
            result = await overmind_is_running(temp_dir)
            assert "is running" in result
            assert temp_dir in result

    @pytest.mark.asyncio
    async def test_overmind_find_procfiles(self):
        """Test finding Procfiles in directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test Procfiles
            (temp_path / "Procfile").write_text("web: python app.py")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "Procfile").write_text("worker: python worker.py")
            
            result = await overmind_find_procfiles(str(temp_path))
            assert "Found 2 Procfile(s)" in result
            assert "web: python app.py" in result
            assert "worker: python worker.py" in result

    @pytest.mark.asyncio
    async def test_overmind_find_procfiles_none_found(self):
        """Test finding Procfiles when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await overmind_find_procfiles(temp_dir)
            assert "No Procfiles found" in result 