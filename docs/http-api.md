# Phonegang HTTP API

The HTTP API provides RESTful endpoints and Server-Sent Events (SSE) for remote phone control and real-time screen monitoring.

## Starting the API Server

```bash
phonegang api --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Visit the root endpoint for interactive documentation:
```
http://localhost:8000/
```

## REST Endpoints

### Device Management

**List Devices**
```http
GET /devices
```

Response:
```json
{
  "success": true,
  "count": 2,
  "devices": [
    {
      "serial": "ZY32LQCK3M",
      "model": "Pixel 6",
      "status": "device"
    }
  ]
}
```

### Screen State

**Get Screen**
```http
GET /devices/<serial>/screen
```

Response:
```json
{
  "success": true,
  "output": "...compact tree view...",
  "serial": "ZY32LQCK3M"
}
```

**Render Screen**
```http
GET /devices/<serial>/render?mode=hierarchy
```

Modes: `hierarchy`, `clickable`, `compact`, `spatial`

### Interactions

**Tap Element**
```http
POST /devices/<serial>/tap
Content-Type: application/json

{
  "text": "Login"
}
```

Or by resource ID:
```json
{
  "resource_id": "com.example:id/button"
}
```

**Tap Coordinates**
```http
POST /devices/<serial>/tap_xy
Content-Type: application/json

{
  "x": 500,
  "y": 1000
}
```

**Type Text**
```http
POST /devices/<serial>/type
Content-Type: application/json

{
  "text": "Hello World"
}
```

**Swipe**
```http
POST /devices/<serial>/swipe
Content-Type: application/json

{
  "x1": 500,
  "y1": 1500,
  "x2": 500,
  "y2": 500,
  "duration": 300
}
```

**Press Key**
```http
POST /devices/<serial>/press
Content-Type: application/json

{
  "keycode": "KEYCODE_BACK"
}
```

Common keycodes: `KEYCODE_BACK`, `KEYCODE_HOME`, `KEYCODE_APP_SWITCH`

### Waiting & Synchronization

**Wait for Element**
```http
POST /devices/<serial>/wait
Content-Type: application/json

{
  "text": "Done",
  "timeout": 10
}
```

**Refresh Cache**
```http
POST /devices/<serial>/refresh
```

## Server-Sent Events (SSE)

Real-time screen updates via SSE streams.

### Stream All Devices

```http
GET /stream/screen
```

Streams screen updates for all connected devices. Each event:

```json
{
  "type": "screen_update",
  "serial": "ZY32LQCK3M",
  "timestamp": 1234567890.123,
  "screen": "...compact tree view..."
}
```

### Stream Specific Device

```http
GET /stream/screen/<serial>
```

Example with JavaScript:

```javascript
const eventSource = new EventSource('http://localhost:8000/stream/screen/ZY32LQCK3M');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'screen_update') {
    console.log('Screen updated:', data.screen);
  }
};
```

Example with curl:

```bash
curl -N http://localhost:8000/stream/screen/ZY32LQCK3M
```

## Example: Automation Script

```bash
#!/bin/bash
API="http://localhost:8000"
SERIAL="ZY32LQCK3M"

# Get current screen
curl "$API/devices/$SERIAL/screen"

# Tap Settings
curl -X POST "$API/devices/$SERIAL/tap" \
  -H "Content-Type: application/json" \
  -d '{"text": "Settings"}'

# Wait for settings to load
curl -X POST "$API/devices/$SERIAL/wait" \
  -H "Content-Type: application/json" \
  -d '{"text": "WiFi", "timeout": 5}'

# Tap WiFi
curl -X POST "$API/devices/$SERIAL/tap" \
  -H "Content-Type: application/json" \
  -d '{"text": "WiFi"}'
```

## Example: Python Client

```python
import requests
import json

API_BASE = "http://localhost:8000"
SERIAL = "ZY32LQCK3M"

# List devices
response = requests.get(f"{API_BASE}/devices")
print(response.json())

# Get screen state
response = requests.get(f"{API_BASE}/devices/{SERIAL}/screen")
screen = response.json()
print(screen['output'])

# Tap element
response = requests.post(
    f"{API_BASE}/devices/{SERIAL}/tap",
    json={"text": "Login"}
)
print(response.json())

# Type text
response = requests.post(
    f"{API_BASE}/devices/{SERIAL}/type",
    json={"text": "hello@example.com"}
)
print(response.json())
```

## Example: SSE Stream (Python)

```python
import requests
import json

API_BASE = "http://localhost:8000"
SERIAL = "ZY32LQCK3M"

response = requests.get(f"{API_BASE}/stream/screen/{SERIAL}", stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])

            if data['type'] == 'screen_update':
                print(f"Screen updated at {data['timestamp']}")
                print(data['screen'][:200])  # First 200 chars
```

## CORS Support

The API includes CORS headers, allowing requests from web applications:

```javascript
fetch('http://localhost:8000/devices')
  .then(r => r.json())
  .then(data => console.log(data.devices));
```

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "message": "Error description"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request (missing parameters)
- `404` - Device not found
- `500` - Server error

## Security Considerations

**⚠️ Important:**
- The API has no authentication by default
- Only bind to `localhost` if on untrusted networks
- Use `--host 127.0.0.1` to restrict access to local machine
- Consider adding a reverse proxy with authentication for production use

## Performance Tips

- SSE streams poll every 500ms by default
- Screen state is cached for 2 seconds
- Use `/refresh` endpoint to force immediate update
- Multiple SSE clients can connect simultaneously
