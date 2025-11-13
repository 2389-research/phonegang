# Phonegang MCP Server Setup

This document explains how to set up the phonegang MCP server so Claude Code can directly interact with your Android phone.

## Prerequisites

1. Android phone with USB debugging enabled
2. USB cable to connect phone to computer
3. phonegang installed: `uv sync`
4. Phone authorized (run `adb devices` once and accept prompt on phone)

## MCP Configuration

Add this to your Claude Code MCP settings file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "phonegang": {
      "command": "uv",
      "args": ["--directory", "/path/to/phonegang", "run", "phonegang-mcp"]
    }
  }
}
```

**Note:** Update the path `/path/to/phonegang` to match your actual phonegang installation directory.

## Restart Claude Code

After adding the configuration, restart Claude Code to load the MCP server.

## Verify Connection

In Claude Code, you should now see phonegang MCP tools available. Try:

```
Can you list my connected Android devices?
```

Claude will use the `list_devices` tool to show your connected phones.

## Available Tools

### High-Level Tools
- `get_screen()` - Get current screen state as compact tree view
- `tap(text=..., resource_id=...)` - Tap an element
- `type_text(text)` - Type text into focused field
- `wait_for(text=..., timeout=10)` - Wait for element to appear

### Low-Level Tools
- `tap_xy(x, y)` - Tap at specific coordinates
- `swipe(x1, y1, x2, y2, duration=300)` - Swipe gesture
- `press_key(keycode)` - Press hardware key (KEYCODE_BACK, KEYCODE_HOME, etc.)
- `get_ui_dump()` - Get raw XML accessibility tree

### Device Management
- `list_devices()` - Show all connected devices

### Cache Control
- `refresh()` - Force fresh UI dump, ignore cache
- `render_screen(mode)` - Get formatted tree (hierarchy/clickable/compact/spatial)

## Example Interactions

**Explore what's on screen:**
```
"What's currently showing on my phone?"
```

**Automate a task:**
```
"Open Settings, find WiFi, and tap it"
```

**Wait for UI state:**
```
"Wait for the 'Done' button to appear, then tap it"
```

## Troubleshooting

**No devices found:**
- Check USB connection
- Run `adb devices` and accept authorization on phone
- Make sure USB debugging is enabled

**Connection errors:**
- Kill existing adb server: `adb kill-server`
- Reconnect phone

**Tools not appearing:**
- Check MCP config path is correct
- Restart Claude Code
- Check Claude Code logs for MCP server errors
