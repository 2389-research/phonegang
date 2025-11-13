# ABOUTME: HTTP API for phonegang MCP server
# ABOUTME: Provides REST and SSE endpoints for remote phone control

import json
import time
from typing import Optional, Generator
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from phonegang.mcp_server import MCPPhonegangServer
from phonegang.device_manager import DeviceManager
from phonegang.config import (
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    SCREEN_STREAM_POLL_INTERVAL_SECONDS,
    SCREEN_STREAM_ERROR_RETRY_DELAY_SECONDS,
)


def create_http_api(host: str = DEFAULT_HTTP_HOST, port: int = DEFAULT_HTTP_PORT) -> Flask:
    """
    Create Flask app with HTTP API for MCP server.

    Args:
        host: Host to bind to (default: 127.0.0.1 for localhost-only access)
        port: Port to listen on

    Returns:
        Flask app instance

    Security Note:
        Defaults to localhost (127.0.0.1) for security. Use '0.0.0.0' to bind to
        all interfaces, but only do this in trusted networks with proper firewall rules.
    """
    app = Flask(__name__)
    CORS(app)  # Enable CORS for web clients

    # Create MCP server instance
    mcp_server = MCPPhonegangServer()

    # Store for SSE clients
    sse_clients = []

    @app.route('/')
    def index():
        """API documentation."""
        return jsonify({
            "name": "Phonegang HTTP API",
            "version": "1.0.0",
            "endpoints": {
                "GET /devices": "List connected devices",
                "GET /devices/<serial>/screen": "Get current screen state",
                "POST /devices/<serial>/tap": "Tap element by text or resource_id",
                "POST /devices/<serial>/tap_xy": "Tap at coordinates (x, y)",
                "POST /devices/<serial>/type": "Type text (body: {text: string})",
                "POST /devices/<serial>/swipe": "Swipe gesture (body: {x1, y1, x2, y2, duration?})",
                "POST /devices/<serial>/press": "Press key (body: {keycode: string})",
                "POST /devices/<serial>/wait": "Wait for element (body: {text?, resource_id?, timeout?})",
                "GET /devices/<serial>/ui_dump": "Get raw XML UI dump",
                "POST /devices/<serial>/refresh": "Force refresh UI cache",
                "GET /devices/<serial>/render": "Render screen (query: mode=hierarchy|clickable|compact|spatial)",
                "GET /stream/screen": "SSE stream of screen updates for all devices",
                "GET /stream/screen/<serial>": "SSE stream of screen updates for specific device"
            }
        })

    @app.route('/devices', methods=['GET'])
    def list_devices():
        """List all connected devices."""
        result = mcp_server.list_devices()
        return jsonify(result)

    @app.route('/devices/<serial>/screen', methods=['GET'])
    def get_screen(serial):
        """Get current screen state."""
        result = mcp_server.get_screen(serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/tap', methods=['POST'])
    def tap(serial):
        """Tap element by text or resource_id."""
        data = request.json or {}
        text = data.get('text')
        resource_id = data.get('resource_id')

        result = mcp_server.tap(text=text, resource_id=resource_id, serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/tap_xy', methods=['POST'])
    def tap_xy(serial):
        """Tap at specific coordinates."""
        data = request.json or {}
        x = data.get('x')
        y = data.get('y')

        if x is None or y is None:
            return jsonify({
                "success": False,
                "message": "Missing required fields: x, y"
            }), 400

        result = mcp_server.tap_xy(x=int(x), y=int(y), serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/type', methods=['POST'])
    def type_text(serial):
        """Type text into focused field."""
        data = request.json or {}
        text = data.get('text')

        if not text:
            return jsonify({
                "success": False,
                "message": "Missing required field: text"
            }), 400

        result = mcp_server.type_text(text=text, serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/swipe', methods=['POST'])
    def swipe(serial):
        """Perform swipe gesture."""
        data = request.json or {}
        x1 = data.get('x1')
        y1 = data.get('y1')
        x2 = data.get('x2')
        y2 = data.get('y2')
        duration = data.get('duration', 300)

        if None in [x1, y1, x2, y2]:
            return jsonify({
                "success": False,
                "message": "Missing required fields: x1, y1, x2, y2"
            }), 400

        result = mcp_server.swipe(
            x1=int(x1), y1=int(y1),
            x2=int(x2), y2=int(y2),
            duration=int(duration),
            serial=serial
        )
        return jsonify(result)

    @app.route('/devices/<serial>/press', methods=['POST'])
    def press_key(serial):
        """Press hardware/software key."""
        data = request.json or {}
        keycode = data.get('keycode')

        if not keycode:
            return jsonify({
                "success": False,
                "message": "Missing required field: keycode"
            }), 400

        result = mcp_server.press_key(keycode=keycode, serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/wait', methods=['POST'])
    def wait_for(serial):
        """Wait for element to appear."""
        data = request.json or {}
        text = data.get('text')
        resource_id = data.get('resource_id')
        timeout = data.get('timeout', 10)

        result = mcp_server.wait_for(
            text=text,
            resource_id=resource_id,
            timeout=int(timeout),
            serial=serial
        )
        return jsonify(result)

    @app.route('/devices/<serial>/ui_dump', methods=['GET'])
    def get_ui_dump(serial):
        """Get raw XML UI dump."""
        result = mcp_server.get_ui_dump(serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/refresh', methods=['POST'])
    def refresh(serial):
        """Force refresh UI cache."""
        result = mcp_server.refresh(serial=serial)
        return jsonify(result)

    @app.route('/devices/<serial>/render', methods=['GET'])
    def render_screen(serial):
        """Render screen in specified format."""
        mode = request.args.get('mode', 'compact')
        result = mcp_server.render_screen(mode=mode, serial=serial)
        return jsonify(result)

    @app.route('/stream/screen', methods=['GET'])
    def stream_all_screens():
        """SSE stream of screen updates for all devices."""
        def generate():
            manager = DeviceManager()
            last_states = {}

            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Screen stream started'})}\n\n"

            while True:
                try:
                    devices = manager.list_devices()

                    for device in devices:
                        serial = device.serial

                        # Get screen state
                        result = mcp_server.get_screen(serial=serial)

                        if result.get('success'):
                            current_state = result.get('output', '')

                            # Only send if state changed
                            if last_states.get(serial) != current_state:
                                last_states[serial] = current_state

                                event_data = {
                                    'type': 'screen_update',
                                    'serial': serial,
                                    'timestamp': time.time(),
                                    'screen': current_state
                                }

                                yield f"data: {json.dumps(event_data)}\n\n"

                    time.sleep(SCREEN_STREAM_POLL_INTERVAL_SECONDS)

                except Exception as e:
                    error_data = {
                        'type': 'error',
                        'message': str(e)
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    time.sleep(SCREEN_STREAM_ERROR_RETRY_DELAY_SECONDS)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    @app.route('/stream/screen/<serial>', methods=['GET'])
    def stream_device_screen(serial):
        """SSE stream of screen updates for specific device."""
        def generate():
            last_state = None

            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'serial': serial, 'message': 'Screen stream started'})}\n\n"

            while True:
                try:
                    # Get screen state
                    result = mcp_server.get_screen(serial=serial)

                    if result.get('success'):
                        current_state = result.get('output', '')

                        # Only send if state changed
                        if last_state != current_state:
                            last_state = current_state

                            event_data = {
                                'type': 'screen_update',
                                'serial': serial,
                                'timestamp': time.time(),
                                'screen': current_state
                            }

                            yield f"data: {json.dumps(event_data)}\n\n"
                    else:
                        error_data = {
                            'type': 'error',
                            'serial': serial,
                            'message': result.get('error', 'Unknown error')
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"

                    time.sleep(SCREEN_STREAM_POLL_INTERVAL_SECONDS)

                except Exception as e:
                    error_data = {
                        'type': 'error',
                        'serial': serial,
                        'message': str(e)
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    time.sleep(SCREEN_STREAM_ERROR_RETRY_DELAY_SECONDS)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    return app


def start_http_api(host: str = DEFAULT_HTTP_HOST, port: int = DEFAULT_HTTP_PORT):
    """
    Start the HTTP API server.

    Args:
        host: Host to bind to (default: 127.0.0.1 for localhost-only access)
        port: Port to listen on

    Security Note:
        Defaults to localhost (127.0.0.1) for security. Use '0.0.0.0' to bind to
        all interfaces, but only do this in trusted networks with proper firewall rules.
    """
    app = create_http_api(host, port)
    print(f"Starting Phonegang HTTP API on http://{host}:{port}")
    print(f"API documentation: http://{host}:{port}/")
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    start_http_api()
