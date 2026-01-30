# Example: Testing a Textual TUI Application

This example demonstrates how to use tui-tester to test a Textual-based TUI application.

## Scenario

You have a TUI application like `amplifier-tui` and want to test:
1. Initial rendering
2. Slash command completion (`/help`, `/status`, etc.)
3. Agent mention completion (`@explorer`, `@zen-architect`, etc.)
4. Keyboard navigation

## Step-by-Step Testing

### 1. Launch the Application

```python
# Spawn the TUI with larger terminal for better visibility
result = tui_terminal(
    operation="spawn",
    command="uv run amplifier-tui run",
    rows=30,
    cols=100
)
session_id = result["session_id"]

# Wait for initialization
import time
time.sleep(2)

# Capture initial state
initial = tui_terminal(operation="capture", session_id=session_id)
print(f"Initial screenshot: {initial['image_path']}")
```

### 2. Test Slash Command Completion

```python
# Type / to trigger command completion
tui_terminal(operation="send_keys", session_id=session_id, keys="/")
time.sleep(0.5)

slash_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Are suggestions visible? How many? Where positioned?

# Filter by typing more
tui_terminal(operation="send_keys", session_id=session_id, keys="he")
time.sleep(0.3)

filtered_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Did suggestions filter to /help?

# Accept with Tab
tui_terminal(operation="send_keys", session_id=session_id, keys="{TAB}")
time.sleep(0.3)

tab_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Did /help get inserted into input?

# Clear and try again
tui_terminal(operation="send_keys", session_id=session_id, keys="{CTRL+U}")
```

### 3. Test @ Agent Mention

```python
# Type @ to trigger agent completion
tui_terminal(operation="send_keys", session_id=session_id, keys="@")
time.sleep(0.5)

at_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Does agent list appear?

# Filter by typing
tui_terminal(operation="send_keys", session_id=session_id, keys="exp")
time.sleep(0.3)

filtered_at_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Did it filter to explorer agents?
```

### 4. Test Navigation

```python
# Navigate through suggestions
for _ in range(3):
    tui_terminal(operation="send_keys", session_id=session_id, keys="{DOWN}")
    time.sleep(0.2)
    
down_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Did selection move down?

# Navigate back up
tui_terminal(operation="send_keys", session_id=session_id, keys="{UP}{UP}")
time.sleep(0.2)

up_capture = tui_terminal(operation="capture", session_id=session_id)
# Check: Did selection move up?
```

### 5. Cleanup

```python
# Always close the session
tui_terminal(operation="close", session_id=session_id)
```

## What to Look For

When analyzing the captured screenshots:

### Layout Issues
- Suggestions appearing at wrong position (bottom vs inline)
- List truncated - only N items visible when more expected
- Elements overlapping or cut off
- Scroll indicators missing

### Content Issues
- Wrong content in suggestions (descriptions vs commands mixed up)
- Tab completion inserting wrong text
- Filter not working correctly
- Missing items in list

### Visual Issues
- Colors not rendering correctly
- Box-drawing characters broken
- Focus indicator not visible
- Status bar information missing or stale

## Automated Testing with Agent

For comprehensive automated testing, delegate to the tui-test-analyst:

```
Use tui-tester:tui-test-analyst to:
1. Launch amplifier-tui
2. Test slash command completion (/, /help, /status)
3. Test @ agent mentions
4. Verify suggestions are visible and properly positioned
5. Check that tab completion works correctly
6. Report any visual issues found with screenshots as evidence
```

The agent will execute the tests systematically and provide a detailed report with screenshots.
