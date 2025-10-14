# ABOUTME: Web-based screen viewer for remote phone mirroring
# ABOUTME: Streams device screenshots to a browser using Flask

import io
import time
import threading
from pathlib import Path
from typing import Optional, Dict
from flask import Flask, Response, render_template_string, request, jsonify
from phonegang.device_manager import DeviceManager
from phonegang.adb_wrapper import ADBDevice
from phonegang.controller import DeviceController


# HTML template for the viewer
VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phonegang Viewer - {{ device_name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            min-height: 100vh;
        }
        .header {
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .device-info {
            font-size: 14px;
            color: #888;
        }
        .viewer-container {
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            position: relative;
            max-width: 100%;
        }
        #screen {
            display: block;
            max-width: 100%;
            height: auto;
            cursor: crosshair;
        }
        .controls {
            margin-top: 20px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }
        button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #1d4ed8;
        }
        button:active {
            transform: scale(0.98);
        }
        .status {
            margin-top: 12px;
            padding: 8px 16px;
            background: #333;
            border-radius: 6px;
            font-size: 12px;
            color: #888;
        }
        .fps-control {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #333;
            padding: 8px 16px;
            border-radius: 6px;
        }
        .fps-control label {
            font-size: 14px;
        }
        .fps-control input {
            width: 60px;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #555;
            background: #222;
            color: #fff;
        }
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #888;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📱 Phonegang Viewer</h1>
        <div class="device-info">Device: {{ device_name }}</div>
    </div>

    <div class="viewer-container">
        <img id="screen" src="/stream" alt="Phone Screen">
        <div class="loading" id="loading">Loading...</div>
    </div>

    <div class="controls">
        <button onclick="pressBack()">◀ Back</button>
        <button onclick="pressHome()">⌂ Home</button>
        <button onclick="pressRecents()">☰ Recents</button>
        <button onclick="takeScreenshot()">📷 Screenshot</button>

        <div class="fps-control">
            <label for="fps">FPS:</label>
            <input type="number" id="fps" value="15" min="1" max="30" onchange="updateFPS()">
        </div>
    </div>

    <div class="status" id="status">Ready</div>

    <script>
        const screen = document.getElementById('screen');
        const loading = document.getElementById('loading');
        const status = document.getElementById('status');
        let currentFPS = 15;

        // Get device serial from URL path
        const serial = window.location.pathname.split('/')[1];

        // Hide loading when image loads
        screen.onload = () => {
            loading.style.display = 'none';
        };

        // Click to tap
        screen.addEventListener('click', (e) => {
            const rect = screen.getBoundingClientRect();
            const scaleX = screen.naturalWidth / rect.width;
            const scaleY = screen.naturalHeight / rect.height;

            const x = Math.round((e.clientX - rect.left) * scaleX);
            const y = Math.round((e.clientY - rect.top) * scaleY);

            fetch(`/${serial}/tap`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({x, y})
            })
            .then(r => r.json())
            .then(data => {
                status.textContent = `Tapped at (${x}, ${y})`;
                setTimeout(() => status.textContent = 'Ready', 2000);
            });
        });

        function pressBack() {
            fetch(`/${serial}/back`, {method: 'POST'})
                .then(() => updateStatus('Back pressed'));
        }

        function pressHome() {
            fetch(`/${serial}/home`, {method: 'POST'})
                .then(() => updateStatus('Home pressed'));
        }

        function pressRecents() {
            fetch(`/${serial}/recents`, {method: 'POST'})
                .then(() => updateStatus('Recents pressed'));
        }

        function takeScreenshot() {
            fetch(`/${serial}/screenshot`, {method: 'POST'})
                .then(r => r.json())
                .then(data => updateStatus(`Screenshot saved: ${data.path}`));
        }

        function updateFPS() {
            currentFPS = parseInt(document.getElementById('fps').value);
            // Force reload stream with new FPS
            screen.src = `/${serial}/stream?fps=${currentFPS}&t=${Date.now()}`;
            updateStatus(`FPS updated to ${currentFPS}`);
        }

        function updateStatus(msg) {
            status.textContent = msg;
            setTimeout(() => status.textContent = 'Ready', 3000);
        }

        // Update stream URL with FPS parameter
        screen.src = `/${serial}/stream?fps=${currentFPS}`;
    </script>
</body>
</html>
"""

# Device selector template
SELECTOR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phonegang - Device Selector</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            min-height: 100vh;
        }
        .header {
            margin-bottom: 40px;
            text-align: center;
        }
        .header h1 {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .header p {
            font-size: 16px;
            color: #888;
        }
        .devices-container {
            max-width: 800px;
            width: 100%;
        }
        .device-card {
            background: #2a2a2a;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s, background 0.2s;
            text-decoration: none;
            color: inherit;
        }
        .device-card:hover {
            background: #333;
            transform: translateY(-2px);
            cursor: pointer;
        }
        .device-info h2 {
            font-size: 20px;
            margin-bottom: 8px;
        }
        .device-info .serial {
            font-size: 14px;
            color: #888;
            font-family: monospace;
        }
        .device-info .status {
            display: inline-block;
            margin-top: 8px;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .status.online {
            background: #16a34a;
            color: white;
        }
        .status.offline {
            background: #dc2626;
            color: white;
        }
        .view-button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        .view-button:hover {
            background: #1d4ed8;
        }
        .no-devices {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
        .no-devices h2 {
            font-size: 24px;
            margin-bottom: 12px;
        }
        .refresh-button {
            margin-top: 20px;
            background: #333;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }
        .refresh-button:hover {
            background: #444;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📱 Phonegang</h1>
        <p>Select a device to view and control</p>
    </div>

    <div class="devices-container">
        {% if devices %}
            {% for device in devices %}
            <a href="/{{ device.serial }}" class="device-card">
                <div class="device-info">
                    <h2>{{ device.model or 'Android Device' }}</h2>
                    <div class="serial">{{ device.serial }}</div>
                    <span class="status {{ 'online' if device.state == 'device' else 'offline' }}">
                        {{ device.state }}
                    </span>
                </div>
                <button class="view-button">View →</button>
            </a>
            {% endfor %}
        {% else %}
            <div class="no-devices">
                <h2>No devices found</h2>
                <p>Connect an Android device via USB and enable USB debugging</p>
                <button class="refresh-button" onclick="location.reload()">Refresh</button>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


class PhoneWebViewer:
    """Web-based phone screen viewer."""

    def __init__(self, serial: Optional[str] = None, fps: int = 15):
        """
        Initialize the web viewer.

        Args:
            serial: Device serial number (None for default device)
            fps: Frames per second for screen updates
        """
        self.serial = serial
        self.fps = fps
        self.device: Optional[ADBDevice] = None
        self.controller: Optional[DeviceController] = None
        self._lock = threading.Lock()
        self._last_screenshot_path: Optional[str] = None

        # Initialize device
        manager = DeviceManager()
        device_info = manager.get_device(serial)
        self.serial = device_info.serial
        self.device_name = f"{device_info.serial}"

    def _ensure_connection(self):
        """Ensure device is connected."""
        if self.device is None:
            self.device = ADBDevice(self.serial)
            self.device.connect()
            self.controller = DeviceController(self.device)

    def get_screenshot_stream(self, fps: int):
        """
        Generator that yields screenshots as MJPEG stream.

        Args:
            fps: Frames per second
        """
        def generate():
            with self._lock:
                self._ensure_connection()

            while True:
                try:
                    # Capture screenshot
                    with self._lock:
                        screenshot_path = self.device.take_screenshot()

                    # Read the screenshot
                    with open(screenshot_path, 'rb') as f:
                        frame = f.read()

                    # Yield as MJPEG frame
                    yield (b'--frame\r\n'
                           b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

                    # Sleep for frame rate
                    time.sleep(1.0 / fps)

                except Exception as e:
                    print(f"Error capturing frame: {e}")
                    time.sleep(1)

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def tap(self, x: int, y: int):
        """Tap at coordinates."""
        with self._lock:
            self._ensure_connection()
            self.device.tap(x, y)

    def press_back(self):
        """Press back button."""
        with self._lock:
            self._ensure_connection()
            self.device.press_back()

    def press_home(self):
        """Press home button."""
        with self._lock:
            self._ensure_connection()
            self.device.press_home()

    def press_recents(self):
        """Press recents button."""
        with self._lock:
            self._ensure_connection()
            self.device.shell("input keyevent KEYCODE_APP_SWITCH")

    def take_screenshot_to_disk(self):
        """Take and save a screenshot."""
        with self._lock:
            self._ensure_connection()
            return self.device.take_screenshot()


def create_app(fps: int = 15):
    """
    Create Flask app for phone viewer.

    Args:
        fps: Default frames per second

    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    viewers: Dict[str, PhoneWebViewer] = {}

    def get_viewer(serial: str) -> PhoneWebViewer:
        """Get or create viewer for device."""
        if serial not in viewers:
            viewers[serial] = PhoneWebViewer(serial=serial, fps=fps)
        return viewers[serial]

    @app.route('/')
    def index():
        """Device selector page."""
        manager = DeviceManager()
        devices = manager.list_devices()
        return render_template_string(SELECTOR_TEMPLATE, devices=devices)

    @app.route('/<serial>')
    def device_viewer(serial):
        """Viewer page for specific device."""
        try:
            viewer = get_viewer(serial)
            return render_template_string(VIEWER_TEMPLATE, device_name=viewer.device_name)
        except Exception as e:
            return f"Error: {e}", 404

    @app.route('/<serial>/stream')
    def stream(serial):
        """MJPEG stream of phone screen."""
        try:
            viewer = get_viewer(serial)
            fps_param = int(request.args.get('fps', viewer.fps))
            return viewer.get_screenshot_stream(fps_param)
        except Exception as e:
            return f"Error: {e}", 500

    @app.route('/<serial>/tap', methods=['POST'])
    def tap(serial):
        """Handle tap events."""
        try:
            viewer = get_viewer(serial)
            data = request.json
            viewer.tap(data['x'], data['y'])
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/<serial>/back', methods=['POST'])
    def back(serial):
        """Press back button."""
        try:
            viewer = get_viewer(serial)
            viewer.press_back()
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/<serial>/home', methods=['POST'])
    def home(serial):
        """Press home button."""
        try:
            viewer = get_viewer(serial)
            viewer.press_home()
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/<serial>/recents', methods=['POST'])
    def recents(serial):
        """Press recents button."""
        try:
            viewer = get_viewer(serial)
            viewer.press_recents()
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/<serial>/screenshot', methods=['POST'])
    def screenshot(serial):
        """Take and save screenshot."""
        try:
            viewer = get_viewer(serial)
            path = viewer.take_screenshot_to_disk()
            return jsonify({'status': 'ok', 'path': path})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return app


def start_viewer(host: str = '0.0.0.0', port: int = 5000, fps: int = 15):
    """
    Start the web viewer server.

    Args:
        host: Host to bind to (0.0.0.0 for all interfaces)
        port: Port to listen on
        fps: Frames per second for screen updates
    """
    app = create_app(fps=fps)
    print(f"Starting phone viewer on http://{host}:{port}")
    print(f"Default streaming FPS: {fps}")
    app.run(host=host, port=port, threaded=True)
