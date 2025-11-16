# MCP Gateway Implementation Plan

## Goal
Transform the MCP Gateway into a true gateway by exposing all registered MCP servers (stdio, HTTP, SSE) through centralized HTTP/SSE endpoints.

## Recommended Approach: Hybrid Implementation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
│         (Can be MCP-unaware HTTP clients)               │
└────────────┬────────────────────────────────────────────┘
             │
             ├─── SSE:  GET /mcp/gateway/{server_id}/sse
             │          (Streaming, real-time)
             │
             └─── HTTP: POST /mcp/gateway/{server_id}/message
                        (Stateless, request-response)
             │
┌────────────▼────────────────────────────────────────────┐
│               FastAPI MCP Gateway                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         MCPConnectionManager                     │  │
│  │  - Connection Pool (server_id → ClientSession)  │  │
│  │  - Keep-alive tasks for stdio servers           │  │
│  │  - Auto-reconnection logic                       │  │
│  │  - Connection lifecycle management               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Gateway Endpoints                        │  │
│  │  - SSE streaming proxy                           │  │
│  │  - HTTP message proxy                            │  │
│  │  - Tool/Resource/Prompt discovery               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└────────────┬────────────────────────────────────────────┘
             │
             ├─── stdio  → Persistent subprocess connections
             ├─── HTTP   → Direct HTTP forwarding
             └─── SSE    → SSE-to-SSE passthrough
             │
┌────────────▼────────────────────────────────────────────┐
│              Registered MCP Servers                      │
│  - stdio servers (local processes)                      │
│  - HTTP servers (remote APIs)                           │
│  - SSE servers (streaming endpoints)                    │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Connection Manager (Core Infrastructure)

**Goal**: Create a robust connection pool for managing MCP server sessions.

**Files to Create:**
1. `backend/app/src/mcp_connection_manager.py`
2. `backend/app/src/mcp_gateway_models.py`

**Key Features:**
- Connection pooling with TTL
- Auto-reconnection for dropped connections
- Health checking
- Graceful shutdown

**Implementation Details:**

```python
class MCPConnectionManager:
    """
    Manages persistent connections to registered MCP servers.

    Features:
    - Connection pooling (one session per server)
    - Keep-alive for stdio servers
    - Auto-reconnection on failure
    - Connection health monitoring
    """

    def __init__(self, database: AgentDatabase):
        self.db = database
        self.connections: Dict[str, MCPConnection] = {}
        self.lock = asyncio.Lock()

    async def get_session(self, server_id: str) -> ClientSession:
        """Get or create a session for the given server."""

    async def initialize_connection(self, server_id: str) -> MCPConnection:
        """Initialize a new connection to an MCP server."""

    async def health_check(self, server_id: str) -> bool:
        """Check if connection is alive."""

    async def cleanup_idle_connections(self):
        """Remove connections idle for > 5 minutes."""

    async def shutdown(self):
        """Gracefully close all connections."""
```

**Connection Lifecycle:**
```
1. Client requests gateway endpoint
2. Manager checks if connection exists
3. If not, create new session using MCP SDK
4. Initialize with server
5. Keep session alive
6. Reuse for subsequent requests
7. Auto-reconnect on failure
8. Cleanup after idle timeout
```

---

### Phase 2: HTTP Message Proxy (Stateless Gateway)

**Goal**: Create stateless HTTP endpoint for single JSON-RPC messages.

**Endpoint:**
```
POST /mcp/gateway/{server_id}/message
```

**Features:**
- Single request-response pattern
- Connection reuse from pool
- Timeout handling
- Error forwarding

**Request/Response:**
```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

**Implementation:**
```python
@app.post("/mcp/gateway/{server_id}/message")
async def gateway_message_proxy(
    server_id: str,
    message: JSONRPCMessage,
    connection_manager: MCPConnectionManager = Depends()
):
    """
    Stateless HTTP proxy for JSON-RPC messages.
    """
    # Get server from database
    server = db.get_mcp_server(server_id)
    if not server:
        raise HTTPException(404, "Server not found")

    # Get or create connection
    session = await connection_manager.get_session(server_id)

    # Forward message
    if message.method == "tools/list":
        result = await session.list_tools()
    elif message.method == "resources/list":
        result = await session.list_resources()
    # ... etc

    # Return response
    return result
```

---

### Phase 3: SSE Streaming Proxy (Real-time Gateway)

**Goal**: Create SSE endpoint for streaming connections.

**Endpoint:**
```
GET /mcp/gateway/{server_id}/sse
```

**Features:**
- Bidirectional streaming
- Keep-alive pings
- Auto-reconnection
- Progress notifications

**Implementation:**
```python
@app.get("/mcp/gateway/{server_id}/sse")
async def gateway_sse_proxy(
    server_id: str,
    request: Request,
    connection_manager: MCPConnectionManager = Depends()
):
    """
    SSE streaming proxy for real-time MCP communication.
    """
    # Establish connection
    session = await connection_manager.get_session(server_id)

    async def event_generator():
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"server_id": server_id})
            }

            # Stream messages
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Handle incoming messages
                # Forward to MCP server
                # Yield responses as SSE events

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for {server_id}")
        finally:
            # Cleanup
            pass

    return EventSourceResponse(event_generator())
```

---

### Phase 4: Tool/Resource/Prompt Proxying

**Goal**: Expose MCP capabilities directly through HTTP endpoints.

**Endpoints:**
```
POST /mcp/gateway/{server_id}/tools/{tool_name}
GET  /mcp/gateway/{server_id}/resources/{resource_uri}
POST /mcp/gateway/{server_id}/prompts/{prompt_name}
```

**Example - Call Tool:**
```python
@app.post("/mcp/gateway/{server_id}/tools/{tool_name}")
async def call_tool_proxy(
    server_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
    connection_manager: MCPConnectionManager = Depends()
):
    """
    Direct tool invocation proxy.

    This makes it easy for non-MCP clients to use MCP tools.
    """
    session = await connection_manager.get_session(server_id)

    result = await session.call_tool(tool_name, arguments)

    return {
        "tool": tool_name,
        "result": result.content,
        "isError": result.isError if hasattr(result, 'isError') else False
    }
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/mcp/gateway/{server_id}/tools/get_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "San Francisco"}'
```

---

### Phase 5: Frontend Integration

**Goal**: Update React frontend to use gateway endpoints.

**New Features:**
1. **Gateway Status**: Show which servers are connected
2. **Test Tool**: UI to test tools directly
3. **Resource Browser**: Browse and view resources
4. **Prompt Tester**: Test prompts with arguments

**New Components:**
```typescript
// MCPGatewayClient.tsx
// - Test tool execution
// - Browse resources
// - Try prompts

// MCPGatewayStatus.tsx
// - Show connection status
// - Connection health
// - Reconnect button
```

---

## Technical Decisions

### Connection Pooling Strategy

**For stdio servers:**
- Keep persistent subprocess connections
- Max 1 connection per server
- Auto-restart on crash
- Idle timeout: 5 minutes

**For HTTP/SSE servers:**
- Direct forwarding (no persistent connection)
- Connection reuse via httpx
- Timeout: 30 seconds

### Error Handling

**Connection Failures:**
```python
try:
    session = await connection_manager.get_session(server_id)
except ConnectionError:
    # Mark server as 'error' in database
    await db.update_mcp_server_status(server_id, 'error')
    # Return 503 Service Unavailable
    raise HTTPException(503, "MCP server unreachable")
```

**Timeout Handling:**
```python
try:
    result = await asyncio.wait_for(
        session.call_tool(...),
        timeout=30.0
    )
except asyncio.TimeoutError:
    raise HTTPException(504, "MCP server timeout")
```

---

## Security Considerations

### Authentication Options

**Option 1: API Keys**
```python
@app.post("/mcp/gateway/{server_id}/message")
async def gateway_proxy(
    server_id: str,
    api_key: str = Header(..., alias="X-API-Key")
):
    # Validate API key
    # Check permissions for server_id
    ...
```

**Option 2: JWT Tokens**
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/mcp/gateway/{server_id}/message")
async def gateway_proxy(
    server_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validate JWT
    # Check claims for server access
    ...
```

### Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/mcp/gateway/{server_id}/message")
@limiter.limit("100/minute")
async def gateway_proxy(...):
    ...
```

---

## Performance Optimization

### Caching Strategy

**Tool Results:**
```python
from functools import lru_cache
from cachetools import TTLCache

tool_cache = TTLCache(maxsize=1000, ttl=60)

@app.post("/mcp/gateway/{server_id}/tools/{tool_name}")
async def call_tool_proxy(...):
    cache_key = f"{server_id}:{tool_name}:{hash(arguments)}"

    if cache_key in tool_cache:
        return tool_cache[cache_key]

    result = await session.call_tool(...)
    tool_cache[cache_key] = result

    return result
```

**Capability Discovery:**
- Cache list_tools(), list_resources(), list_prompts()
- TTL: 5 minutes
- Invalidate on server update/verify

---

## Monitoring & Observability

### Metrics to Track

```python
from prometheus_client import Counter, Histogram

gateway_requests = Counter(
    'mcp_gateway_requests_total',
    'Total gateway requests',
    ['server_id', 'method', 'status']
)

gateway_latency = Histogram(
    'mcp_gateway_latency_seconds',
    'Gateway request latency',
    ['server_id', 'method']
)

active_connections = Gauge(
    'mcp_gateway_active_connections',
    'Active MCP connections',
    ['server_id']
)
```

### Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "gateway_request",
    server_id=server_id,
    method=message.method,
    latency_ms=latency,
    status="success"
)
```

---

## Testing Strategy

### Unit Tests
- Connection manager lifecycle
- Message forwarding logic
- Error handling

### Integration Tests
```python
async def test_gateway_stdio_proxy():
    # Start example stdio server
    # Register in database
    # Call gateway endpoint
    # Verify response matches direct call

async def test_gateway_connection_pooling():
    # Make multiple requests
    # Verify same connection reused

async def test_gateway_auto_reconnect():
    # Kill stdio subprocess
    # Make request
    # Verify auto-reconnection
```

### Load Tests
```bash
# Test concurrent connections
ab -n 1000 -c 10 http://localhost:8000/mcp/gateway/{id}/message
```

---

## Deployment Considerations

### Environment Variables
```bash
MCP_GATEWAY_MAX_CONNECTIONS=100
MCP_GATEWAY_IDLE_TIMEOUT=300
MCP_GATEWAY_REQUEST_TIMEOUT=30
MCP_GATEWAY_ENABLE_CACHING=true
```

### Docker Deployment
```dockerfile
# Ensure stdio servers can be spawned
# Mount volumes for stdio server executables
# Configure resource limits
```

---

## Migration Path

### Phase 1 (Week 1): Core Infrastructure
- [ ] Implement MCPConnectionManager
- [ ] Add HTTP message proxy
- [ ] Basic tests

### Phase 2 (Week 2): Streaming Support
- [ ] Implement SSE proxy
- [ ] Handle bidirectional streaming
- [ ] Connection health monitoring

### Phase 3 (Week 3): Direct Capability Proxies
- [ ] Tool invocation endpoints
- [ ] Resource access endpoints
- [ ] Prompt execution endpoints

### Phase 4 (Week 4): Frontend Integration
- [ ] Update UI to show gateway status
- [ ] Add tool testing interface
- [ ] Resource browser
- [ ] Prompt tester

### Phase 5 (Week 5): Production Hardening
- [ ] Add authentication
- [ ] Implement rate limiting
- [ ] Add caching layer
- [ ] Monitoring & metrics
- [ ] Load testing

---

## Success Criteria

✅ Any registered MCP server (stdio/HTTP/SSE) can be accessed via:
- HTTP JSON-RPC endpoint
- SSE streaming endpoint

✅ stdio servers remain connected for duration of gateway lifetime

✅ Automatic reconnection on failure

✅ Tools/resources/prompts can be invoked directly via REST

✅ Frontend can test and interact with all server capabilities

✅ Performance: < 50ms overhead for HTTP, < 100ms for stdio

✅ Reliability: 99.9% uptime for gateway layer

---

## Next Steps

1. **Review this plan** - Confirm architectural approach
2. **Choose Phase 1 scope** - Start with connection manager?
3. **Decide on auth strategy** - API keys vs JWT vs none?
4. **Set performance targets** - Latency, throughput, connections
5. **Begin implementation** - I can start coding the connection manager

Would you like me to proceed with Phase 1 (Connection Manager) implementation?
