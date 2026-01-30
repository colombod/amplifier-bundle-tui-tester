---
bundle:
  name: tui-tester
  version: 0.1.0
  description: Test TUI applications with AI-assisted visual analysis

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/anderlpz/amplifier-bundle-design-intelligence-enhanced@main
  - bundle: tui-tester:behaviors/tui-tester

agents:
  include:
    - tui-tester:agents/tui-test-analyst
---

# TUI Tester

Test Terminal User Interface applications with AI-powered visual analysis.

## Capabilities

- **Spawn TUI apps** in headless terminal sessions
- **Drive interactions** via keystrokes (navigation, input, special keys)
- **Capture state** as text and rendered screenshots
- **Visual analysis** using AI vision to identify issues

## Quick Start

```python
# Spawn a TUI application
result = tui_terminal(operation="spawn", command="python my_tui_app.py")
session_id = result["session_id"]

# Send keystrokes
tui_terminal(operation="send_keys", session_id=session_id, keys="hello{ENTER}")

# Capture screenshot
capture = tui_terminal(operation="capture", session_id=session_id)
# Returns: {text, ansi, image_path}

# Clean up
tui_terminal(operation="close", session_id=session_id)
```

## Agent

Delegate TUI testing tasks to **tui-tester:agents/tui-test-analyst** for comprehensive testing workflows with visual analysis.

---

@tui-tester:context/tui-testing-instructions.md

---

@foundation:context/shared/common-system-base.md
