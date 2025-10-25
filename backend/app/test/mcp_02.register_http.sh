#!/bin/bash
# Test script for registering an HTTP-based MCP server
# Usage: ./mcp_02.register_http.sh

BASE_URL="http://localhost:8000"

echo "=== Register HTTP MCP Server ==="
curl -X POST "$BASE_URL/mcp/servers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "description": "Example HTTP MCP server",
    "url": "http://localhost:3000/mcp",
    "headers": {
      "Authorization": "Bearer test-token",
      "X-API-Key": "my-api-key"
    }
  }' | jq .

echo ""
