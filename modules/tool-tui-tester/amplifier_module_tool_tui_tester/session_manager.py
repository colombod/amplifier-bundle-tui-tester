"""Session manager for TUI terminal sessions.

Manages the lifecycle of terminal sessions including:
- Spawning processes in pseudo-terminals
- Tracking active sessions
- Cleanup and timeout handling
"""

import asyncio
import fcntl
import os
import pty
import select
import signal
import struct
import termios
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pyte
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Named ANSI color table (standard 8 colors)
# ---------------------------------------------------------------------------

_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "red": (205, 49, 49),
    "green": (13, 188, 121),
    "yellow": (229, 229, 16),
    "blue": (36, 114, 200),
    "magenta": (188, 63, 188),
    "cyan": (17, 168, 205),
    "white": (229, 229, 229),
}

_BRIGHT_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "black": (102, 102, 102),
    "red": (241, 76, 76),
    "green": (35, 209, 139),
    "yellow": (245, 245, 67),
    "blue": (59, 142, 234),
    "magenta": (214, 112, 214),
    "cyan": (41, 184, 219),
    "white": (255, 255, 255),
}

# Maps xterm indices 0-7 to the named color keys for palette lookups
_STANDARD_INDEX_NAMES = [
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]

# ---------------------------------------------------------------------------
# xterm-256 palette helpers
# ---------------------------------------------------------------------------

# The six intensity values used in the 6×6×6 color cube (indices 16-231)
_CUBE_VALUES: list[int] = [0, 95, 135, 175, 215, 255]


def _xterm_256_to_rgb(n: int) -> tuple[int, int, int]:
    """Convert an xterm-256 palette index to an ``(r, g, b)`` tuple.

    Ranges:
    - 0–7:    standard ANSI colors
    - 8–15:   bright ANSI colors
    - 16–231: 6×6×6 color cube
    - 232–255: grayscale ramp
    """
    if n < 0 or n > 255:
        return (220, 220, 220)  # fallback to default fg

    if n < 8:
        return _NAMED_COLORS[_STANDARD_INDEX_NAMES[n]]
    if n < 16:
        return _BRIGHT_NAMED_COLORS[_STANDARD_INDEX_NAMES[n - 8]]
    if n < 232:
        idx = n - 16
        r_idx = idx // 36
        g_idx = (idx // 6) % 6
        b_idx = idx % 6
        return (_CUBE_VALUES[r_idx], _CUBE_VALUES[g_idx], _CUBE_VALUES[b_idx])

    # 232–255: grayscale ramp
    value = 8 + (n - 232) * 10
    return (value, value, value)


# ---------------------------------------------------------------------------
# Color resolution helpers
# ---------------------------------------------------------------------------

_DEFAULT_FG: tuple[int, int, int] = (220, 220, 220)
_DEFAULT_BG: tuple[int, int, int] = (30, 30, 30)


def _resolve_color(
    raw: str,
    default: tuple[int, int, int],
) -> tuple[int, int, int]:
    """Resolve a pyte color value to an ``(r, g, b)`` tuple.

    Handles:
    - ``"default"`` → *default*
    - Named colors (``"red"``, ``"green"``, …)
    - Integer-as-string 0-255 (256-color palette)
    - 6-char hex string like ``"ff5500"``
    """
    if raw == "default" or raw is None:
        return default

    # Named ANSI color
    if raw in _NAMED_COLORS:
        return _NAMED_COLORS[raw]

    # Integer (256-color palette index) — pyte may pass str or int
    try:
        idx = int(raw)
        if 0 <= idx <= 255:
            return _xterm_256_to_rgb(idx)
    except (ValueError, TypeError):
        pass

    # 6-char hex string (true-color)
    if isinstance(raw, str) and len(raw) == 6:
        try:
            r = int(raw[0:2], 16)
            g = int(raw[2:4], 16)
            b = int(raw[4:6], 16)
            return (r, g, b)
        except ValueError:
            pass

    return default


def _brighten(color: tuple[int, int, int], amount: int = 50) -> tuple[int, int, int]:
    """Brighten *color* by *amount*, capping each channel at 255."""
    return (
        min(color[0] + amount, 255),
        min(color[1] + amount, 255),
        min(color[2] + amount, 255),
    )


# ---------------------------------------------------------------------------
# Font loading helper
# ---------------------------------------------------------------------------

_FONT_SEARCH_PATHS: list[str] = [
    # Debian / Ubuntu
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    # Arch / Fedora
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf",
    # macOS
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFMono-Regular.otf",
    "/Library/Fonts/SF-Mono-Regular.otf",
    # Windows
    "C:\\Windows\\Fonts\\consola.ttf",
    "C:\\Windows\\Fonts\\cour.ttf",
]


def _load_monospace_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a TrueType monospace font at *size*; fall back to default."""
    for fp in _FONT_SEARCH_PATHS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# ANSI string builder (for capture output)
# ---------------------------------------------------------------------------

# Map pyte's 256-color index to SGR foreground/background codes
_SGR_FG_256 = "\033[38;5;{}m"
_SGR_BG_256 = "\033[48;5;{}m"
_SGR_FG_RGB = "\033[38;2;{};{};{}m"
_SGR_BG_RGB = "\033[48;2;{};{};{}m"
_SGR_BOLD = "\033[1m"
_SGR_RESET = "\033[0m"


def _sgr_color(raw: str, *, is_bg: bool = False) -> str:
    """Return the SGR escape sequence for the given pyte color value."""
    if raw == "default" or raw is None:
        return ""

    prefix_256 = _SGR_BG_256 if is_bg else _SGR_FG_256
    prefix_rgb = _SGR_BG_RGB if is_bg else _SGR_FG_RGB

    # Named → map to standard index
    if raw in _NAMED_COLORS:
        idx = _STANDARD_INDEX_NAMES.index(raw)
        return prefix_256.format(idx)

    # Integer 0-255
    try:
        idx = int(raw)
        if 0 <= idx <= 255:
            return prefix_256.format(idx)
    except (ValueError, TypeError):
        pass

    # 6-char hex → true-color
    if isinstance(raw, str) and len(raw) == 6:
        try:
            r = int(raw[0:2], 16)
            g = int(raw[2:4], 16)
            b = int(raw[4:6], 16)
            return prefix_rgb.format(r, g, b)
        except ValueError:
            pass

    return ""


def _build_ansi_line(
    screen: pyte.Screen,
    row_idx: int,
    cols: int,
) -> str:
    """Build a single ANSI-escaped line from the screen buffer."""
    row = screen.buffer.get(row_idx, {})
    parts: list[str] = []

    for col_idx in range(cols):
        char_data = row.get(col_idx)
        if char_data is None:
            parts.append(" ")
            continue

        sgr: list[str] = []
        fg_seq = _sgr_color(char_data.fg)
        if fg_seq:
            sgr.append(fg_seq)
        bg_seq = _sgr_color(char_data.bg, is_bg=True)
        if bg_seq:
            sgr.append(bg_seq)
        if char_data.bold:
            sgr.append(_SGR_BOLD)

        ch = char_data.data if char_data.data else " "

        if sgr:
            parts.append("".join(sgr))
            parts.append(ch)
            parts.append(_SGR_RESET)
        else:
            parts.append(ch)

    return "".join(parts).rstrip()


# ---------------------------------------------------------------------------
# TUISession
# ---------------------------------------------------------------------------


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
    font_size: int = 14

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

    async def _read_output_async(
        self,
        timeout: float = 0.1,
        max_reads: int = 100,
    ) -> bytes:
        """Async wrapper around :meth:`_read_output`.

        Runs the blocking I/O in an executor so the event loop is not blocked.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._read_output,
            timeout,
            max_reads,
        )

    async def pump_output(
        self,
        duration_seconds: float = 1.0,
        poll_interval: float = 0.05,
    ) -> bytes:
        """Continuously read output for a duration (for TUI apps that render async).

        Args:
            duration_seconds: How long to pump output
            poll_interval: How often to poll for data

        Returns:
            All output read during the duration
        """
        output = bytearray()
        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            chunk = await self._read_output_async(timeout=poll_interval, max_reads=10)
            if chunk:
                output.extend(chunk)
            await asyncio.sleep(poll_interval)

        return bytes(output)

    async def capture(self) -> dict[str, Any]:
        """Capture current terminal state."""
        # Pump output to let async TUI apps finish rendering
        await self.pump_output(duration_seconds=0.5, poll_interval=0.05)

        # Get text representation
        text_lines: list[str] = []
        for line in self.screen.display:
            text_lines.append(line.rstrip())
        text = "\n".join(text_lines)

        # Build proper ANSI-escaped representation
        ansi_lines: list[str] = []
        for row_idx in range(self.rows):
            ansi_lines.append(_build_ansi_line(self.screen, row_idx, self.cols))
        ansi = "\n".join(ansi_lines)

        # Render to image
        self.capture_count += 1
        image_path = self.session_dir / f"capture_{self.capture_count:04d}.png"
        self._render_image(image_path, font_size=self.font_size)

        return {
            "text": text,
            "ansi": ansi,
            "image_path": str(image_path),
        }

    def _render_image(
        self,
        path: Path,
        font_size: int = 14,
    ) -> None:
        """Render the terminal screen to a PNG image."""
        padding = 10

        # Load font and derive character metrics
        font = _load_monospace_font(font_size)
        try:
            bbox = font.getbbox("M")
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]
            # Add a small vertical gap so lines don't touch
            char_height = max(char_height, font_size) + 2
        except Exception:  # noqa: BLE001
            # Fallback for bitmap fonts without getbbox
            char_width = 8
            char_height = font_size + 2

        # Calculate image size
        img_width = (self.cols * char_width) + (padding * 2)
        img_height = (self.rows * char_height) + (padding * 2)

        # Create image with dark background
        image = Image.new("RGB", (img_width, img_height), _DEFAULT_BG)
        draw = ImageDraw.Draw(image)

        # Render each character
        for row_idx, row in enumerate(self.screen.buffer.values()):
            y = padding + (row_idx * char_height)

            for col_idx in range(self.cols):
                char_data = row.get(col_idx)
                if char_data is None:
                    continue

                x = padding + (col_idx * char_width)

                # Resolve background color and draw a filled rect when non-default
                bg = _resolve_color(char_data.bg, _DEFAULT_BG)
                if bg != _DEFAULT_BG:
                    draw.rectangle(
                        [x, y, x + char_width, y + char_height],
                        fill=bg,
                    )

                # Resolve foreground color
                fg = _resolve_color(char_data.fg, _DEFAULT_FG)

                # Bold → brighten foreground
                if char_data.bold:
                    fg = _brighten(fg)

                char = char_data.data if char_data.data else " "
                draw.text((x, y), char, fill=fg, font=font)

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

    def resize(self, rows: int, cols: int) -> None:
        """Resize the terminal to *rows*×*cols*.

        Updates the internal screen/stream, notifies the child process via
        ``SIGWINCH``, and sets the PTY window size.
        """
        old_display = list(self.screen.display)

        # Create a new screen/stream pair with the new dimensions
        new_screen = pyte.Screen(cols, rows)
        new_stream = pyte.Stream(new_screen)

        # Copy over the visible text from the old screen
        for row_idx, line in enumerate(old_display):
            if row_idx >= rows:
                break
            for col_idx, ch in enumerate(line):
                if col_idx >= cols:
                    break
                if ch != " ":
                    new_screen.buffer[row_idx][col_idx] = (
                        new_screen.buffer[row_idx]
                        .get(
                            col_idx,
                            new_screen.default_char,
                        )
                        ._replace(data=ch)
                    )

        self.screen = new_screen
        self.stream = new_stream
        self.rows = rows
        self.cols = cols

        # Notify the child process of the new window size
        if self.is_alive():
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            os.kill(self.pid, signal.SIGWINCH)

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
                        time.sleep(0.1)
                    except OSError:
                        break
                else:
                    # Force kill if still alive
                    os.kill(self.pid, signal.SIGKILL)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------


class SessionManager:
    """Manages multiple TUI terminal sessions."""

    def __init__(
        self,
        base_dir: Path | None = None,
        session_timeout_minutes: int = 30,
        default_font_size: int = 14,
    ):
        """Initialize the session manager.

        Args:
            base_dir: Base directory for session data.
                Defaults to ``~/.amplifier/tui-sessions``.
            session_timeout_minutes: Automatically clean up sessions older than
                this many minutes.  Defaults to 30.
            default_font_size: Font size used when rendering terminal
                screenshots.  Defaults to 14.
        """
        if base_dir is None:
            base_dir = Path.home() / ".amplifier" / "tui-sessions"
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.session_timeout_minutes = session_timeout_minutes
        self.default_font_size = default_font_size

        self._sessions: dict[str, TUISession] = {}

    # -- stale-session cleanup ----------------------------------------------

    def cleanup_stale(self) -> int:
        """Remove sessions that have exceeded the configured timeout.

        Returns:
            Number of sessions cleaned up.
        """
        cutoff = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        stale = [sid for sid, s in self._sessions.items() if s.created_at < cutoff]
        for sid in stale:
            session = self._sessions.pop(sid, None)
            if session:
                session.close()
        return len(stale)

    # -- public API ---------------------------------------------------------

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
        # Housekeeping: reap stale sessions
        self.cleanup_stale()

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
            # Parent process — set terminal size
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
                font_size=self.default_font_size,
            )

            self._sessions[session_id] = session

            # Give the process a moment to start and produce initial output
            await asyncio.sleep(0.5)
            await session.pump_output(duration_seconds=0.5, poll_interval=0.05)

            return session

        # Unreachable (child execs), but keeps type checkers happy
        raise RuntimeError("Child process failed to exec")  # pragma: no cover

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
        self.cleanup_stale()
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
