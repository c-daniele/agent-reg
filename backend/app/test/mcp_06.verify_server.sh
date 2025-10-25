#!/bin/bash
# Test script for verifying an MCP server connection
# Usage: ./mcp_06.verify_server.sh <server_id>

BASE_URL="http://localhost:8000"

if [ -z "$1" ]; then
  echo "Usage: $0 <server_id>"
  exit 1
fi

SERVER_ID="$1"

echo "=== Verify MCP Server: $SERVER_ID ==="
curl -X POST "$BASE_URL/mcp/servers/$SERVER_ID/verify" \
  -H "Content-Type: application/json" | jq .

echo ""
