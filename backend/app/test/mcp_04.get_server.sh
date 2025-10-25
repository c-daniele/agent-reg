#!/bin/bash
# Test script for getting a specific MCP server
# Usage: ./mcp_04.get_server.sh <server_id>

BASE_URL="http://localhost:8000"

if [ -z "$1" ]; then
  echo "Usage: $0 <server_id>"
  exit 1
fi

SERVER_ID="$1"

echo "=== Get MCP Server: $SERVER_ID ==="
curl -X GET "$BASE_URL/mcp/servers/$SERVER_ID" \
  -H "Content-Type: application/json" | jq .

echo ""
