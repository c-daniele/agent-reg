# MCP Gateway Quick Start Guide

This guide will get you up and running with the MCP Gateway in 5 minutes.

## Prerequisites

- Python 3.8+
- pip

## Step 1: Install Dependencies

```bash
cd backend/app
pip install -r requirements.txt
```

Expected output:
```
Installing collected packages: fastapi, uvicorn, sqlmodel, python-dateutil, python-dotenv, jsonschema, httpx
Successfully installed...
```

## Step 2: Start the Gateway

```bash
cd src
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The gateway is now running!

## Step 3: Test with Example MCP Server

Open a **new terminal** and run:

```bash
cd backend/app/test
./mcp_08.register_example_server.sh
```

Expected output (JSON):
```json
{
  "id": "550e8400-...",
  "type": "stdio",
  "description": "Simple example MCP server with echo, add, and greet tools",
  "config": {
    "command": "python3",
    "args": ["/path/to/simple_mcp_server.py"]
  },
  "capabilities": {
    "tools": [
      {
        "name": "echo",
        "description": "Echo back the input message",
        "inputSchema": {...}
      },
      {
        "name": "add",
        "description": "Add two numbers together",
        "inputSchema": {...}
      },
      {
        "name": "greet",
        "description": "Generate a greeting message",
        "inputSchema": {...}
      }
    ],
    "resources": [
      {
        "uri": "file://config.json",
        "name": "Configuration",
        "description": "Server configuration file",
        "mimeType": "application/json"
      },
      {
        "uri": "file://data/sample.txt",
        "name": "Sample Data",
        "description": "Sample text data",
        "mimeType": "text/plain"
      }
    ],
    "prompts": [
      {
        "name": "summarize",
        "description": "Summarize a given text",
        "arguments": [...]
      },
      {
        "name": "translate",
        "description": "Translate text to another language",
        "arguments": [...]
      }
    ]
  },
  "created_at": "2025-10-25T...",
  "last_verified": "2025-10-25T...",
  "status": "active"
}
```

✅ Success! Your MCP server is registered.

## Step 4: List All Servers

```bash
./mcp_03.list_servers.sh
```

You should see a list containing your registered server.

## Step 5: Search for Capabilities

Search for the "add" tool:

```bash
./mcp_05.search_capabilities.sh add tool
```

Expected output:
```json
[
  {
    "server_id": "550e8400-...",
    "server_type": "stdio",
    "server_description": "Simple example MCP server...",
    "server_config": {...},
    "matched_tools": [
      {
        "name": "add",
        "description": "Add two numbers together",
        "inputSchema": {...}
      }
    ],
    "matched_resources": [],
    "matched_prompts": []
  }
]
```

Search for all capabilities containing "text":

```bash
./mcp_05.search_capabilities.sh text
```

You should see resources and prompts that mention "text".

## Step 6: Explore the API

Open your browser and navigate to:

```
http://localhost:8000/docs
```

You'll see the **interactive API documentation** (Swagger UI) with all available endpoints.

Try the following:
1. Click on `/mcp/servers` → "Try it out" → "Execute"
2. Click on `/mcp/search` → "Try it out" → Enter "echo" in query → "Execute"

## Common Operations

### Register Your Own MCP Server

#### stdio Server
```bash
curl -X POST http://localhost:8000/mcp/servers/register \
  -H "Content-Type: application/json" \
  -d '{
    "type": "stdio",
    "description": "My MCP server",
    "command": "node",
    "args": ["path/to/server.js"]
  }'
```

#### HTTP Server
```bash
curl -X POST http://localhost:8000/mcp/servers/register \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "description": "My HTTP MCP server",
    "url": "http://myserver.com/mcp",
    "headers": {
      "Authorization": "Bearer YOUR_TOKEN"
    }
  }'
```

### Get Server by ID

Replace `<server_id>` with actual ID:
```bash
./mcp_04.get_server.sh <server_id>
```

### Search Capabilities

Search for tools only:
```bash
./mcp_05.search_capabilities.sh weather tool
```

Search for resources only:
```bash
./mcp_05.search_capabilities.sh config resource
```

Search for prompts only:
```bash
./mcp_05.search_capabilities.sh summarize prompt
```

### Verify Server Connection

```bash
./mcp_06.verify_server.sh <server_id>
```

### Delete Server

```bash
./mcp_07.delete_server.sh <server_id>
```

## Troubleshooting

### Problem: "Command not found" when registering stdio server

**Solution**: Ensure the command exists in your PATH:
```bash
which python3  # or node, npm, etc.
```

### Problem: "Failed to connect to MCP server"

**Solution**:
1. Check if the MCP server is actually running (for HTTP/SSE)
2. Verify the command/URL is correct
3. Check the server logs for errors

### Problem: "No results" when searching

**Solution**:
1. Verify servers are registered: `./mcp_03.list_servers.sh`
2. Check server status is "active"
3. Try broader search terms

### Problem: Port 8000 already in use

**Solution**: Change the port in [main.py](src/main.py):
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```

## Next Steps

1. **Read the full documentation**: [MCP_GATEWAY_README.md](MCP_GATEWAY_README.md)
2. **Study the example server**: [examples/simple_mcp_server.py](examples/simple_mcp_server.py)
3. **Create your own MCP server**: Follow the MCP specification
4. **Integrate with your app**: Use the REST API to query capabilities

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mcp/servers/register` | Register new MCP server |
| GET | `/mcp/servers` | List all MCP servers |
| GET | `/mcp/servers/{server_id}` | Get server details |
| GET | `/mcp/search` | Search capabilities |
| POST | `/mcp/servers/{server_id}/verify` | Verify server |
| DELETE | `/mcp/servers/{server_id}` | Delete server |

## Support

- Documentation: [MCP_GATEWAY_README.md](MCP_GATEWAY_README.md)
- Implementation Details: [MCP_IMPLEMENTATION_SUMMARY.md](../MCP_IMPLEMENTATION_SUMMARY.md)
- MCP Protocol Spec: https://spec.modelcontextprotocol.io/

## Happy Gateway-ing! 🚀
