# Agent Registry Backend

FastAPI-based backend for the Agent Registry service with MCP (Model Context Protocol) server support.

## Quick Start

### 1. Install Dependencies

```bash
cd backend/app
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Server

**Option A: Using the startup script (recommended)**
```bash
cd backend/app
./start_server.sh
```

**Option B: Manual start**
```bash
cd backend/app
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:src"
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at: `http://localhost:8000`

### 3. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## MCP Server Registration

### Register a stdio MCP Server

```bash
curl -X POST http://localhost:8000/mcp/servers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Everything",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-everything"]
  }'
```

### Register an HTTP/SSE MCP Server

```bash
curl -X POST http://localhost:8000/mcp/servers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My HTTP Server",
    "type": "http",
    "url": "http://localhost:3000/mcp"
  }'
```

## Important Note

The backend requires `PYTHONPATH` to include the `src` directory for proper module imports. The `start_server.sh` script handles this automatically.

## Troubleshooting

If you encounter import errors like `ModuleNotFoundError: No module named 'database'`, make sure you're:

1. Running from the `backend/app` directory
2. Using the `start_server.sh` script, OR
3. Setting `PYTHONPATH` manually: `export PYTHONPATH="${PYTHONPATH}:src"`
