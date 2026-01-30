# Amplifier Bundle: TUI Tester

**AI-assisted testing for Terminal User Interface applications.**

Spawn TUI apps in headless terminals, drive interactions, capture screenshots, and analyze with AI vision.

## Installation

```bash
amplifier bundle add git+https://github.com/colombod/amplifier-bundle-tui-tester@main
amplifier bundle use tui-tester
```

## What's Included

### Tool

| Tool | Purpose |
|------|---------|
| **tui_terminal** | Spawn, drive, and capture TUI applications in headless terminals |

### Agent

| Agent | Purpose |
|-------|---------|
| `tui-tester:tui-test-analyst` | Comprehensive visual analysis and issue identification |

### Dependencies

This bundle includes:
- **amplifier-foundation** - Core Amplifier capabilities
- **design-intelligence-enhanced** - AI-powered visual analysis for professional design evaluation

## Quick Start

### Spawn and Test a TUI Application

```
Spawn my Textual app with command: uv run my-tui-app
```

### Navigate and Capture

```
Send arrow down three times then Enter, and capture a screenshot
```

### Visual Analysis

```
Use tui-tester:tui-test-analyst to analyze my TUI for layout issues and accessibility problems
```

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

## Directory Structure

```
amplifier-bundle-tui-tester/
├── bundle.md                 # Thin entry point
├── behaviors/
│   └── tui-tester.yaml       # Tool + agent composition
├── agents/
│   └── tui-test-analyst.md   # Visual analysis agent
├── context/
│   └── tui-testing-instructions.md
├── examples/
│   └── test-textual-app.md
└── modules/
    └── tool-tui-tester/      # Terminal emulation tool
```

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
