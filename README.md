# Amplifier TUI Tester Bundle

**AI-assisted testing for Terminal User Interface applications**

Test TUI applications by spawning them in headless terminals, driving interactions, and capturing screenshots for AI-powered visual analysis.

## What Is TUI Testing?

TUI Testing with Amplifier lets you verify terminal-based applications:

- **Spawn** TUI apps in isolated headless terminal sessions
- **Drive** interactions via keystrokes (navigation, input, special keys)
- **Capture** terminal state as text and rendered screenshots
- **Analyze** with AI vision to identify visual/UX issues

**Use cases:**

- Visual regression testing for Textual/urwid/Rich applications
- Verifying keyboard navigation and accessibility
- Testing layouts at different terminal sizes
- Automated screenshot documentation
- CI/CD integration for TUI apps

## Components

This bundle provides:

| Component | Description |
|-----------|-------------|
| **tool-tui-terminal** | Tool for spawning, driving, and capturing TUI applications |
| **tui-test-analyst** | Agent for comprehensive visual analysis and issue identification |
| **design-intelligence-enhanced** | AI-powered design evaluation (included dependency) |

## Installation

### Run Directly

```bash
amplifier run --bundle git+https://github.com/colombod/amplifier-bundle-tui-tester@main
```

### Include in Your Bundle

Add to your bundle's `includes:` section:

```yaml
includes:
  - bundle: git+https://github.com/colombod/amplifier-bundle-tui-tester@main
```

## Quick Start

### Test a TUI Application

```
Spawn my Textual app with command: uv run my-tui-app
```

### Navigate and Capture

```
Send arrow down three times then Enter, and capture a screenshot
```

### Visual Analysis

```
Analyze the current TUI screen for layout issues and accessibility problems
```

## Agent

Delegate comprehensive TUI testing to the specialized agent:

```
Use tui-tester:tui-test-analyst to test my Textual application for visual issues.
The app is started with: uv run my-tui-app
```

The agent will:
1. Spawn your application
2. Navigate through the UI systematically
3. Capture screenshots at each step
4. Analyze for visual/UX issues using design principles
5. Provide a detailed report with recommendations

## Use Cases

### Testing Slash Command Completion

```
Spawn my chat app with: uv run amplifier-tui run
Then type "/" and capture a screenshot to see if suggestions appear correctly
```

### Testing at Different Terminal Sizes

```
Test my app at both 80x24 (standard) and 120x40 (large) terminal sizes,
comparing the layout differences
```

### Keyboard Navigation Audit

```
Test keyboard navigation in my Textual app - verify I can reach all interactive 
elements using only Tab, arrows, and Enter
```

### Visual Regression Testing

```
Spawn my app, navigate to the settings screen, capture it, then compare 
against the baseline screenshot at tests/baseline-settings.png
```

## Special Keys Reference

When describing interactions, you can reference these special keys:

| Keys | Description |
|------|-------------|
| Enter, Return | Submit/confirm |
| Tab | Next element / trigger completion |
| Escape | Cancel/close |
| Arrow keys (Up, Down, Left, Right) | Navigation |
| Home, End, Page Up, Page Down | Extended navigation |
| Ctrl+C, Ctrl+D, Ctrl+Z | Interrupt, EOF, Suspend |
| F1 - F12 | Function keys |

## Dependencies

This bundle includes:

- **amplifier-foundation** - Core Amplifier capabilities
- **design-intelligence-enhanced** - AI-powered visual analysis for professional design evaluation

## Troubleshooting

**Session not found**
- Sessions are ephemeral - if the process exited, the session is gone
- Ask to list active sessions to see what's available

**Application not responding to keys**
- Some apps need time to initialize - try waiting before sending keys
- Check if the app requires specific environment variables

**Screenshot looks wrong**
- Verify terminal size matches what your app expects
- Some apps detect terminal capabilities - headless mode may affect rendering

## Contributing

This project welcomes contributions and suggestions.

## License

MIT
