# ABOUTME: MCP-compliant HTTP transport for phonegang
# ABOUTME: Implements streamable HTTP according to MCP specification

import json
import uuid
import asyncio
import secrets
import time
from typing import Dict, Optional, Any
from flask import Flask, request, Response, stream_with_context, redirect, render_template_string
from flask_cors import CORS
from phonegang.mcp_server import MCPPhonegangServer
from phonegang.config import (
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    OAUTH_CODE_EXPIRY_SECONDS,
    OAUTH_TOKEN_EXPIRY_SECONDS,
)


class MCPHTTPTransport:
    """MCP-compliant HTTP transport using SSE."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.mcp_server = MCPPhonegangServer()
        # OAuth state
        self.oauth_codes: Dict[str, Dict[str, Any]] = {}  # code -> {expires_at, used, client_id, redirect_uri, code_challenge}
        self.oauth_tokens: Dict[str, Dict[str, Any]] = {}  # token -> {expires_at, client_id, scope}
        self.oauth_clients: Dict[str, Dict[str, Any]] = {}  # client_id -> {client_secret, redirect_uris, name}

    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": asyncio.get_event_loop().time()
        }
        return session_id

    def validate_session(self, session_id: Optional[str]) -> bool:
        """Validate session ID."""
        if session_id is None:
            return False
        return session_id in self.sessions

    async def handle_message(self, message: dict, session_id: Optional[str] = None) -> dict:
        """
        Handle JSON-RPC message.

        Args:
            message: JSON-RPC message
            session_id: Optional session ID

        Returns:
            JSON-RPC response
        """
        # Validate JSON-RPC format
        if "jsonrpc" not in message or message["jsonrpc"] != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: missing or invalid jsonrpc version"
                },
                "id": message.get("id")
            }

        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        # Handle MCP protocol messages
        if method == "initialize":
            # Initialize session
            new_session_id = self.create_session()
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "phonegang",
                        "version": "0.1.0"
                    },
                    "_meta": {
                        "sessionId": new_session_id
                    }
                },
                "id": msg_id
            }

        # For MCP over HTTP, sessions are optional
        # Only validate session if one was provided
        if session_id and not self.validate_session(session_id):
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": "Invalid session"
                },
                "id": msg_id
            }

        # Handle tool calls
        if method == "tools/list":
            tools = [
                {
                    "name": "list_devices",
                    "description": "List all connected Android devices",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_screen",
                    "description": "Get current screen state",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "serial": {"type": "string", "description": "Device serial"}
                        }
                    }
                },
                {
                    "name": "tap",
                    "description": "Tap element by text or resource_id",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "resource_id": {"type": "string"},
                            "serial": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "type_text",
                    "description": "Type text into focused field",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "serial": {"type": "string"}
                        },
                        "required": ["text"]
                    }
                },
                {
                    "name": "tap_xy",
                    "description": "Tap at coordinates",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "serial": {"type": "string"}
                        },
                        "required": ["x", "y"]
                    }
                },
                {
                    "name": "swipe",
                    "description": "Swipe gesture",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "x1": {"type": "number"},
                            "y1": {"type": "number"},
                            "x2": {"type": "number"},
                            "y2": {"type": "number"},
                            "duration": {"type": "number"},
                            "serial": {"type": "string"}
                        },
                        "required": ["x1", "y1", "x2", "y2"]
                    }
                },
                {
                    "name": "press_key",
                    "description": "Press hardware key",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "keycode": {"type": "string"},
                            "serial": {"type": "string"}
                        },
                        "required": ["keycode"]
                    }
                },
                {
                    "name": "render_screen",
                    "description": "Render screen in format",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["hierarchy", "clickable", "compact", "spatial"]
                            },
                            "serial": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "take_screenshot",
                    "description": "Take screenshot and return as base64 image",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "serial": {"type": "string", "description": "Device serial"}
                        }
                    }
                }
            ]

            return {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": msg_id
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # Call the tool
            tool_method = getattr(self.mcp_server, tool_name, None)
            if tool_method is None:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    },
                    "id": msg_id
                }

            result = tool_method(**arguments)

            # Handle screenshot results specially (return as image)
            if tool_name == "take_screenshot" and result.get("success") and "image" in result:
                content = [
                    {
                        "type": "image",
                        "data": result["image"],
                        "mimeType": result.get("mime_type", "image/png")
                    }
                ]
                # Also include success message
                if "serial" in result:
                    content.append({
                        "type": "text",
                        "text": f"Screenshot from device {result['serial']}"
                    })
            else:
                # Regular text response
                content = [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]

            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": content
                },
                "id": msg_id
            }

        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": msg_id
            }


OAUTH_CONSENT_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Phonegang - Authorize Access</title>
<style>
body { font-family: sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
.card { border: 1px solid #ddd; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h1 { color: #333; }
.info { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0; }
button { background: #2563eb; color: white; border: none; padding: 12px 24px;
         border-radius: 6px; font-size: 16px; cursor: pointer; width: 100%; }
button:hover { background: #1d4ed8; }
.warning { color: #666; font-size: 14px; margin-top: 20px; }
</style>
</head>
<body>
<div class="card">
<h1>📱 Phonegang</h1>
<p>An application is requesting access to control your Android devices.</p>
<div class="info">
<strong>Permissions requested:</strong>
<ul>
<li>View connected devices</li>
<li>Read screen state</li>
<li>Control device (tap, type, swipe)</li>
</ul>
</div>
<form method="POST">
<!-- Hidden fields to preserve OAuth parameters -->
{% if client_id %}<input type="hidden" name="client_id" value="{{ client_id }}">{% endif %}
{% if redirect_uri %}<input type="hidden" name="redirect_uri" value="{{ redirect_uri }}">{% endif %}
{% if state %}<input type="hidden" name="state" value="{{ state }}">{% endif %}
{% if scope %}<input type="hidden" name="scope" value="{{ scope }}">{% endif %}
{% if response_type %}<input type="hidden" name="response_type" value="{{ response_type }}">{% endif %}
{% if code_challenge %}<input type="hidden" name="code_challenge" value="{{ code_challenge }}">{% endif %}
{% if code_challenge_method %}<input type="hidden" name="code_challenge_method" value="{{ code_challenge_method }}">{% endif %}
<button type="submit">Authorize Access</button>
</form>
<p class="warning">Only authorize applications you trust.</p>
</div>
</body>
</html>
"""


def create_mcp_http_server(host: str = DEFAULT_HTTP_HOST, port: int = DEFAULT_HTTP_PORT, auth_token: Optional[str] = None, base_url: Optional[str] = None) -> Flask:
    """
    Create MCP-compliant HTTP server.

    Args:
        host: Host to bind to (default: 127.0.0.1 for localhost-only access)
        port: Port to listen on
        auth_token: Optional Bearer token for authentication (None = no auth)
        base_url: Base URL for OAuth metadata (e.g., http://example.com:8081)

    Returns:
        Flask app

    Security Note:
        Defaults to localhost (127.0.0.1) for security. Use '0.0.0.0' to bind to
        all interfaces, but only do this in trusted networks with proper firewall rules.
    """
    app = Flask(__name__)
    CORS(app, origins="*", allow_headers=["*"], expose_headers=["*"])

    if base_url is None:
        base_url = f"http://{host}:{port}"

    transport = MCPHTTPTransport()

    def check_auth():
        """Check authentication if required."""
        if auth_token is None:
            return True  # No auth required

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Check if it's the static token
        if token == auth_token:
            return True

        # Check if it's an OAuth token
        if token in transport.oauth_tokens:
            token_data = transport.oauth_tokens[token]
            if token_data['expires_at'] > time.time():
                return True
            else:
                # Token expired
                del transport.oauth_tokens[token]

        return False

    @app.route("/.well-known/oauth-authorization-server", methods=["GET"])
    def oauth_metadata():
        """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
        return {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/oauth/authorize",
            "token_endpoint": f"{base_url}/oauth/token",
            "registration_endpoint": f"{base_url}/oauth/register",
            "scopes_supported": [
                "read:devices",
                "read:screen",
                "write:control"
            ],
            "response_types_supported": [
                "code"
            ],
            "grant_types_supported": [
                "authorization_code",
                "client_credentials"
            ],
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
                "none"
            ],
            "code_challenge_methods_supported": [
                "S256",
                "plain"
            ],
            "service_documentation": f"{base_url}/docs"
        }

    @app.route("/oauth/register", methods=["POST"])
    def oauth_register():
        """Dynamic Client Registration (RFC 7591)."""
        data = request.json

        if not data:
            return {"error": "invalid_request", "error_description": "Request body required"}, 400

        # Generate client credentials
        client_id = secrets.token_urlsafe(16)
        client_secret = secrets.token_urlsafe(32)

        # Get redirect URIs
        redirect_uris = data.get("redirect_uris", [])
        if not redirect_uris:
            return {"error": "invalid_redirect_uri", "error_description": "At least one redirect_uri required"}, 400

        # Store client
        transport.oauth_clients[client_id] = {
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
            "client_name": data.get("client_name", "Unnamed Client"),
            "grant_types": data.get("grant_types", ["authorization_code"]),
            "response_types": data.get("response_types", ["code"]),
            "scope": data.get("scope", "read:devices read:screen write:control"),
            "created_at": time.time()
        }

        # Return client credentials
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_secret_expires_at": 0,  # Never expires
            "redirect_uris": redirect_uris,
            "grant_types": transport.oauth_clients[client_id]["grant_types"],
            "response_types": transport.oauth_clients[client_id]["response_types"],
            "client_name": transport.oauth_clients[client_id]["client_name"],
            "scope": transport.oauth_clients[client_id]["scope"]
        }, 201

    @app.route("/oauth/authorize", methods=["GET", "POST"])
    def oauth_authorize():
        """OAuth 2.0 authorization endpoint with PKCE support."""
        # Get parameters from query string (GET) or form data (POST)
        client_id = request.args.get("client_id") or request.form.get("client_id")
        redirect_uri = request.args.get("redirect_uri") or request.form.get("redirect_uri")
        state = request.args.get("state") or request.form.get("state")
        scope = request.args.get("scope") or request.form.get("scope") or "read:devices read:screen write:control"
        response_type = request.args.get("response_type") or request.form.get("response_type") or "code"
        code_challenge = request.args.get("code_challenge") or request.form.get("code_challenge")
        code_challenge_method = request.args.get("code_challenge_method") or request.form.get("code_challenge_method") or "plain"

        # Validate client_id and redirect_uri only if client is registered
        # For development, we allow unregistered clients (client_id can be anything)
        if client_id and client_id in transport.oauth_clients:
            # Client is registered, validate redirect_uri
            if redirect_uri and redirect_uri not in transport.oauth_clients[client_id]["redirect_uris"]:
                return {"error": "invalid_redirect_uri", "error_description": "redirect_uri not registered for this client"}, 400

        if request.method == "GET":
            # Show consent page with all OAuth parameters as hidden fields
            return render_template_string(
                OAUTH_CONSENT_PAGE,
                client_id=client_id,
                redirect_uri=redirect_uri,
                state=state,
                scope=scope,
                response_type=response_type,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method
            )

        # POST - user authorized
        if not redirect_uri:
            return {"error": "redirect_uri required"}, 400

        if response_type != "code":
            return {"error": "unsupported_response_type", "error_description": "Only 'code' is supported"}, 400

        # Generate authorization code
        code = secrets.token_urlsafe(32)
        transport.oauth_codes[code] = {
            "expires_at": time.time() + OAUTH_CODE_EXPIRY_SECONDS,
            "used": False,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method
        }

        # Redirect back with code
        redirect_url = f"{redirect_uri}?code={code}"
        if state:
            redirect_url += f"&state={state}"

        return redirect(redirect_url)

    @app.route("/oauth/token", methods=["POST"])
    def oauth_token():
        """OAuth 2.0 token endpoint with PKCE support."""
        import hashlib
        import base64

        # OAuth 2.0 spec requires application/x-www-form-urlencoded, but we also support JSON
        def get_param(name):
            """Get parameter from form data or JSON body."""
            if request.form:
                return request.form.get(name)
            elif request.is_json:
                return request.json.get(name)
            return None

        grant_type = get_param("grant_type")

        if grant_type == "authorization_code":
            code = get_param("code")
            client_id = get_param("client_id")
            client_secret = get_param("client_secret")
            redirect_uri = get_param("redirect_uri")
            code_verifier = get_param("code_verifier")

            if not code or code not in transport.oauth_codes:
                return {"error": "invalid_grant", "error_description": "Invalid code"}, 400

            code_data = transport.oauth_codes[code]

            # Check if expired
            if code_data["expires_at"] < time.time():
                del transport.oauth_codes[code]
                return {"error": "invalid_grant", "error_description": "Code expired"}, 400

            # Check if already used
            if code_data["used"]:
                return {"error": "invalid_grant", "error_description": "Code already used"}, 400

            # For PKCE flows, client_id in token request is optional
            # If client_id is provided, it must match; if not, use the one from authorization
            if client_id:
                # Client sent client_id, validate it matches
                if code_data.get("client_id") and client_id != code_data["client_id"]:
                    return {"error": "invalid_client", "error_description": "Client mismatch"}, 400

                # Only validate credentials if client is registered
                if client_id in transport.oauth_clients:
                    expected_secret = transport.oauth_clients[client_id]["client_secret"]
                    if client_secret != expected_secret:
                        return {"error": "invalid_client", "error_description": "Invalid client credentials"}, 401
            else:
                # Client didn't send client_id (valid for PKCE), use the one from authorization
                client_id = code_data.get("client_id")

            # Validate redirect_uri
            if redirect_uri != code_data["redirect_uri"]:
                return {"error": "invalid_grant", "error_description": "Redirect URI mismatch"}, 400

            # Validate PKCE if code_challenge was provided
            if code_data.get("code_challenge"):
                if not code_verifier:
                    return {"error": "invalid_request", "error_description": "code_verifier required"}, 400

                # Verify code challenge
                method = code_data.get("code_challenge_method", "plain")
                if method == "S256":
                    # SHA256 hash
                    computed_challenge = base64.urlsafe_b64encode(
                        hashlib.sha256(code_verifier.encode()).digest()
                    ).decode().rstrip("=")
                else:
                    # Plain
                    computed_challenge = code_verifier

                if computed_challenge != code_data["code_challenge"]:
                    return {"error": "invalid_grant", "error_description": "Invalid code_verifier"}, 400

            # Mark as used
            code_data["used"] = True

            # Generate access token
            access_token = secrets.token_urlsafe(48)
            transport.oauth_tokens[access_token] = {
                "expires_at": time.time() + OAUTH_TOKEN_EXPIRY_SECONDS,
                "client_id": code_data.get("client_id"),
                "scope": code_data.get("scope")
            }

            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": OAUTH_TOKEN_EXPIRY_SECONDS,
                "scope": code_data.get("scope")
            }

        elif grant_type == "client_credentials":
            # Get client credentials
            client_id = get_param("client_id")
            client_secret = get_param("client_secret")

            # Validate client
            if client_id and client_id in transport.oauth_clients:
                expected_secret = transport.oauth_clients[client_id]["client_secret"]
                if client_secret != expected_secret:
                    return {"error": "invalid_client"}, 401

            # Direct token grant
            access_token = secrets.token_urlsafe(48)
            transport.oauth_tokens[access_token] = {
                "expires_at": time.time() + OAUTH_TOKEN_EXPIRY_SECONDS,
                "client_id": client_id,
                "scope": "read:devices read:screen write:control"
            }

            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": OAUTH_TOKEN_EXPIRY_SECONDS
            }

        else:
            return {"error": "unsupported_grant_type"}, 400

    @app.route("/mcp", methods=["POST", "GET", "OPTIONS"])
    def mcp_endpoint():
        """Main MCP endpoint."""
        # Handle CORS preflight
        if request.method == "OPTIONS":
            return "", 204

        # Check authentication
        if not check_auth():
            return {"error": "Unauthorized"}, 401

        # Validate MCP protocol version
        protocol_version = request.headers.get("MCP-Protocol-Version", "2025-03-26")
        if protocol_version != "2025-03-26":
            return {"error": "Unsupported protocol version"}, 400

        # Get session ID
        session_id = request.headers.get("Mcp-Session-Id")

        # Handle POST (message)
        if request.method == "POST":
            accept_header = request.headers.get("Accept", "")

            # Check if client wants SSE
            if "text/event-stream" in accept_header:
                # SSE streaming response
                def generate():
                    try:
                        message = request.json

                        # Process message
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        response = loop.run_until_complete(
                            transport.handle_message(message, session_id)
                        )
                        loop.close()

                        # Stream response as SSE
                        yield f"data: {json.dumps(response)}\n\n"

                    except Exception as e:
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            },
                            "id": None
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"

                return Response(
                    stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no"
                    }
                )
            else:
                # Regular JSON response
                message = request.json

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(
                    transport.handle_message(message, session_id)
                )
                loop.close()

                # Check if response contains new session ID
                if "result" in response and "_meta" in response["result"]:
                    new_session_id = response["result"]["_meta"].get("sessionId")
                    if new_session_id:
                        return response, 200, {"Mcp-Session-Id": new_session_id}

                return response, 200

        # Handle GET (not part of spec, but useful for testing)
        return {
            "name": "Phonegang MCP Server",
            "version": "0.1.0",
            "transport": "streamable-http",
            "endpoint": "/mcp",
            "instructions": "Send JSON-RPC messages via POST with MCP-Protocol-Version header"
        }

    return app


def start_mcp_http_server(host: str = DEFAULT_HTTP_HOST, port: int = DEFAULT_HTTP_PORT, auth_token: Optional[str] = None, base_url: Optional[str] = None):
    """
    Start MCP HTTP server.

    Args:
        host: Host to bind to (default: 127.0.0.1 for localhost-only access)
        port: Port to listen on
        auth_token: Optional Bearer token for authentication
        base_url: Base URL for OAuth metadata

    Security Note:
        Defaults to localhost (127.0.0.1) for security. Use '0.0.0.0' to bind to
        all interfaces, but only do this in trusted networks with proper firewall rules.
    """
    if base_url is None:
        base_url = f"http://{host}:{port}"

    app = create_mcp_http_server(host, port, auth_token, base_url)
    print(f"Starting MCP HTTP server on {base_url}/mcp")
    print(f"Protocol version: 2025-03-26")
    print(f"Transport: streamable-http")
    print(f"\nOAuth 2.0 Endpoints:")
    print(f"  Discovery: {base_url}/.well-known/oauth-authorization-server")
    print(f"  Register:  {base_url}/oauth/register")
    print(f"  Authorize: {base_url}/oauth/authorize")
    print(f"  Token:     {base_url}/oauth/token")
    if auth_token:
        print(f"\nStatic Token: {auth_token}")
    print(f"\nSupports: PKCE (S256), Dynamic Client Registration (RFC 7591)")
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    start_mcp_http_server()
