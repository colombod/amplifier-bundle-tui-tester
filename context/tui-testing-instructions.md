# TUI Testing with AI Assistance

You have access to the `tui_terminal` tool for testing Terminal User Interface applications.

## Overview

This capability allows you to:
1. Launch TUI applications in controlled terminal sessions
2. Interact with them via keystrokes
3. Capture their visual state as both text and screenshots
4. Use AI vision to analyze the visual output and identify issues

## Quick Reference

| Operation | Purpose | Example |
|-----------|---------|---------|
| `spawn` | Start a TUI app | `tui_terminal(operation="spawn", command="python app.py")` |
| `send_keys` | Type or navigate | `tui_terminal(operation="send_keys", session_id="...", keys="hello{ENTER}")` |
| `capture` | Get text + screenshot | `tui_terminal(operation="capture", session_id="...")` |
| `close` | End session | `tui_terminal(operation="close", session_id="...")` |
| `list` | Show active sessions | `tui_terminal(operation="list")` |

## Operations Detail

### spawn

Start a new terminal session with a TUI application.

**Parameters:**
- `command` (required): The command to run (e.g., `"python my_app.py"`, `"amplifier-tui run"`)
- `rows` (optional, default 24): Terminal height in rows
- `cols` (optional, default 80): Terminal width in columns
- `env` (optional): Additional environment variables as dict

**Returns:**
```json
{
  "session_id": "abc123",
  "status": "running",
  "rows": 24,
  "cols": 80
}
```

### send_keys

Send keystrokes to a running session.

**Parameters:**
- `session_id` (required): The session to send keys to
- `keys` (required): The keys to send (see Special Keys below)
- `wait_ms` (optional, default 100): Milliseconds to wait after sending

**Special Keys:**

Use curly braces for special keys:
```
{ENTER}     - Enter/Return key
{TAB}       - Tab key
{ESC}       - Escape key
{BACKSPACE} - Backspace
{DELETE}    - Delete

{UP}        - Arrow up
{DOWN}      - Arrow down
{LEFT}      - Arrow left
{RIGHT}     - Arrow right

{HOME}      - Home key
{END}       - End key
{PGUP}      - Page up
{PGDN}      - Page down

{CTRL+C}    - Ctrl+C (interrupt)
{CTRL+D}    - Ctrl+D (EOF)
{CTRL+Z}    - Ctrl+Z (suspend)
{CTRL+L}    - Ctrl+L (clear)

{F1} - {F12} - Function keys
```

**Examples:**
```python
# Type text and press enter
tui_terminal(operation="send_keys", session_id=sid, keys="hello world{ENTER}")

# Navigate with arrows
tui_terminal(operation="send_keys", session_id=sid, keys="{DOWN}{DOWN}{ENTER}")

# Use slash command
tui_terminal(operation="send_keys", session_id=sid, keys="/help{ENTER}")

# Trigger completion with tab
tui_terminal(operation="send_keys", session_id=sid, keys="/he{TAB}")
```

### capture

Capture the current terminal state.

**Parameters:**
- `session_id` (required): The session to capture

**Returns:**
```json
{
  "text": "Plain text content of terminal...",
  "ansi": "Content with ANSI escape codes...",
  "image_path": "/home/user/.amplifier/tui-sessions/abc123/capture_001.png",
  "rows": 24,
  "cols": 80
}
```

The `image_path` points to a PNG screenshot that can be analyzed with vision capabilities.

### close

Close a terminal session and clean up resources.

**Parameters:**
- `session_id` (required): The session to close

### list

List all active terminal sessions.

**Returns:**
```json
{
  "sessions": [
    {"session_id": "abc123", "command": "python app.py", "status": "running"},
    {"session_id": "def456", "command": "amplifier-tui", "status": "running"}
  ]
}
```

## Testing Workflow

### Basic Testing Pattern

```python
# 1. Spawn the TUI app
result = tui_terminal(operation="spawn", command="uv run amplifier-tui run")
session_id = result["session_id"]

# 2. Wait for app to initialize (send empty or capture)
import time
time.sleep(2)  # Give app time to start

# 3. Capture initial state
initial = tui_terminal(operation="capture", session_id=session_id)

# 4. Interact with the app
tui_terminal(operation="send_keys", session_id=session_id, keys="/help{ENTER}")

# 5. Capture after interaction
after_help = tui_terminal(operation="capture", session_id=session_id)

# 6. Analyze the screenshot with vision
# (use the image_path with vision capabilities)

# 7. Clean up
tui_terminal(operation="close", session_id=session_id)
```

### Testing Completion/Suggestions

```python
# Test slash command completion
tui_terminal(operation="send_keys", session_id=sid, keys="/")
capture1 = tui_terminal(operation="capture", session_id=sid)
# Analyze: Are suggestions visible? How many? Where positioned?

tui_terminal(operation="send_keys", session_id=sid, keys="he")
capture2 = tui_terminal(operation="capture", session_id=sid)
# Analyze: Did suggestions filter correctly?

tui_terminal(operation="send_keys", session_id=sid, keys="{TAB}")
capture3 = tui_terminal(operation="capture", session_id=sid)
# Analyze: Did completion work? What was inserted?
```

### Testing @ Mentions

```python
# Test agent mention completion
tui_terminal(operation="send_keys", session_id=sid, keys="@")
capture = tui_terminal(operation="capture", session_id=sid)
# Analyze: Does agent list appear? Is it readable?
```

## Visual Analysis Guidelines

When analyzing captured screenshots, look for:

**Layout Issues:**
- Elements cut off or not fully visible
- Text overlapping
- Misaligned columns or rows
- Scroll indicators not visible when needed

**UX Problems:**
- Focus/cursor not clearly visible
- Selection highlighting unclear
- Status bar information missing
- Error messages not prominent enough

**Completion/Suggestion Issues:**
- Suggestions not appearing where expected
- Too few suggestions visible (truncated list)
- Wrong content in suggestions (description vs command confusion)
- Tab completion inserting wrong content

**Visual Glitches:**
- ANSI color rendering issues
- Box-drawing characters broken
- Unicode characters not displaying
- Flickering or incomplete redraws

## Agent Available

For comprehensive TUI testing workflows, delegate to **tui-tester:tui-test-analyst** which specializes in:
- Systematic test workflows
- Visual analysis with AI vision
- Issue identification and reporting
- Before/after comparisons

## Troubleshooting

**App doesn't start:**
- Check if command is correct
- Verify dependencies are installed
- Check for missing environment variables

**Keys don't work:**
- Ensure app has finished initializing (wait after spawn)
- Check if app is in correct mode/state
- Try capturing to see current state

**Screenshot is blank/wrong:**
- App may not have rendered yet (increase wait time)
- Terminal size may be too small
- Check if app exited (capture anyway to see error)

**Session not found:**
- Session may have timed out (30 min default)
- App may have crashed (spawn again)
- Check list operation to see active sessions
