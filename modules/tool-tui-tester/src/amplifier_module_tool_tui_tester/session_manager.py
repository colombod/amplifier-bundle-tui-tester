"""Session manager for TUI terminal sessions.

Manages the lifecycle of terminal sessions including:
- Spawning processes in pseudo-terminals
- Tracking active sessions
- Cleanup and timeout handling
"""

import asyncio
import os
import pty
import select
import signal
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pyte
from PIL import Image, ImageDraw, ImageFont


@dataclass
class TUISession:
    """Represents an active TUI terminal session."""

    id: str
    command: str
    rows: int
    cols: int
    pid: int
    fd: int  # File descriptor for the PTY
    screen: pyte.Screen
    stream: pyte.Stream
    session_dir: Path
    created_at: datetime = field(default_factory=datetime.now)
    capture_count: int = 0

    def is_alive(self) -> bool:
        """Check if the process is still running."""
        try:
            os.kill(self.pid, 0)
            return True
        except OSError:
            return False

    async def send(self, data: bytes, wait_ms: int = 100) -> None:
        """Send data to the terminal."""
        os.write(self.fd, data)
        # Wait for output to be generated
        await asyncio.sleep(wait_ms / 1000.0)
        # Read any available output
        self._read_output()

    def _read_output(self, timeout: float = 0.1, max_reads: int = 100) -> bytes:
        """Read available output from the terminal.

        Args:
            timeout: Timeout for each select call
            max_reads: Maximum number of read iterations to prevent infinite loops
        """
        output = bytearray()
        reads = 0

        while reads < max_reads:
            reads += 1
            # Check if data is available
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if not ready:
                break

            try:
                chunk = os.read(self.fd, 8192)
                if not chunk:
                    break
                output.extend(chunk)
                # Feed to pyte screen
                self.stream.feed(chunk.decode("utf-8", errors="replace"))
            except OSError:
                break

        return bytes(output)

    async def pump_output(
        self, duration_seconds: float = 1.0, poll_interval: float = 0.05
    ) -> bytes:
        """Continuously read output for a duration (for TUI apps that render async).

        Args:
            duration_seconds: How long to pump output
            poll_interval: How often to poll for data

        Returns:
            All output read during the duration
        """
        import time

        output = bytearray()
        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            chunk = self._read_output(timeout=poll_interval, max_reads=10)
            if chunk:
                output.extend(chunk)
            await asyncio.sleep(poll_interval)

        return bytes(output)

    async def capture(self) -> dict[str, Any]:
        """Capture current terminal state."""
        # Read any pending output first
        self._read_output()

        # Get text representation
        text_lines = []
        for line in self.screen.display:
            text_lines.append(line.rstrip())
        text = "\n".join(text_lines)

        # Get ANSI representation (simplified - just the text for now)
        ansi = text  # Could enhance to preserve colors

        # Render to image
        self.capture_count += 1
        image_path = self.session_dir / f"capture_{self.capture_count:04d}.png"
        self._render_image(image_path)

        return {
            "text": text,
            "ansi": ansi,
            "image_path": str(image_path),
        }

    def _render_image(self, path: Path) -> None:
        """Render the terminal screen to a PNG image."""
        # Configuration
        font_size = 14
        char_width = 8  # Approximate for monospace
        char_height = 16
        padding = 10

        # Calculate image size
        img_width = (self.cols * char_width) + (padding * 2)
        img_height = (self.rows * char_height) + (padding * 2)

        # Create image with dark background
        bg_color = (30, 30, 30)  # Dark gray
        fg_color = (220, 220, 220)  # Light gray

        image = Image.new("RGB", (img_width, img_height), bg_color)
        draw = ImageDraw.Draw(image)

        # Try to load a monospace font, fall back to default
        try:
            # Try common system font paths
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                "/System/Library/Fonts/Monaco.ttf",
                "C:\\Windows\\Fonts\\consola.ttf",
            ]
            font = None
            for fp in font_paths:
                if os.path.exists(fp):
                    font = ImageFont.truetype(fp, font_size)
                    break
            if font is None:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # Define ANSI colors
        colors = {
            "default": fg_color,
            "black": (0, 0, 0),
            "red": (205, 49, 49),
            "green": (13, 188, 121),
            "yellow": (229, 229, 16),
            "blue": (36, 114, 200),
            "magenta": (188, 63, 188),
            "cyan": (17, 168, 205),
            "white": (229, 229, 229),
        }

        # Render each character
        for row_idx, row in enumerate(self.screen.buffer.values()):
            y = padding + (row_idx * char_height)

            for col_idx in range(self.cols):
                char_data = row.get(col_idx)
                if char_data is None:
                    continue

                char = char_data.data if char_data.data else " "
                x = padding + (col_idx * char_width)

                # Get foreground color
                fg = char_data.fg if hasattr(char_data, "fg") else "default"
                color = colors.get(fg, fg_color)

                # Handle bold
                if hasattr(char_data, "bold") and char_data.bold:
                    # Could use bold font variant
                    pass

                # Draw character
                draw.text((x, y), char, fill=color, font=font)

        # Draw cursor if visible
        cursor_y = self.screen.cursor.y
        cursor_x = self.screen.cursor.x
        cursor_rect = [
            padding + (cursor_x * char_width),
            padding + (cursor_y * char_height),
            padding + ((cursor_x + 1) * char_width),
            padding + ((cursor_y + 1) * char_height),
        ]
        draw.rectangle(cursor_rect, outline=(100, 100, 200))

        # Save image
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "PNG")

    def close(self) -> None:
        """Close the session and clean up."""
        try:
            os.close(self.fd)
        except OSError:
            pass

        if self.is_alive():
            try:
                os.kill(self.pid, signal.SIGTERM)
                # Give it a moment to terminate
                for _ in range(10):
                    try:
                        os.kill(self.pid, 0)
                        import time

                        time.sleep(0.1)
                    except OSError:
                        break
                else:
                    # Force kill if still alive
                    os.kill(self.pid, signal.SIGKILL)
            except OSError:
                pass


class SessionManager:
    """Manages multiple TUI terminal sessions."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize the session manager.

        Args:
            base_dir: Base directory for session data. Defaults to ~/.amplifier/tui-sessions
        """
        if base_dir is None:
            base_dir = Path.home() / ".amplifier" / "tui-sessions"
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._sessions: dict[str, TUISession] = {}

    async def spawn(
        self,
        command: str,
        rows: int = 24,
        cols: int = 80,
        env: dict[str, str] | None = None,
    ) -> TUISession:
        """Spawn a new terminal session.

        Args:
            command: Command to run
            rows: Terminal height
            cols: Terminal width
            env: Additional environment variables

        Returns:
            The created TUISession
        """
        session_id = str(uuid.uuid4())[:8]
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Prepare environment
        spawn_env = os.environ.copy()
        spawn_env["TERM"] = "xterm-256color"
        spawn_env["COLUMNS"] = str(cols)
        spawn_env["LINES"] = str(rows)
        if env:
            spawn_env.update(env)

        # Create pyte screen and stream
        screen = pyte.Screen(cols, rows)
        stream = pyte.Stream(screen)

        # Fork a pseudo-terminal
        pid, fd = pty.fork()

        if pid == 0:
            # Child process
            os.execvpe("/bin/sh", ["/bin/sh", "-c", command], spawn_env)
        else:
            # Parent process
            # Set terminal size
            import fcntl
            import struct
            import termios

            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

            session = TUISession(
                id=session_id,
                command=command,
                rows=rows,
                cols=cols,
                pid=pid,
                fd=fd,
                screen=screen,
                stream=stream,
                session_dir=session_dir,
            )

            self._sessions[session_id] = session

            # Give the process a moment to start and produce initial output
            await asyncio.sleep(0.5)
            session._read_output()

            return session

    def get(self, session_id: str) -> TUISession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    async def close(self, session_id: str) -> bool:
        """Close a session.

        Returns:
            True if session was found and closed, False otherwise
        """
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            return True
        return False

    def list_sessions(self) -> list[TUISession]:
        """List all active sessions."""
        return list(self._sessions.values())

    async def cleanup_dead(self) -> int:
        """Clean up sessions with dead processes.

        Returns:
            Number of sessions cleaned up
        """
        dead = [sid for sid, s in self._sessions.items() if not s.is_alive()]
        for sid in dead:
            await self.close(sid)
        return len(dead)
