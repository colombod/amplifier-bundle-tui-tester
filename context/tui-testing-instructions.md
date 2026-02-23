# TUI Testing with AI Assistance

You have access to the `tui_terminal` tool for testing Terminal User Interface applications.

## Overview

This capability allows you to:
1. Launch TUI applications in controlled terminal sessions
2. Interact with them via keystrokes
3. Resize the terminal dynamically to test responsive layouts
4. Capture their visual state as both text and screenshots
5. Use AI vision to analyze the visual output and identify issues

## Quick Reference

| Operation | Purpose | Example |
|-----------|---------|---------|
| `spawn` | Start a TUI app | `tui_terminal(operation="spawn", command="python app.py")` |
| `send_keys` | Type or navigate | `tui_terminal(operation="send_keys", session_id="...", keys="hello{ENTER}")` |
| `capture` | Get text + screenshot | `tui_terminal(operation="capture", session_id="...")` |
| `resize` | Change terminal size | `tui_terminal(operation="resize", session_id="...", rows=40, cols=120)` |
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
  "text": "ANSI-escaped text content of terminal...",
  "ansi": "Content with ANSI escape codes...",
  "image_path": "/home/user/.amplifier/tui-sessions/abc123/capture_001.png",
  "rows": 24,
  "cols": 80
}
```

The `text` field returns proper ANSI-escaped text preserving colors and formatting (not just plain text). The `image_path` points to a PNG screenshot that can be analyzed with vision capabilities.

### resize

Resize a running terminal session. The new dimensions take effect immediately and a `SIGWINCH` signal is sent to the child process, causing well-behaved TUI applications to detect the size change and re-render their layout.

**Parameters:**
- `session_id` (required): The session to resize
- `rows` (optional): New terminal height in rows
- `cols` (optional): New terminal width in columns

Provide at least one of `rows` or `cols`. Any omitted dimension stays unchanged.

**Returns:**
```json
{
  "session_id": "abc123",
  "rows": 40,
  "cols": 120,
  "status": "resized"
}
```

**Examples:**
```python
# Resize both dimensions
tui_terminal(operation="resize", session_id=sid, rows=40, cols=120)

# Resize only width (height stays the same)
tui_terminal(operation="resize", session_id=sid, cols=60)

# Resize only height (width stays the same)
tui_terminal(operation="resize", session_id=sid, rows=50)
```

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

### Responsive Testing Pattern

Test how a TUI application adapts to different terminal sizes by spawning at one size, capturing, resizing, and capturing again.

```python
# 1. Spawn at a standard desktop size
result = tui_terminal(operation="spawn", command="python my_app.py", rows=40, cols=120)
session_id = result["session_id"]

# 2. Wait for initialization
tui_terminal(operation="send_keys", session_id=session_id, keys="", wait_ms=2000)

# 3. Capture at the initial (large) size
large = tui_terminal(operation="capture", session_id=session_id)
# Analyze: baseline layout at 120 cols

# 4. Resize to a narrow terminal
tui_terminal(operation="resize", session_id=session_id, rows=40, cols=60)

# 5. Give the app a moment to re-render
tui_terminal(operation="send_keys", session_id=session_id, keys="", wait_ms=500)

# 6. Capture at the narrow size
narrow = tui_terminal(operation="capture", session_id=session_id)
# Analyze: does the layout adapt? Any truncation or overlap?

# 7. Resize to a very small terminal
tui_terminal(operation="resize", session_id=session_id, rows=15, cols=40)
tui_terminal(operation="send_keys", session_id=session_id, keys="", wait_ms=500)
small = tui_terminal(operation="capture", session_id=session_id)
# Analyze: minimum viable size — is the app still usable?

# 8. Clean up
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

**Responsive Layout Issues:**
- Elements that overlap or disappear at smaller terminal sizes
- Content that fails to reflow when width changes
- Panels that collapse incorrectly after resize
- Scroll regions that do not adjust to new height

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

**Resize has no visible effect:**
- The application may not handle SIGWINCH — capture to check if layout changed
- Send a no-op keystroke (`keys=""`) after resize to give the app time to re-render
- Some frameworks need an explicit redraw; try `{CTRL+L}` after resize
- Verify the app is still running with `list` — a crash during resize leaves a dead session

**Layout looks wrong after resize:**
- Capture both before and after to compare
- Try resizing back to the original dimensions to see if the layout recovers
- Some TUI frameworks have minimum size requirements — going below them can cause artifacts
