# MCP Gateway Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Gateway                              │
│                    (FastAPI Application)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
    │   A2A API   │  │   MCP API    │  │  Health API │
    │  /agents/*  │  │  /mcp/*      │  │   /health   │
    └─────────────┘  └──────────────┘  └─────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
    │  Database   │  │  MCP Client  │  │  Validators │
    │  (SQLite)   │  │  Connector   │  │             │
    └─────────────┘  └──────────────┘  └─────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
    │   stdio     │  │     HTTP     │  │     SSE     │
    │ MCP Servers │  │ MCP Servers  │  │ MCP Servers │
    └─────────────┘  └──────────────┘  └─────────────┘
```

## Component Layers

### 1. API Layer (FastAPI Routes)

**A2A Routes** (`/agents/*`)
- Agent registration
- Agent listing and search
- Agent heartbeat
- Agent updates and deletion

**MCP Routes** (`/mcp/*`)
- MCP server registration
- MCP server listing
- Capability search
- Server verification
- Server deletion

### 2. Business Logic Layer

**MCP Client Connector** (`mcp_client.py`)
```
┌──────────────────────────────────┐
│       MCPClient Class            │
├──────────────────────────────────┤
│ - discover_capabilities()        │
│ - _discover_stdio_capabilities() │
│ - _discover_http_capabilities()  │
└──────────────────────────────────┘
```

**Database Operations** (`database.py`)
```
┌──────────────────────────────────┐
│     AgentDatabase Class          │
├──────────────────────────────────┤
│ A2A Methods:                     │
│ - insert_agent()                 │
│ - list_agents()                  │
│ - update_agent()                 │
│                                  │
│ MCP Methods:                     │
│ - insert_mcp_server()            │
│ - list_mcp_servers()             │
│ - search_mcp_capabilities()      │
│ - update_mcp_server_status()     │
└──────────────────────────────────┘
```

**Data Models** (`mcp_models.py`)
```
┌──────────────────────────────────┐
│       Pydantic Models            │
├──────────────────────────────────┤
│ - MCPServerRegister              │
│ - MCPServerResponse              │
│ - MCPServerCapabilities          │
│ - MCPToolCapability              │
│ - MCPResourceCapability          │
│ - MCPPromptCapability            │
│ - MCPSearchQuery                 │
│ - MCPSearchResult                │
└──────────────────────────────────┘
```

### 3. Data Layer (SQLite Database)

```
┌─────────────────────────────────────────────────────┐
│                 SQLite Database                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  A2A Tables:                                        │
│  ┌──────────────┐                                   │
│  │   agents     │  (A2A agent cards)                │
│  └──────────────┘                                   │
│                                                      │
│  MCP Tables:                                        │
│  ┌──────────────┐                                   │
│  │ mcp_servers  │  (Server configs & status)        │
│  └──────┬───────┘                                   │
│         │                                            │
│         ├─────┐                                      │
│         │     │                                      │
│  ┌──────▼─────▼──┐  ┌─────────────┐  ┌───────────┐ │
│  │   mcp_tools   │  │mcp_resources│  │mcp_prompts│ │
│  └───────────────┘  └─────────────┘  └───────────┘ │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### Registration Flow

```
┌─────────┐         ┌──────────┐         ┌──────────┐
│ Client  │         │ Gateway  │         │  MCP     │
│         │         │          │         │ Server   │
└────┬────┘         └────┬─────┘         └────┬─────┘
     │                   │                    │
     │ POST /register    │                    │
     ├──────────────────>│                    │
     │                   │                    │
     │                   │ initialize         │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ capabilities       │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ tools/list         │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ tools response     │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ resources/list     │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ resources response │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ prompts/list       │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ prompts response   │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ [Store in DB]      │
     │                   │                    │
     │ Server details    │                    │
     │<──────────────────┤                    │
     │                   │                    │
```

### Search Flow

```
┌─────────┐         ┌──────────┐         ┌──────────┐
│ Client  │         │ Gateway  │         │ Database │
└────┬────┘         └────┬─────┘         └────┬─────┘
     │                   │                    │
     │ GET /mcp/search   │                    │
     │ ?query=weather    │                    │
     ├──────────────────>│                    │
     │                   │                    │
     │                   │ Query tools        │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ Matched servers    │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ Query resources    │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ Matched servers    │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ Query prompts      │
     │                   ├───────────────────>│
     │                   │                    │
     │                   │ Matched servers    │
     │                   │<───────────────────┤
     │                   │                    │
     │                   │ [Merge results]    │
     │                   │                    │
     │ Search results    │                    │
     │<──────────────────┤                    │
     │                   │                    │
```

## MCP Client Architecture

### stdio Transport

```
┌────────────────────────────────────────────┐
│           MCP Client (Python)              │
└─────────────┬──────────────────────────────┘
              │
              │ asyncio.create_subprocess_exec()
              │
┌─────────────▼──────────────────────────────┐
│       subprocess (MCP Server)              │
│                                            │
│  ┌──────┐           ┌──────┐              │
│  │stdin │◄──────────┤ JSON │              │
│  └──┬───┘           │ RPC  │              │
│     │               │      │              │
│  ┌──▼────┐          └──────┘              │
│  │stdout │──────────►                     │
│  └───────┘                                │
│                                            │
└────────────────────────────────────────────┘
```

### HTTP Transport

```
┌────────────────────────────────────────────┐
│        MCP Client (httpx)                  │
└─────────────┬──────────────────────────────┘
              │
              │ HTTP POST (JSON-RPC)
              │
┌─────────────▼──────────────────────────────┐
│      HTTP MCP Server                       │
│                                            │
│  ┌─────────────────────────────┐          │
│  │  POST /mcp                  │          │
│  │  Content-Type: application/ │          │
│  │                json         │          │
│  │  Authorization: Bearer XXX  │          │
│  └─────────────────────────────┘          │
│                                            │
└────────────────────────────────────────────┘
```

## Database Schema Relationships

```
┌──────────────────────┐
│    mcp_servers       │
│ ────────────────────│
│ id (PK)              │
│ type                 │◄──────────────────┐
│ description          │                   │
│ config (JSON)        │                   │
│ created_at           │                   │
│ last_verified        │                   │
│ status               │                   │
└──────────┬───────────┘                   │
           │ 1                             │
           │                               │
           │ *                             │
   ┌───────┴────────────┬──────────────────┼──────────────┐
   │                    │                  │              │
┌──▼──────────┐  ┌──────▼────────┐  ┌──────▼────────┐   │
│  mcp_tools  │  │ mcp_resources │  │  mcp_prompts  │   │
│─────────────│  │───────────────│  │───────────────│   │
│ id (PK)     │  │ id (PK)       │  │ id (PK)       │   │
│ server_id   │  │ server_id     │  │ server_id     │   │
│ name        │  │ uri           │  │ name          │   │
│ description │  │ name          │  │ description   │   │
│ input_schema│  │ description   │  │ arguments     │   │
└─────────────┘  │ mime_type     │  └───────────────┘   │
                 └───────────────┘                       │
                                                         │
                 ON DELETE CASCADE ────────────────────┘
```

## Request/Response Flow

### 1. Register MCP Server

```
Request:
{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "server"],
  "env": {"PORT": "8080"}
}

         ↓ Validation (Pydantic)

         ↓ MCP Client Connection

         ↓ Capability Discovery

         ↓ Database Insert

Response:
{
  "id": "uuid",
  "type": "stdio",
  "config": {...},
  "capabilities": {
    "tools": [...],
    "resources": [...],
    "prompts": [...]
  },
  "status": "active"
}
```

### 2. Search Capabilities

```
Request:
GET /mcp/search?query=weather&capability_type=tool

         ↓ Parse Query Parameters

         ↓ Database Search (SQL LIKE)

         ↓ Filter by Capability Type

         ↓ Merge Server Info

Response:
[
  {
    "server_id": "uuid",
    "matched_tools": [...],
    "matched_resources": [],
    "matched_prompts": []
  }
]
```

## Security Architecture

```
┌─────────────────────────────────────────────┐
│              API Gateway                    │
│                                             │
│  ┌─────────────────────────────────┐       │
│  │  CORS Middleware                │       │
│  └─────────┬───────────────────────┘       │
│            │                                │
│  ┌─────────▼───────────────────────┐       │
│  │  Request Validation (Pydantic)  │       │
│  └─────────┬───────────────────────┘       │
│            │                                │
│  ┌─────────▼───────────────────────┐       │
│  │  Database Layer                 │       │
│  │  - Parameterized Queries        │       │
│  │  - SQL Injection Prevention     │       │
│  └─────────┬───────────────────────┘       │
│            │                                │
│  ┌─────────▼───────────────────────┐       │
│  │  MCP Client Layer               │       │
│  │  - Timeout Protection           │       │
│  │  - Error Handling               │       │
│  │  - Subprocess Isolation         │       │
│  └─────────────────────────────────┘       │
│                                             │
└─────────────────────────────────────────────┘
```

## Performance Considerations

### 1. Database Indexing

```
Indexes:
- mcp_servers(type)         → Fast filtering by server type
- mcp_servers(status)       → Fast active/inactive queries
- mcp_tools(server_id)      → Fast joins
- mcp_tools(name)           → Fast capability searches
- mcp_resources(name)       → Fast resource searches
- mcp_prompts(name)         → Fast prompt searches
```

### 2. Async Operations

```
┌──────────────────────┐
│   FastAPI Endpoint   │  ← async def
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│    MCP Client        │  ← async methods
│  - Non-blocking I/O  │
│  - Concurrent calls  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│   MCP Server         │
│  - Independent       │
│    execution         │
└──────────────────────┘
```

## Scalability Path

### Current (Single Instance)
```
┌──────────────┐
│   FastAPI    │
│   + SQLite   │
└──────────────┘
```

### Future (Distributed)
```
┌──────────────┐     ┌──────────────┐
│  FastAPI #1  │     │  FastAPI #2  │
└──────┬───────┘     └──────┬───────┘
       │                    │
       │     ┌──────────────┘
       │     │
┌──────▼─────▼────┐
│   PostgreSQL    │
│   or MySQL      │
└─────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│             Production                   │
│                                          │
│  ┌────────────────┐                     │
│  │  Load Balancer │                     │
│  └────────┬───────┘                     │
│           │                              │
│  ┌────────▼────────┐  ┌──────────────┐ │
│  │   FastAPI #1    │  │  FastAPI #2  │ │
│  └────────┬────────┘  └──────┬───────┘ │
│           │                  │          │
│  ┌────────▼──────────────────▼────────┐│
│  │         Database (Shared)          ││
│  └────────────────────────────────────┘│
│                                          │
└─────────────────────────────────────────┘
```

## Summary

The MCP Gateway architecture is:

- **Modular**: Clear separation of concerns (API, Logic, Data)
- **Extensible**: Easy to add new capability types
- **Performant**: Indexed queries, async I/O
- **Scalable**: Can grow from SQLite to PostgreSQL
- **Secure**: Input validation, parameterized queries
- **Maintainable**: Well-documented, tested components
