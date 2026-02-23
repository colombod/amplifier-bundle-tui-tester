"""Tests for the key parsing module."""

import pytest

from amplifier_module_tool_tui_tester.keys import (
    SPECIAL_KEYS,
    get_available_keys,
    parse_keys,
)


# ---------------------------------------------------------------------------
# Plain text passthrough
# ---------------------------------------------------------------------------


class TestPlainText:
    def test_ascii_passthrough(self):
        assert parse_keys("hello") == b"hello"

    def test_empty_string(self):
        assert parse_keys("") == b""

    def test_unicode_text(self):
        assert parse_keys("héllo") == "héllo".encode("utf-8")

    def test_unicode_with_special_key(self):
        assert parse_keys("héllo{ENTER}") == "héllo".encode("utf-8") + b"\r"

    def test_spaces_preserved(self):
        assert parse_keys("hello world") == b"hello world"

    def test_digits_and_symbols(self):
        assert parse_keys("abc123!@#") == b"abc123!@#"


# ---------------------------------------------------------------------------
# Single special keys
# ---------------------------------------------------------------------------


class TestSingleSpecialKeys:
    def test_enter(self):
        assert parse_keys("{ENTER}") == b"\r"

    def test_return_alias(self):
        assert parse_keys("{RETURN}") == b"\r"

    def test_tab(self):
        assert parse_keys("{TAB}") == b"\t"

    def test_esc(self):
        assert parse_keys("{ESC}") == b"\x1b"

    def test_escape_alias(self):
        assert parse_keys("{ESCAPE}") == b"\x1b"

    def test_backspace(self):
        assert parse_keys("{BACKSPACE}") == b"\x7f"

    def test_delete(self):
        assert parse_keys("{DELETE}") == b"\x1b[3~"

    def test_space(self):
        assert parse_keys("{SPACE}") == b" "

    def test_insert(self):
        assert parse_keys("{INSERT}") == b"\x1b[2~"


# ---------------------------------------------------------------------------
# Arrow keys
# ---------------------------------------------------------------------------


class TestArrowKeys:
    def test_up(self):
        assert parse_keys("{UP}") == b"\x1b[A"

    def test_down(self):
        assert parse_keys("{DOWN}") == b"\x1b[B"

    def test_right(self):
        assert parse_keys("{RIGHT}") == b"\x1b[C"

    def test_left(self):
        assert parse_keys("{LEFT}") == b"\x1b[D"


# ---------------------------------------------------------------------------
# Navigation keys
# ---------------------------------------------------------------------------


class TestNavigationKeys:
    def test_home(self):
        assert parse_keys("{HOME}") == b"\x1b[H"

    def test_end(self):
        assert parse_keys("{END}") == b"\x1b[F"

    def test_pgup(self):
        assert parse_keys("{PGUP}") == b"\x1b[5~"

    def test_pageup_alias(self):
        assert parse_keys("{PAGEUP}") == b"\x1b[5~"

    def test_pgdn(self):
        assert parse_keys("{PGDN}") == b"\x1b[6~"

    def test_pagedown_alias(self):
        assert parse_keys("{PAGEDOWN}") == b"\x1b[6~"


# ---------------------------------------------------------------------------
# Function keys F1-F12
# ---------------------------------------------------------------------------


class TestFunctionKeys:
    @pytest.mark.parametrize(
        "key,expected",
        [
            ("F1", b"\x1bOP"),
            ("F2", b"\x1bOQ"),
            ("F3", b"\x1bOR"),
            ("F4", b"\x1bOS"),
            ("F5", b"\x1b[15~"),
            ("F6", b"\x1b[17~"),
            ("F7", b"\x1b[18~"),
            ("F8", b"\x1b[19~"),
            ("F9", b"\x1b[20~"),
            ("F10", b"\x1b[21~"),
            ("F11", b"\x1b[23~"),
            ("F12", b"\x1b[24~"),
        ],
    )
    def test_function_key(self, key: str, expected: bytes):
        assert parse_keys(f"{{{key}}}") == expected


# ---------------------------------------------------------------------------
# Ctrl combinations
# ---------------------------------------------------------------------------


class TestCtrlCombinations:
    def test_ctrl_c(self):
        assert parse_keys("{CTRL+C}") == b"\x03"

    def test_ctrl_d(self):
        assert parse_keys("{CTRL+D}") == b"\x04"

    def test_ctrl_z(self):
        assert parse_keys("{CTRL+Z}") == b"\x1a"

    def test_ctrl_a(self):
        assert parse_keys("{CTRL+A}") == b"\x01"

    def test_ctrl_l(self):
        assert parse_keys("{CTRL+L}") == b"\x0c"

    def test_ctrl_i_is_tab(self):
        assert parse_keys("{CTRL+I}") == b"\t"

    def test_ctrl_m_is_enter(self):
        assert parse_keys("{CTRL+M}") == b"\r"

    def test_ctrl_bracket_is_esc(self):
        assert parse_keys("{CTRL+[}") == b"\x1b"

    @pytest.mark.parametrize("letter", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    def test_all_ctrl_letters_in_map(self, letter: str):
        """Every CTRL+<letter> should be defined in SPECIAL_KEYS."""
        assert f"CTRL+{letter}" in SPECIAL_KEYS


# ---------------------------------------------------------------------------
# Mixed text and special keys
# ---------------------------------------------------------------------------


class TestMixedInput:
    def test_text_then_enter(self):
        assert parse_keys("hello{ENTER}") == b"hello\r"

    def test_special_text_special(self):
        assert parse_keys("{TAB}world{ESC}") == b"\tworld\x1b"

    def test_text_between_specials(self):
        assert parse_keys("{UP}text{DOWN}") == b"\x1b[Atext\x1b[B"

    def test_command_line(self):
        result = parse_keys("ls -la{ENTER}")
        assert result == b"ls -la\r"


# ---------------------------------------------------------------------------
# Multiple consecutive special keys
# ---------------------------------------------------------------------------


class TestConsecutiveSpecialKeys:
    def test_two_ups_and_enter(self):
        assert parse_keys("{UP}{UP}{ENTER}") == b"\x1b[A\x1b[A\r"

    def test_three_tabs(self):
        assert parse_keys("{TAB}{TAB}{TAB}") == b"\t\t\t"

    def test_arrow_sequence(self):
        assert parse_keys("{LEFT}{LEFT}{RIGHT}") == b"\x1b[D\x1b[D\x1b[C"


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------


class TestCaseInsensitivity:
    def test_lowercase_enter(self):
        assert parse_keys("{enter}") == b"\r"

    def test_mixed_case_tab(self):
        assert parse_keys("{Tab}") == b"\t"

    def test_lowercase_ctrl(self):
        assert parse_keys("{ctrl+c}") == b"\x03"

    def test_mixed_case_ctrl(self):
        assert parse_keys("{Ctrl+D}") == b"\x04"

    def test_lowercase_arrow(self):
        assert parse_keys("{up}") == b"\x1b[A"

    def test_lowercase_function_key(self):
        assert parse_keys("{f1}") == b"\x1bOP"


# ---------------------------------------------------------------------------
# Unknown key passthrough
# ---------------------------------------------------------------------------


class TestUnknownKeys:
    def test_unknown_key_passes_through(self):
        assert parse_keys("{UNKNOWN}") == b"{UNKNOWN}"

    def test_unknown_preserves_original_case(self):
        # The unknown path uses match.group(1) (original case), not .upper()
        assert parse_keys("{FooBar}") == b"{FooBar}"

    def test_unknown_surrounded_by_text(self):
        assert parse_keys("before{NOPE}after") == b"before{NOPE}after"

    def test_unknown_mixed_with_known(self):
        result = parse_keys("{ENTER}{NOPE}{TAB}")
        assert result == b"\r{NOPE}\t"


# ---------------------------------------------------------------------------
# get_available_keys()
# ---------------------------------------------------------------------------


class TestGetAvailableKeys:
    def test_returns_sorted_list(self):
        keys = get_available_keys()
        assert keys == sorted(keys)

    def test_returns_list_of_strings(self):
        keys = get_available_keys()
        assert isinstance(keys, list)
        assert all(isinstance(k, str) for k in keys)

    def test_contains_basic_keys(self):
        keys = get_available_keys()
        for expected in ("ENTER", "TAB", "ESC", "BACKSPACE", "SPACE"):
            assert expected in keys

    def test_contains_arrow_keys(self):
        keys = get_available_keys()
        for expected in ("UP", "DOWN", "LEFT", "RIGHT"):
            assert expected in keys

    def test_contains_function_keys(self):
        keys = get_available_keys()
        for i in range(1, 13):
            assert f"F{i}" in keys

    def test_contains_ctrl_combos(self):
        keys = get_available_keys()
        assert "CTRL+C" in keys
        assert "CTRL+D" in keys
        assert "CTRL+Z" in keys

    def test_matches_special_keys_dict(self):
        keys = get_available_keys()
        assert set(keys) == set(SPECIAL_KEYS.keys())
