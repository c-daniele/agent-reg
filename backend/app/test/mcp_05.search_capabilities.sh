#!/bin/bash
# Test script for searching MCP capabilities
# Usage: ./mcp_05.search_capabilities.sh [query] [capability_type] [server_type]

BASE_URL="http://localhost:8000"

QUERY="${1:-}"
CAPABILITY_TYPE="${2:-}"
SERVER_TYPE="${3:-}"

# Build query parameters
PARAMS=""
if [ -n "$QUERY" ]; then
  PARAMS="?query=$QUERY"
fi
if [ -n "$CAPABILITY_TYPE" ]; then
  if [ -z "$PARAMS" ]; then
    PARAMS="?capability_type=$CAPABILITY_TYPE"
  else
    PARAMS="${PARAMS}&capability_type=$CAPABILITY_TYPE"
  fi
fi
if [ -n "$SERVER_TYPE" ]; then
  if [ -z "$PARAMS" ]; then
    PARAMS="?server_type=$SERVER_TYPE"
  else
    PARAMS="${PARAMS}&server_type=$SERVER_TYPE"
  fi
fi

echo "=== Search MCP Capabilities ==="
echo "Query: ${QUERY:-all}"
echo "Capability Type: ${CAPABILITY_TYPE:-all}"
echo "Server Type: ${SERVER_TYPE:-all}"
echo ""

curl -X GET "$BASE_URL/mcp/search$PARAMS" \
  -H "Content-Type: application/json" | jq .

echo ""
