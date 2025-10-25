# MCP Gateway Documentation

## Overview

The MCP Gateway extends the Agent Registry to support the **Model Context Protocol (MCP)**. It provides a centralized registry for MCP servers, enabling discovery and search of MCP capabilities (tools, resources, and prompts) across multiple servers.

## Key Features

1. **MCP Server Registration**: Register stdio, HTTP, and SSE-based MCP servers
2. **Automatic Capability Discovery**: Automatically discover and catalog tools, resources, and prompts
3. **Centralized Search**: Search for capabilities across all registered MCP servers
4. **Connection Verification**: Verify MCP server availability and status
5. **RESTful API**: Easy-to-use REST endpoints for all operations

## Architecture

### Components

- **mcp_models.py**: Pydantic data models for MCP servers and capabilities
- **mcp_client.py**: MCP client connector for handshakes and capability discovery
- **database.py**: Extended with MCP tables and operations
- **main.py**: FastAPI endpoints for MCP server management

### Database Schema

The implementation adds four new tables:

1. **mcp_servers**: Core server information (type, config, status)
2. **mcp_tools**: Tool capabilities with input schemas
3. **mcp_resources**: Resource capabilities with URIs
4. **mcp_prompts**: Prompt capabilities with arguments

All capability tables have foreign keys to `mcp_servers` with CASCADE delete.

## API Endpoints

### 1. Register MCP Server

**POST** `/mcp/servers/register`

Register a new MCP server and automatically discover its capabilities.

#### Request Body - stdio Server

```json
{
  "type": "stdio",
  "description": "My stdio MCP server",
  "command": "python",
  "args": ["-m", "my_mcp_server"],
  "env": {
    "MCP_PORT": "8080",
    "DEBUG": "true"
  }
}
```

#### Request Body - HTTP Server

```json
{
  "type": "http",
  "description": "My HTTP MCP server",
  "url": "http://localhost:3000/mcp",
  "headers": {
    "Authorization": "Bearer token123",
    "X-API-Key": "my-key"
  }
}
```

#### Request Body - SSE Server

```json
{
  "type": "sse",
  "description": "My SSE MCP server",
  "url": "http://localhost:3000/sse",
  "headers": {
    "Authorization": "Bearer token123"
  }
}
```

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "stdio",
  "description": "My stdio MCP server",
  "config": {
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "env": {"MCP_PORT": "8080", "DEBUG": "true"}
  },
  "capabilities": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Get weather information",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          }
        }
      }
    ],
    "resources": [
      {
        "uri": "file://data/config.json",
        "name": "Configuration",
        "description": "Server configuration",
        "mimeType": "application/json"
      }
    ],
    "prompts": [
      {
        "name": "summarize",
        "description": "Summarize text",
        "arguments": [
          {"name": "text", "description": "Text to summarize"}
        ]
      }
    ]
  },
  "created_at": "2025-10-25T10:30:00.000Z",
  "last_verified": "2025-10-25T10:30:00.000Z",
  "status": "active"
}
```

### 2. List MCP Servers

**GET** `/mcp/servers`

List all registered MCP servers with optional filters.

#### Query Parameters

- `server_type` (optional): Filter by type (stdio, http, sse)
- `status` (optional): Filter by status (active, inactive, error)

#### Example

```bash
GET /mcp/servers?server_type=stdio&status=active
```

#### Response (200 OK)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "stdio",
    "description": "My stdio MCP server",
    "config": {...},
    "capabilities": {...},
    "created_at": "2025-10-25T10:30:00.000Z",
    "last_verified": "2025-10-25T10:30:00.000Z",
    "status": "active"
  }
]
```

### 3. Get MCP Server

**GET** `/mcp/servers/{server_id}`

Get detailed information about a specific MCP server.

#### Response (200 OK)

Same structure as registration response.

### 4. Search MCP Capabilities

**GET** `/mcp/search`

Search for tools, resources, or prompts across all registered MCP servers.

#### Query Parameters

- `query` (optional): Search keywords
- `capability_type` (optional): Filter by type (tool, resource, prompt)
- `server_type` (optional): Filter by server type (stdio, http, sse)
- `limit` (optional): Maximum results (1-1000, default: 100)

#### Example

```bash
GET /mcp/search?query=weather&capability_type=tool
```

#### Response (200 OK)

```json
[
  {
    "server_id": "550e8400-e29b-41d4-a716-446655440000",
    "server_type": "stdio",
    "server_description": "Weather MCP server",
    "server_config": {
      "command": "python",
      "args": ["-m", "weather_server"]
    },
    "matched_tools": [
      {
        "name": "get_weather",
        "description": "Get current weather information",
        "inputSchema": {...}
      }
    ],
    "matched_resources": [],
    "matched_prompts": []
  }
]
```

### 5. Verify MCP Server

**POST** `/mcp/servers/{server_id}/verify`

Verify connection to an MCP server and update its status.

#### Response (200 OK)

```json
{
  "server_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "message": "Server is reachable and responding",
  "capabilities": {...}
}
```

#### Response (503 Service Unavailable)

```json
{
  "detail": "Server verification failed: Timeout waiting for server response"
}
```

### 6. Delete MCP Server

**DELETE** `/mcp/servers/{server_id}`

Delete an MCP server and all its associated capabilities.

#### Response (204 No Content)

Empty response body on success.

## Testing

Test scripts are provided in the `test/` directory:

```bash
# Register stdio server
./test/mcp_01.register_stdio.sh

# Register HTTP server
./test/mcp_02.register_http.sh

# List all servers
./test/mcp_03.list_servers.sh

# List only stdio servers
./test/mcp_03.list_servers.sh stdio

# Get specific server
./test/mcp_04.get_server.sh <server_id>

# Search for capabilities
./test/mcp_05.search_capabilities.sh weather tool

# Verify server connection
./test/mcp_06.verify_server.sh <server_id>

# Delete server
./test/mcp_07.delete_server.sh <server_id>
```

## MCP Protocol Implementation

The gateway implements the MCP specification (version 2024-11-05):

### Handshake Process

1. **Initialize**: Send `initialize` method with protocol version and client info
2. **Initialized**: Send `notifications/initialized` after receiving response
3. **List Capabilities**: Query tools, resources, and prompts using respective methods

### Supported Server Types

#### stdio
- Launches subprocess with command, args, and environment variables
- Communicates via stdin/stdout using JSON-RPC
- Suitable for local MCP servers

#### HTTP
- Connects to HTTP endpoint
- Sends POST requests with JSON-RPC payloads
- Supports custom headers for authentication

#### SSE (Server-Sent Events)
- Similar to HTTP but optimized for SSE transport
- Supports long-lived connections
- Custom headers for authentication

## Error Handling

The gateway provides comprehensive error handling:

- **422 Unprocessable Entity**: Invalid request or unable to connect to MCP server
- **404 Not Found**: Server ID not found
- **500 Internal Server Error**: Database or unexpected errors
- **503 Service Unavailable**: Server verification failed

## Security Considerations

1. **Environment Variables**: Stored securely in database, passed to stdio processes
2. **HTTP Headers**: Stored securely for authenticated HTTP/SSE connections
3. **Command Validation**: stdio commands should be validated before execution
4. **Network Isolation**: Consider network policies for HTTP/SSE servers

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. The database will be automatically initialized on first run

3. Start the server:

```bash
cd backend/app/src
uvicorn main:app --reload --port 8000
```

## Usage Examples

### Register a Weather MCP Server

```bash
curl -X POST http://localhost:8000/mcp/servers/register \
  -H "Content-Type: application/json" \
  -d '{
    "type": "stdio",
    "description": "Weather information server",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-weather"]
  }'
```

### Search for Weather Tools

```bash
curl "http://localhost:8000/mcp/search?query=weather&capability_type=tool"
```

### List All Active Servers

```bash
curl "http://localhost:8000/mcp/servers?status=active"
```

## Development

### Adding New Capability Types

To add new capability types (beyond tools, resources, prompts):

1. Update `mcp_models.py` with new capability models
2. Add new table in `database.py` `_init_database()`
3. Update `insert_mcp_server()` and `get_mcp_server()` in `database.py`
4. Update `search_mcp_capabilities()` with new search logic
5. Update `MCPClient` to discover new capabilities

### Extending the MCP Client

The `MCPClient` class in `mcp_client.py` can be extended to support:

- Additional MCP protocol versions
- Custom transport mechanisms
- Enhanced error recovery
- Connection pooling for HTTP/SSE

## Troubleshooting

### Server Registration Fails

- **Check server availability**: Ensure the MCP server is running and accessible
- **Verify command**: For stdio servers, ensure the command exists in PATH
- **Check logs**: Review server stderr output for errors

### Search Returns No Results

- **Verify server status**: Use `/mcp/servers` to check server status
- **Check capability names**: MCP servers may use different naming conventions
- **Try broader queries**: Start with simple keywords

### Database Errors

- **Check file permissions**: Ensure the database file is writable
- **Verify schema**: Delete database file to force re-initialization
- **Check SQLite version**: Ensure SQLite 3.31+ for JSON support

## Future Enhancements

Potential improvements:

1. **Capability Caching**: Cache capability lists with TTL
2. **Server Health Monitoring**: Periodic health checks
3. **Capability Versioning**: Track capability changes over time
4. **Authentication**: Add API key authentication for gateway endpoints
5. **Rate Limiting**: Protect against abuse
6. **Webhooks**: Notify when new capabilities are discovered
7. **Capability Graph**: Build relationships between capabilities

## References

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite JSON Functions](https://www.sqlite.org/json1.html)
