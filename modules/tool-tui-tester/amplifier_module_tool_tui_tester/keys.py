"""Key parsing utilities for TUI terminal tool.

Converts human-readable key notation like {ENTER}, {TAB}, {CTRL+C}
into actual terminal escape sequences.
"""

import re

# Special key mappings
SPECIAL_KEYS: dict[str, bytes] = {
    # Basic control keys
    "ENTER": b"\r",
    "RETURN": b"\r",
    "TAB": b"\t",
    "ESC": b"\x1b",
    "ESCAPE": b"\x1b",
    "BACKSPACE": b"\x7f",
    "DELETE": b"\x1b[3~",
    "SPACE": b" ",
    # Arrow keys
    "UP": b"\x1b[A",
    "DOWN": b"\x1b[B",
    "RIGHT": b"\x1b[C",
    "LEFT": b"\x1b[D",
    # Navigation keys
    "HOME": b"\x1b[H",
    "END": b"\x1b[F",
    "PGUP": b"\x1b[5~",
    "PAGEUP": b"\x1b[5~",
    "PGDN": b"\x1b[6~",
    "PAGEDOWN": b"\x1b[6~",
    "INSERT": b"\x1b[2~",
    # Function keys
    "F1": b"\x1bOP",
    "F2": b"\x1bOQ",
    "F3": b"\x1bOR",
    "F4": b"\x1bOS",
    "F5": b"\x1b[15~",
    "F6": b"\x1b[17~",
    "F7": b"\x1b[18~",
    "F8": b"\x1b[19~",
    "F9": b"\x1b[20~",
    "F10": b"\x1b[21~",
    "F11": b"\x1b[23~",
    "F12": b"\x1b[24~",
    # Control key combinations
    "CTRL+A": b"\x01",
    "CTRL+B": b"\x02",
    "CTRL+C": b"\x03",
    "CTRL+D": b"\x04",
    "CTRL+E": b"\x05",
    "CTRL+F": b"\x06",
    "CTRL+G": b"\x07",
    "CTRL+H": b"\x08",
    "CTRL+I": b"\t",  # Same as TAB
    "CTRL+J": b"\n",
    "CTRL+K": b"\x0b",
    "CTRL+L": b"\x0c",
    "CTRL+M": b"\r",  # Same as ENTER
    "CTRL+N": b"\x0e",
    "CTRL+O": b"\x0f",
    "CTRL+P": b"\x10",
    "CTRL+Q": b"\x11",
    "CTRL+R": b"\x12",
    "CTRL+S": b"\x13",
    "CTRL+T": b"\x14",
    "CTRL+U": b"\x15",
    "CTRL+V": b"\x16",
    "CTRL+W": b"\x17",
    "CTRL+X": b"\x18",
    "CTRL+Y": b"\x19",
    "CTRL+Z": b"\x1a",
    "CTRL+[": b"\x1b",  # Same as ESC
    "CTRL+\\": b"\x1c",
    "CTRL+]": b"\x1d",
    "CTRL+^": b"\x1e",
    "CTRL+_": b"\x1f",
}

# Pattern to match special keys like {ENTER}, {CTRL+C}, etc.
SPECIAL_KEY_PATTERN = re.compile(r"\{([^}]+)\}")


def parse_keys(input_string: str) -> bytes:
    """Parse a string with special key notation into bytes.

    Args:
        input_string: String with optional special keys like "hello{ENTER}"

    Returns:
        Bytes to send to terminal

    Examples:
        >>> parse_keys("hello")
        b'hello'
        >>> parse_keys("{ENTER}")
        b'\\r'
        >>> parse_keys("test{TAB}more{ENTER}")
        b'test\\tmore\\r'
        >>> parse_keys("{UP}{UP}{ENTER}")
        b'\\x1b[A\\x1b[A\\r'
    """
    result = bytearray()
    pos = 0

    for match in SPECIAL_KEY_PATTERN.finditer(input_string):
        # Add any text before this special key
        if match.start() > pos:
            result.extend(input_string[pos : match.start()].encode("utf-8"))

        # Look up the special key
        key_name = match.group(1).upper()
        if key_name in SPECIAL_KEYS:
            result.extend(SPECIAL_KEYS[key_name])
        else:
            # Unknown special key - pass through as-is
            result.extend(f"{{{match.group(1)}}}".encode())

        pos = match.end()

    # Add any remaining text
    if pos < len(input_string):
        result.extend(input_string[pos:].encode("utf-8"))

    return bytes(result)


def get_available_keys() -> list[str]:
    """Get list of all available special key names."""
    return sorted(SPECIAL_KEYS.keys())
