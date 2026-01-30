# TUI Terminal Testing Tool

Amplifier tool module for testing TUI (Terminal User Interface) applications.

## Features

- Spawn TUI applications in pseudo-terminals
- Send keystrokes including special keys (arrows, tab, enter, ctrl sequences)
- Capture terminal state as text and PNG screenshots
- Session management for multiple concurrent tests
- Headless operation (no X11 required)

## Installation

```bash
pip install amplifier-module-tool-tui-tester
```

Or with uv:

```bash
uv add amplifier-module-tool-tui-tester
```

## Dependencies

- `pyte>=0.8.0` - Terminal emulation
- `Pillow>=10.0.0` - Image rendering
- `amplifier-core>=0.1.0` - Amplifier framework

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    TUITerminalTool                   │
│  (Tool interface - operations: spawn/send/capture)   │
├─────────────────────────────────────────────────────┤
│                   SessionManager                     │
│  (Manages multiple concurrent terminal sessions)     │
├─────────────────────────────────────────────────────┤
│                    TUISession                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │  PTY Process │ │ pyte Screen  │ │ PIL Renderer │ │
│  │  (pty module)│ │ (emulation)  │ │   (images)   │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────┘
```

## How It Works

1. **Spawn**: Creates a pseudo-terminal (PTY) and executes the command
2. **Terminal Emulation**: pyte emulates a VT100 terminal, processing ANSI sequences
3. **Key Parsing**: Converts `{ENTER}`, `{TAB}`, etc. to actual escape sequences
4. **Image Rendering**: PIL renders the terminal buffer to a PNG with colors
5. **Session Management**: Tracks multiple sessions with automatic cleanup

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
pyright src/

# Linting
ruff check src/
```

## License

MIT
