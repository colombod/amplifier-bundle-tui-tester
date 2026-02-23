"""Tests for the session manager module."""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pyte
import pytest
from PIL import ImageFont

from amplifier_module_tool_tui_tester.session_manager import (
    SessionManager,
    TUISession,
    _brighten,
    _build_ansi_line,
    _load_monospace_font,
    _resolve_color,
    _xterm_256_to_rgb,
    _DEFAULT_BG,
    _DEFAULT_FG,
    _NAMED_COLORS,
)


# ---------------------------------------------------------------------------
# _xterm_256_to_rgb
# ---------------------------------------------------------------------------


class TestXterm256ToRgb:
    """Test the xterm-256 palette index to RGB conversion."""

    def test_standard_black(self):
        assert _xterm_256_to_rgb(0) == _NAMED_COLORS["black"]

    def test_standard_red(self):
        assert _xterm_256_to_rgb(1) == _NAMED_COLORS["red"]

    def test_standard_green(self):
        assert _xterm_256_to_rgb(2) == _NAMED_COLORS["green"]

    def test_standard_white(self):
        assert _xterm_256_to_rgb(7) == _NAMED_COLORS["white"]

    def test_standard_range_all(self):
        """Indices 0-7 map to the standard named color palette."""
        names = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
        for i, name in enumerate(names):
            assert _xterm_256_to_rgb(i) == _NAMED_COLORS[name]

    def test_bright_colors(self):
        """Indices 8-15 map to the bright named color palette."""
        from amplifier_module_tool_tui_tester.session_manager import _BRIGHT_NAMED_COLORS

        names = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
        for i, name in enumerate(names):
            assert _xterm_256_to_rgb(8 + i) == _BRIGHT_NAMED_COLORS[name]

    def test_color_cube_origin(self):
        # Index 16 = (0, 0, 0) in the 6x6x6 cube
        assert _xterm_256_to_rgb(16) == (0, 0, 0)

    def test_color_cube_max(self):
        # Index 231 = (255, 255, 255) in the 6x6x6 cube
        assert _xterm_256_to_rgb(231) == (255, 255, 255)

    def test_color_cube_red_axis(self):
        # Index 16 + 36 = 52 -> r_idx=1, g_idx=0, b_idx=0 -> (95, 0, 0)
        assert _xterm_256_to_rgb(52) == (95, 0, 0)

    def test_color_cube_green_axis(self):
        # Index 16 + 6 = 22 -> r_idx=0, g_idx=1, b_idx=0 -> (0, 95, 0)
        assert _xterm_256_to_rgb(22) == (0, 95, 0)

    def test_color_cube_blue_axis(self):
        # Index 16 + 1 = 17 -> r_idx=0, g_idx=0, b_idx=1 -> (0, 0, 95)
        assert _xterm_256_to_rgb(17) == (0, 0, 95)

    def test_grayscale_start(self):
        # Index 232 -> value = 8 + 0*10 = 8
        assert _xterm_256_to_rgb(232) == (8, 8, 8)

    def test_grayscale_end(self):
        # Index 255 -> value = 8 + 23*10 = 238
        assert _xterm_256_to_rgb(255) == (238, 238, 238)

    def test_grayscale_middle(self):
        # Index 244 -> value = 8 + 12*10 = 128
        assert _xterm_256_to_rgb(244) == (128, 128, 128)

    def test_out_of_range_negative(self):
        assert _xterm_256_to_rgb(-1) == (220, 220, 220)

    def test_out_of_range_high(self):
        assert _xterm_256_to_rgb(256) == (220, 220, 220)

    def test_out_of_range_very_high(self):
        assert _xterm_256_to_rgb(999) == (220, 220, 220)


# ---------------------------------------------------------------------------
# _resolve_color
# ---------------------------------------------------------------------------


class TestResolveColor:
    """Test the color resolution from pyte values to RGB tuples."""

    def test_default_string(self):
        assert _resolve_color("default", _DEFAULT_FG) == _DEFAULT_FG

    def test_none_returns_default(self):
        assert _resolve_color(None, _DEFAULT_BG) == _DEFAULT_BG

    def test_named_color_red(self):
        assert _resolve_color("red", _DEFAULT_FG) == _NAMED_COLORS["red"]

    def test_named_color_green(self):
        assert _resolve_color("green", _DEFAULT_FG) == _NAMED_COLORS["green"]

    def test_named_color_blue(self):
        assert _resolve_color("blue", _DEFAULT_FG) == _NAMED_COLORS["blue"]

    def test_all_named_colors(self):
        for name, rgb in _NAMED_COLORS.items():
            assert _resolve_color(name, _DEFAULT_FG) == rgb

    def test_integer_string_zero(self):
        assert _resolve_color("0", _DEFAULT_FG) == _NAMED_COLORS["black"]

    def test_integer_string_palette(self):
        assert _resolve_color("1", _DEFAULT_FG) == _NAMED_COLORS["red"]

    def test_integer_string_200(self):
        # 200 is in the color cube range
        result = _resolve_color("200", _DEFAULT_FG)
        assert result == _xterm_256_to_rgb(200)

    def test_hex_string(self):
        assert _resolve_color("ff5500", _DEFAULT_FG) == (255, 85, 0)

    def test_hex_string_all_zeros(self):
        assert _resolve_color("000000", _DEFAULT_FG) == (0, 0, 0)

    def test_hex_string_all_ff(self):
        assert _resolve_color("ffffff", _DEFAULT_FG) == (255, 255, 255)

    def test_invalid_string_returns_default(self):
        assert _resolve_color("not-a-color", _DEFAULT_FG) == _DEFAULT_FG

    def test_uses_custom_default(self):
        custom = (42, 42, 42)
        assert _resolve_color("default", custom) == custom
        assert _resolve_color(None, custom) == custom


# ---------------------------------------------------------------------------
# _brighten
# ---------------------------------------------------------------------------


class TestBrighten:
    """Test the color brightening helper."""

    def test_normal_brighten(self):
        assert _brighten((100, 100, 100), 50) == (150, 150, 150)

    def test_caps_at_255(self):
        assert _brighten((230, 240, 250), 50) == (255, 255, 255)

    def test_already_max(self):
        assert _brighten((255, 255, 255), 50) == (255, 255, 255)

    def test_zero_amount(self):
        assert _brighten((100, 100, 100), 0) == (100, 100, 100)

    def test_default_amount(self):
        # Default amount is 50
        assert _brighten((0, 0, 0)) == (50, 50, 50)

    def test_partial_cap(self):
        # Only some channels cap
        assert _brighten((200, 100, 250), 60) == (255, 160, 255)

    def test_all_zeros(self):
        assert _brighten((0, 0, 0), 100) == (100, 100, 100)


# ---------------------------------------------------------------------------
# _build_ansi_line
# ---------------------------------------------------------------------------


class TestBuildAnsiLine:
    """Test the ANSI string builder for screen lines."""

    def test_empty_screen(self):
        screen = pyte.Screen(10, 1)
        line = _build_ansi_line(screen, 0, 10)
        # Empty screen has no characters in buffer -> all spaces -> rstripped to ""
        assert line == ""

    def test_basic_text(self):
        screen = pyte.Screen(20, 1)
        stream = pyte.Stream(screen)
        stream.feed("hello")
        line = _build_ansi_line(screen, 0, 20)
        assert "hello" in line

    def test_colored_text_has_escapes(self):
        screen = pyte.Screen(20, 1)
        stream = pyte.Stream(screen)
        # ESC[31m = red foreground, then text, then reset
        stream.feed("\033[31mred\033[0m")
        line = _build_ansi_line(screen, 0, 20)
        # Should contain SGR escape sequences (builder wraps each char individually)
        assert "\033[" in line
        assert "\033[0m" in line
        # The characters r, e, d should all be present in the output
        assert "r" in line
        assert "e" in line
        assert "d" in line

    def test_nonexistent_row(self):
        screen = pyte.Screen(10, 5)
        # Row 99 doesn't exist in a 5-row screen -> empty dict -> all spaces
        line = _build_ansi_line(screen, 99, 10)
        assert line == ""


# ---------------------------------------------------------------------------
# _load_monospace_font
# ---------------------------------------------------------------------------


class TestLoadMonospaceFont:
    """Test font loading."""

    def test_returns_font_object(self):
        font = _load_monospace_font(14)
        assert isinstance(font, (ImageFont.FreeTypeFont, ImageFont.ImageFont))

    def test_different_sizes(self):
        font_small = _load_monospace_font(10)
        font_large = _load_monospace_font(24)
        assert font_small is not None
        assert font_large is not None

    def test_fallback_when_no_fonts(self):
        with patch(
            "amplifier_module_tool_tui_tester.session_manager._FONT_SEARCH_PATHS",
            ["/nonexistent/font.ttf"],
        ):
            font = _load_monospace_font(14)
            assert font is not None  # Should fall back to default


# ---------------------------------------------------------------------------
# SessionManager lifecycle (requires real PTY)
# ---------------------------------------------------------------------------


class TestSessionManagerLifecycle:
    """Test SessionManager spawn/get/close/list operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> SessionManager:
        return SessionManager(base_dir=tmp_path / "sessions")

    async def test_spawn_creates_session(self, manager: SessionManager):
        session = await manager.spawn("echo hello", rows=24, cols=80)
        try:
            assert session is not None
            assert isinstance(session.id, str)
            assert len(session.id) == 8
            assert session.command == "echo hello"
            assert session.rows == 24
            assert session.cols == 80
            assert session.pid > 0
            assert session.fd >= 0
            assert session.session_dir.exists()
        finally:
            await manager.close(session.id)

    async def test_get_retrieves_session(self, manager: SessionManager):
        session = await manager.spawn("sleep 10", rows=24, cols=80)
        try:
            retrieved = manager.get(session.id)
            assert retrieved is session
        finally:
            await manager.close(session.id)

    async def test_get_nonexistent_returns_none(self, manager: SessionManager):
        assert manager.get("nonexistent") is None

    async def test_close_removes_session(self, manager: SessionManager):
        session = await manager.spawn("sleep 10", rows=24, cols=80)
        sid = session.id
        result = await manager.close(sid)
        assert result is True
        assert manager.get(sid) is None

    async def test_close_nonexistent_returns_false(self, manager: SessionManager):
        result = await manager.close("nonexistent")
        assert result is False

    async def test_list_sessions(self, manager: SessionManager):
        s1 = await manager.spawn("sleep 10", rows=24, cols=80)
        s2 = await manager.spawn("sleep 10", rows=24, cols=80)
        try:
            sessions = manager.list_sessions()
            ids = {s.id for s in sessions}
            assert s1.id in ids
            assert s2.id in ids
            assert len(sessions) >= 2
        finally:
            await manager.close(s1.id)
            await manager.close(s2.id)

    async def test_cleanup_dead(self, manager: SessionManager):
        session = await manager.spawn("echo done", rows=24, cols=80)
        sid = session.id
        # echo exits immediately -> wait a moment then reap the zombie so
        # os.kill(pid, 0) will raise OSError and is_alive() returns False.
        await asyncio.sleep(1.0)
        try:
            os.waitpid(session.pid, os.WNOHANG)
        except ChildProcessError:
            pass
        cleaned = await manager.cleanup_dead()
        assert cleaned >= 1
        assert manager.get(sid) is None

    async def test_cleanup_stale(self, manager: SessionManager):
        session = await manager.spawn("sleep 60", rows=24, cols=80)
        sid = session.id
        # Mock created_at to be old enough to be stale
        session.created_at = datetime.now() - timedelta(minutes=60)
        cleaned = manager.cleanup_stale()
        assert cleaned >= 1
        assert manager.get(sid) is None

    async def test_spawn_with_custom_env(self, manager: SessionManager):
        session = await manager.spawn(
            "echo $MY_TEST_VAR",
            rows=24,
            cols=80,
            env={"MY_TEST_VAR": "test_value_12345"},
        )
        try:
            capture = await session.capture()
            assert "test_value_12345" in capture["text"]
        finally:
            await manager.close(session.id)

    async def test_spawn_custom_dimensions(self, manager: SessionManager):
        session = await manager.spawn("sleep 10", rows=40, cols=120)
        try:
            assert session.rows == 40
            assert session.cols == 120
        finally:
            await manager.close(session.id)


# ---------------------------------------------------------------------------
# TUISession
# ---------------------------------------------------------------------------


class TestTUISession:
    """Test TUISession operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> SessionManager:
        return SessionManager(base_dir=tmp_path / "sessions")

    async def test_is_alive_for_running_process(self, manager: SessionManager):
        session = await manager.spawn("sleep 30", rows=24, cols=80)
        try:
            assert session.is_alive() is True
        finally:
            await manager.close(session.id)

    async def test_is_alive_false_for_exited_process(self, manager: SessionManager):
        session = await manager.spawn("echo done", rows=24, cols=80)
        sid = session.id
        # Wait for echo to exit, then reap the zombie so os.kill(pid, 0)
        # raises OSError and is_alive() correctly returns False.
        await asyncio.sleep(1.0)
        try:
            os.waitpid(session.pid, os.WNOHANG)
        except ChildProcessError:
            pass
        alive = session.is_alive()
        # Clean up regardless
        await manager.close(sid)
        assert alive is False

    async def test_send_and_capture_roundtrip(self, manager: SessionManager):
        """Spawn cat, send text, verify it appears in capture."""
        session = await manager.spawn("cat", rows=24, cols=80)
        try:
            await session.send(b"hello world")
            capture = await session.capture()
            assert "hello world" in capture["text"]
        finally:
            await manager.close(session.id)

    async def test_capture_returns_expected_keys(self, manager: SessionManager):
        session = await manager.spawn("echo capture_test", rows=24, cols=80)
        try:
            capture = await session.capture()
            assert "text" in capture
            assert "ansi" in capture
            assert "image_path" in capture
            assert isinstance(capture["text"], str)
            assert isinstance(capture["ansi"], str)
            assert isinstance(capture["image_path"], str)
        finally:
            await manager.close(session.id)

    async def test_capture_image_file_exists(self, manager: SessionManager):
        session = await manager.spawn("echo image_test", rows=24, cols=80)
        try:
            capture = await session.capture()
            image_path = Path(capture["image_path"])
            assert image_path.exists()
            assert image_path.suffix == ".png"
            # Verify it's a non-empty file
            assert image_path.stat().st_size > 0
        finally:
            await manager.close(session.id)

    async def test_capture_increments_counter(self, manager: SessionManager):
        session = await manager.spawn("echo counter_test", rows=24, cols=80)
        try:
            cap1 = await session.capture()
            cap2 = await session.capture()
            assert "0001" in cap1["image_path"]
            assert "0002" in cap2["image_path"]
        finally:
            await manager.close(session.id)

    async def test_resize(self, manager: SessionManager):
        session = await manager.spawn("sleep 30", rows=24, cols=80)
        try:
            session.resize(40, 120)
            assert session.rows == 40
            assert session.cols == 120
            assert session.screen.columns == 120
            assert session.screen.lines == 40
        finally:
            await manager.close(session.id)

    async def test_resize_preserves_content(self, manager: SessionManager):
        session = await manager.spawn("cat", rows=24, cols=80)
        try:
            await session.send(b"visible")
            await asyncio.sleep(0.3)
            session.resize(30, 100)
            # The old text should be carried over to the new screen
            display_text = "".join(session.screen.display)
            assert "visible" in display_text
        finally:
            await manager.close(session.id)

    async def test_send_special_keys(self, manager: SessionManager):
        """Verify that special byte sequences can be sent."""
        session = await manager.spawn("cat", rows=24, cols=80)
        try:
            # Send text followed by newline
            await session.send(b"line1\r")
            capture = await session.capture()
            assert "line1" in capture["text"]
        finally:
            await manager.close(session.id)

    async def test_session_dir_created(self, manager: SessionManager):
        session = await manager.spawn("sleep 10", rows=24, cols=80)
        try:
            assert session.session_dir.is_dir()
            assert session.id in str(session.session_dir)
        finally:
            await manager.close(session.id)


# ---------------------------------------------------------------------------
# SessionManager initialization
# ---------------------------------------------------------------------------


class TestSessionManagerInit:
    """Test SessionManager constructor and defaults."""

    def test_default_base_dir(self):
        mgr = SessionManager()
        expected = Path.home() / ".amplifier" / "tui-sessions"
        assert mgr.base_dir == expected

    def test_custom_base_dir(self, tmp_path: Path):
        custom = tmp_path / "custom-sessions"
        mgr = SessionManager(base_dir=custom)
        assert mgr.base_dir == custom
        assert custom.exists()

    def test_default_timeout(self):
        mgr = SessionManager()
        assert mgr.session_timeout_minutes == 30

    def test_custom_timeout(self, tmp_path: Path):
        mgr = SessionManager(base_dir=tmp_path, session_timeout_minutes=60)
        assert mgr.session_timeout_minutes == 60

    def test_default_font_size(self):
        mgr = SessionManager()
        assert mgr.default_font_size == 14

    def test_custom_font_size(self, tmp_path: Path):
        mgr = SessionManager(base_dir=tmp_path, default_font_size=20)
        assert mgr.default_font_size == 20

    def test_empty_sessions_on_init(self, tmp_path: Path):
        mgr = SessionManager(base_dir=tmp_path)
        assert mgr.list_sessions() == []
