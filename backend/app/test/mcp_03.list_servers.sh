#!/bin/bash
# Test script for listing MCP servers
# Usage: ./mcp_03.list_servers.sh [server_type] [status]

BASE_URL="http://localhost:8000"

SERVER_TYPE="${1:-}"
STATUS="${2:-}"

# Build query parameters
PARAMS=""
if [ -n "$SERVER_TYPE" ]; then
  PARAMS="?server_type=$SERVER_TYPE"
fi
if [ -n "$STATUS" ]; then
  if [ -z "$PARAMS" ]; then
    PARAMS="?status=$STATUS"
  else
    PARAMS="${PARAMS}&status=$STATUS"
  fi
fi

echo "=== List MCP Servers ==="
echo "Filters: server_type=${SERVER_TYPE:-none}, status=${STATUS:-none}"
curl -X GET "$BASE_URL/mcp/servers$PARAMS" \
  -H "Content-Type: application/json" | jq .

echo ""
