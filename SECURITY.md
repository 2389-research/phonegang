# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Phonegang, please report it responsibly:

### Where to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues via:
- Email: [Create an issue and request private disclosure]
- GitHub Security Advisories: Use the "Security" tab in the repository

### What to Include

Please provide:

1. **Description**: Detailed description of the vulnerability
2. **Impact**: What could an attacker do?
3. **Steps to reproduce**: How to trigger the vulnerability
4. **Affected versions**: Which versions are affected
5. **Suggested fix**: If you have ideas for fixing it
6. **Disclosure timeline**: Your preferred timeline for disclosure

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 30 days
  - Medium/Low: Next release cycle

## Security Considerations

### ADB Authentication

Phonegang uses ADB (Android Debug Bridge) for device communication. Be aware:

- ADB keys are stored in `~/.android/adbkey`
- Devices must be authorized via USB debugging prompt
- Keep your ADB keys secure - they grant device access
- Don't share your private ADB keys

### HTTP API Security

The HTTP API (`phonegang api`) has important security considerations:

⚠️ **Default Configuration is INSECURE**

- **No authentication by default** - Anyone with network access can control your devices
- **Bind to localhost only** for local use: `phonegang api --host 127.0.0.1`
- **Don't expose to internet** without additional security
- Consider using authentication/authorization if exposing remotely
- Use reverse proxy (nginx, Caddy) with authentication for production

### MCP HTTP Server

The MCP HTTP server (`phonegang mcp-http`) includes OAuth 2.0 support:

- Use `--auth-token` for simple bearer token authentication
- OAuth 2.0 with PKCE for more robust authentication
- Tokens are stored in memory only (not persisted)
- Generate strong tokens - don't use predictable values

### Web Viewer

The web viewer (`phonegang viewer`) provides screen mirroring:

- **No authentication** - Anyone who can access the port can view/control your device
- Bind to `127.0.0.1` for local-only access
- Use SSH tunneling for remote access: `ssh -L 5000:localhost:5000 user@server`
- Screenshots are stored locally - manage sensitive data appropriately

### Device Access

Phonegang can control Android devices completely:

- **Full device control** - Can tap, type, install apps, etc.
- **Screen access** - Can capture screenshots and view screen content
- **No sandboxing** - Direct ADB access to authorized devices
- Only connect trusted devices
- Be cautious when running untrusted automation scripts

### Code Execution

- Never run untrusted phonegang scripts
- Review automation scripts before execution
- Be aware scripts can control your devices fully
- MCP server executes commands on host system

## Best Practices

### For Users

1. **Keep ADB keys secure**: Protect `~/.android/adbkey`
2. **Limit API exposure**: Bind to localhost unless needed
3. **Use authentication**: Enable auth for remote access
4. **Review scripts**: Check automation scripts before running
5. **Update regularly**: Keep phonegang and dependencies updated
6. **Firewall rules**: Block external access to API ports
7. **Device trust**: Only authorize known devices

### For Developers

1. **Input validation**: Validate all user inputs
2. **Command injection**: Sanitize inputs used in shell commands
3. **Path traversal**: Validate file paths
4. **Resource limits**: Implement rate limiting and timeouts
5. **Error handling**: Don't leak sensitive info in errors
6. **Dependencies**: Keep dependencies updated
7. **Code review**: Review security implications of changes

### For Server Deployments

If deploying phonegang servers in production:

1. **Authentication**: Always enable authentication
2. **HTTPS**: Use TLS for all network traffic
3. **Reverse proxy**: Use nginx/Caddy with auth
4. **Network isolation**: Isolate device network
5. **Logging**: Log access and commands
6. **Monitoring**: Monitor for suspicious activity
7. **Updates**: Automate security updates
8. **Backup**: Backup ADB keys securely

## Known Security Limitations

- **ADB protocol**: Inherent ADB security limitations apply
- **No audit log**: Commands are not logged by default
- **In-memory only**: Session state not persisted
- **No rate limiting**: API has no built-in rate limits
- **Screenshot storage**: Screenshots stored unencrypted

## Security Updates

Security fixes will be released as:
- Patch releases for supported versions
- Announced in release notes
- Referenced in CHANGELOG.md

Subscribe to releases to stay informed.

## Acknowledgments

We appreciate responsible disclosure of security issues. Contributors who report valid security issues will be acknowledged (with their permission) in:

- Security advisory
- Release notes
- Project documentation

Thank you for helping keep Phonegang secure!
