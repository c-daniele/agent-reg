#!/bin/bash
# Test script for registering the example simple MCP server
# Usage: ./mcp_08.register_example_server.sh

BASE_URL="http://localhost:8000"

# Get the path to the example server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_SERVER="$SCRIPT_DIR/../examples/simple_mcp_server.py"

echo "=== Register Example Simple MCP Server ==="
echo "Server script: $EXAMPLE_SERVER"
echo ""

curl -X POST "$BASE_URL/mcp/servers/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"stdio\",
    \"description\": \"Simple example MCP server with echo, add, and greet tools\",
    \"command\": \"python3\",
    \"args\": [\"$EXAMPLE_SERVER\"]
  }" | jq .

echo ""
