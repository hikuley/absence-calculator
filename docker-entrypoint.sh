#!/bin/sh

# Replace API_URL placeholder with environment variable
echo "window.API_URL = '${API_URL}/api';" > /usr/share/nginx/html/config.js

# Start nginx
exec "$@"
