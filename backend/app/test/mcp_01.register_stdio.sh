#!/bin/bash
# Test script for registering a stdio-based MCP server
# Usage: ./mcp_01.register_stdio.sh

BASE_URL="http://localhost:8000"

echo "=== Register stdio MCP Server ==="
curl -X POST "$BASE_URL/mcp/servers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "stdio",
    "description": "Example stdio MCP server",
    "command": "python",
    "args": ["-m", "mcp_server_example"],
    "env": {
      "MCP_SERVER_PORT": "8080"
    }
  }' | jq .

echo ""
