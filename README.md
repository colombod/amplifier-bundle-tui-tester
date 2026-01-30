# TUI Tester Bundle

Test Terminal User Interface (TUI) applications with AI-assisted visual analysis.

## Overview

This bundle provides capabilities for programmatically testing TUI applications:

- **Spawn** TUI apps in headless terminal sessions
- **Drive** interactions via keystrokes (navigation, input, special keys)
- **Capture** terminal state as text and rendered screenshots
- **Analyze** with AI vision to identify visual/UX issues

Perfect for testing applications built with Textual, urwid, Rich, or any terminal-based UI.

## Installation

Add to your bundle's includes:

```yaml
includes:
  - bundle: git+https://github.com/yourusername/amplifier-bundle-tui-tester@main
```

Or use directly with Amplifier:

```bash
amplifier run --bundle tui-tester
```

## Quick Start

```python
# 1. Spawn a TUI application
result = tui_terminal(operation="spawn", command="python my_tui_app.py")
session_id = result["session_id"]

# 2. Send keystrokes
tui_terminal(operation="send_keys", session_id=session_id, keys="hello{ENTER}")

# 3. Navigate with arrow keys
tui_terminal(operation="send_keys", session_id=session_id, keys="{DOWN}{DOWN}{ENTER}")

# 4. Capture current state (text + screenshot)
capture = tui_terminal(operation="capture", session_id=session_id)
# Returns: {text, ansi, image_path}

# 5. Clean up
tui_terminal(operation="close", session_id=session_id)
```

## Operations

| Operation | Description | Required Params |
|-----------|-------------|-----------------|
| `spawn` | Start TUI app in terminal | `command` |
| `send_keys` | Send keystrokes | `session_id`, `keys` |
| `capture` | Get text + screenshot | `session_id` |
| `close` | End session | `session_id` |
| `list` | List active sessions | - |

## Special Keys

Use curly braces for special keys:

```
{ENTER}     - Enter/Return
{TAB}       - Tab
{ESC}       - Escape
{BACKSPACE} - Backspace

{UP}, {DOWN}, {LEFT}, {RIGHT} - Arrow keys
{HOME}, {END}, {PGUP}, {PGDN} - Navigation

{CTRL+C}    - Interrupt
{CTRL+D}    - EOF
{CTRL+Z}    - Suspend

{F1} - {F12} - Function keys
```

## Agent

Delegate TUI testing tasks to the specialized agent:

```
Use tui-tester:tui-test-analyst to test my Textual application for visual issues
```

The agent will:
1. Spawn your application
2. Navigate through the UI
3. Capture screenshots at each step
4. Analyze for visual/UX issues
5. Provide a detailed report

## Use Cases

### Testing Completion Behavior

```python
# Test slash command completion
tui_terminal(operation="send_keys", session_id=sid, keys="/")
capture1 = tui_terminal(operation="capture", session_id=sid)
# Analyze: Are suggestions showing?

tui_terminal(operation="send_keys", session_id=sid, keys="he{TAB}")
capture2 = tui_terminal(operation="capture", session_id=sid)
# Analyze: Did completion work correctly?
```

### Testing Layout at Different Sizes

```python
# Test small terminal
small = tui_terminal(operation="spawn", command="python app.py", rows=20, cols=60)
capture_small = tui_terminal(operation="capture", session_id=small["session_id"])

# Test large terminal
large = tui_terminal(operation="spawn", command="python app.py", rows=40, cols=120)
capture_large = tui_terminal(operation="capture", session_id=large["session_id"])

# Compare layouts
```

### Visual Regression Testing

```python
# Capture baseline
baseline = tui_terminal(operation="capture", session_id=sid)

# Make changes...

# Capture after changes
after = tui_terminal(operation="capture", session_id=sid)

# Use vision to compare and identify differences
```

## Dependencies

This bundle includes:
- **amplifier-foundation** - Core Amplifier capabilities
- **design-intelligence-enhanced** - AI-powered visual analysis for design evaluation

## Requirements

- Python 3.11+
- pyte (terminal emulation) - auto-installed
- Pillow (image rendering) - auto-installed

## How It Works

1. **Terminal Emulation**: Uses `pyte` to emulate a VT100 terminal
2. **Process Control**: Uses Python's `pty` module to spawn processes in pseudo-terminals
3. **Image Rendering**: Uses PIL to render terminal state to PNG images
4. **Headless Operation**: No X11 or display required - works in CI/CD

## License

MIT
