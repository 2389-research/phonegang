# ABOUTME: Configuration constants for phonegang
# ABOUTME: Centralizes magic numbers and default values for better maintainability

"""Configuration constants for phonegang."""

# ADB Connection Configuration
ADB_AUTH_TIMEOUT_SECONDS = 10
"""Timeout for ADB authentication in seconds."""

# UI Caching Configuration
UI_CACHE_TIMEOUT_SECONDS = 2.0
"""Duration to cache UI dumps before refreshing (in seconds)."""

# Swipe Gesture Configuration
DEFAULT_SWIPE_DURATION_MS = 300
"""Default duration for swipe gestures in milliseconds."""

# Scrolling Configuration
MAX_SCROLL_ATTEMPTS = 10
"""Maximum number of scroll attempts when searching for elements."""

# UI Refresh Configuration
UI_REFRESH_INTERVAL_SECONDS = 0.5
"""Interval between UI refreshes when polling for changes (in seconds)."""

# Wait Configuration
DEFAULT_WAIT_TIMEOUT_SECONDS = 10
"""Default timeout for waiting for elements to appear (in seconds)."""

# Screen Streaming Configuration
SCREEN_STREAM_POLL_INTERVAL_SECONDS = 0.5
"""Polling interval for screen update streams (in seconds)."""

SCREEN_STREAM_ERROR_RETRY_DELAY_SECONDS = 1.0
"""Delay before retrying after stream errors (in seconds)."""

# OAuth Configuration
OAUTH_CODE_EXPIRY_SECONDS = 600
"""OAuth authorization code expiry time (10 minutes)."""

OAUTH_TOKEN_EXPIRY_SECONDS = 3600
"""OAuth access token expiry time (1 hour)."""

# Network Configuration
DEFAULT_HTTP_HOST = "127.0.0.1"
"""Default host for HTTP servers (localhost for security)."""

DEFAULT_HTTP_PORT = 8000
"""Default port for HTTP servers."""

# Retry Configuration
DEFAULT_MAX_RETRIES = 3
"""Default maximum number of retries for transient failures."""

DEFAULT_RETRY_DELAYS = [2, 4, 8]
"""Default exponential backoff delays for retries (in seconds)."""
