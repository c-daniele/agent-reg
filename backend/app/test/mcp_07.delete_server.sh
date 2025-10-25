#!/bin/bash
# Test script for deleting an MCP server
# Usage: ./mcp_07.delete_server.sh <server_id>

BASE_URL="http://localhost:8000"

if [ -z "$1" ]; then
  echo "Usage: $0 <server_id>"
  exit 1
fi

SERVER_ID="$1"

echo "=== Delete MCP Server: $SERVER_ID ==="
curl -X DELETE "$BASE_URL/mcp/servers/$SERVER_ID" \
  -H "Content-Type: application/json" -v

echo ""
