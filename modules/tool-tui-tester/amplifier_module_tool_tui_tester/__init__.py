"""TUI Terminal Testing Tool for Amplifier.

Provides terminal session management for testing TUI applications:
- Spawn TUI apps in pseudo-terminals
- Send keystrokes and special keys
- Capture terminal state as text and screenshots
- Resize terminal to test responsive layouts
- Manage session lifecycle
"""

from pathlib import Path
from typing import Any

from amplifier_core.interfaces import Tool
from amplifier_core.models import ToolResult

from .keys import parse_keys
from .session_manager import SessionManager

# Re-export for external use
__all__ = ["TUITerminalTool", "SessionManager", "mount"]

# Global session manager (lazy initialization)
_session_manager: SessionManager | None = None
_session_manager_config: dict[str, Any] = {}


def _err(message: str) -> ToolResult:
    """Return a failed ToolResult with a properly structured error dict."""
    return ToolResult(success=False, error={"message": message})


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        cfg = _session_manager_config

        base_dir: Path | None = None
        raw_dir = cfg.get("session_dir")
        if raw_dir:
            base_dir = Path(str(raw_dir)).expanduser()

        _session_manager = SessionManager(
            base_dir=base_dir,
            session_timeout_minutes=int(cfg.get("session_timeout_minutes", 30)),
            default_font_size=int(cfg.get("default_font_size", 14)),
        )
    return _session_manager


class TUITerminalTool(Tool):
    """Tool for testing TUI applications via terminal emulation."""

    @property
    def name(self) -> str:
        return "tui_terminal"

    @property
    def description(self) -> str:
        return (
            "Test TUI (Terminal User Interface) applications by spawning "
            "terminal sessions, sending keystrokes, and capturing screenshots.\n\n"
            "Operations:\n"
            "- spawn: Start a new TUI app session\n"
            "- send_keys: Send keystrokes (supports {ENTER}, {TAB}, {UP}, {CTRL+C})\n"
            "- capture: Capture terminal state as text and screenshot\n"
            "- resize: Resize terminal to test responsive layouts\n"
            "- close: Close a session\n"
            "- list: List active sessions\n\n"
            "Example: spawn -> send_keys -> capture -> resize -> capture -> close\n\n"
            "Special keys: {ENTER}, {TAB}, {ESC}, {UP}, {DOWN}, {LEFT}, {RIGHT}, "
            "{HOME}, {END}, {CTRL+C}, {CTRL+D}, {F1}-{F12}"
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["spawn", "send_keys", "capture", "resize", "close", "list"],
                    "description": "Operation to perform",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID (required for send_keys, capture, resize, close)",
                },
                "command": {
                    "type": "string",
                    "description": "Command to run (required for spawn)",
                },
                "keys": {
                    "type": "string",
                    "description": "Keys to send. Use {ENTER}, {TAB}, etc. for special keys",
                },
                "wait_ms": {
                    "type": "integer",
                    "description": "Milliseconds to wait after sending keys (default: 100)",
                    "default": 100,
                },
                "rows": {
                    "type": "integer",
                    "description": "Terminal height in rows (default: 24, also used for resize)",
                    "default": 24,
                },
                "cols": {
                    "type": "integer",
                    "description": "Terminal width in columns (default: 80, also used for resize)",
                    "default": 80,
                },
                "env": {
                    "type": "object",
                    "description": "Additional environment variables",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["operation"],
        }

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """Execute a TUI terminal operation."""
        operation = input.get("operation")

        if not operation:
            return _err("Missing required parameter: operation")

        manager = get_session_manager()

        try:
            if operation == "spawn":
                return await self._spawn(manager, input)
            elif operation == "send_keys":
                return await self._send_keys(manager, input)
            elif operation == "capture":
                return await self._capture(manager, input)
            elif operation == "resize":
                return await self._resize(manager, input)
            elif operation == "close":
                return await self._close(manager, input)
            elif operation == "list":
                return await self._list(manager)
            else:
                return _err(f"Unknown operation: {operation}")
        except Exception as e:
            return _err(f"Operation {operation} failed: {e}")

    async def _spawn(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Spawn a new TUI session."""
        command = kwargs.get("command")
        if not command:
            return _err("Missing required parameter: command")

        rows = kwargs.get("rows", 24)
        cols = kwargs.get("cols", 80)
        env = kwargs.get("env", {})

        session = await manager.spawn(
            command=command,
            rows=rows,
            cols=cols,
            env=env,
        )

        return ToolResult(
            success=True,
            output={
                "session_id": session.id,
                "status": "running" if session.is_alive() else "exited",
                "rows": rows,
                "cols": cols,
                "command": command,
            },
        )

    async def _send_keys(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Send keystrokes to a session."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return _err("Missing required parameter: session_id")

        keys = kwargs.get("keys", "")
        wait_ms = kwargs.get("wait_ms", 100)

        session = manager.get(session_id)
        if not session:
            return _err(f"Session not found: {session_id}")

        # Parse special keys and convert to bytes
        key_bytes = parse_keys(keys)

        # Send to session
        await session.send(key_bytes, wait_ms=wait_ms)

        return ToolResult(
            success=True,
            output={
                "status": "sent",
                "keys_sent": len(key_bytes),
                "session_alive": session.is_alive(),
            },
        )

    async def _capture(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Capture terminal state."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return _err("Missing required parameter: session_id")

        session = manager.get(session_id)
        if not session:
            return _err(f"Session not found: {session_id}")

        capture = await session.capture()

        return ToolResult(
            success=True,
            output={
                "text": capture["text"],
                "ansi": capture["ansi"],
                "image_path": capture["image_path"],
                "rows": session.rows,
                "cols": session.cols,
                "session_alive": session.is_alive(),
            },
        )

    async def _resize(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Resize a terminal session."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return _err("Missing required parameter: session_id")

        session = manager.get(session_id)
        if not session:
            return _err(f"Session not found: {session_id}")

        rows = kwargs.get("rows", session.rows)
        cols = kwargs.get("cols", session.cols)

        old_rows, old_cols = session.rows, session.cols
        session.resize(rows, cols)

        return ToolResult(
            success=True,
            output={
                "status": "resized",
                "old_size": {"rows": old_rows, "cols": old_cols},
                "new_size": {"rows": rows, "cols": cols},
                "session_alive": session.is_alive(),
            },
        )

    async def _close(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Close a session."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return _err("Missing required parameter: session_id")

        success = await manager.close(session_id)

        if success:
            return ToolResult(
                success=True,
                output={"status": "closed", "session_id": session_id},
            )
        else:
            return _err(f"Session not found: {session_id}")

    async def _list(self, manager: SessionManager) -> ToolResult:
        """List active sessions."""
        sessions = manager.list_sessions()

        return ToolResult(
            success=True,
            output={
                "sessions": [
                    {
                        "session_id": s.id,
                        "command": s.command,
                        "status": "running" if s.is_alive() else "exited",
                        "rows": s.rows,
                        "cols": s.cols,
                    }
                    for s in sessions
                ],
                "count": len(sessions),
            },
        )


# Module mount point
async def mount(coordinator, config: dict) -> Tool:
    """Mount the TUI terminal tool.

    Args:
        coordinator: Module coordinator for registration
        config: Configuration from bundle. Supported keys:
            - session_dir: Base directory for session data
            - session_timeout_minutes: Auto-cleanup timeout (default: 30)
            - default_font_size: Font size for screenshots (default: 14)

    Returns:
        The mounted TUI terminal tool instance
    """
    global _session_manager_config
    _session_manager_config = config or {}

    tool = TUITerminalTool()
    await coordinator.mount("tools", tool, name="tui_terminal")
    return tool
