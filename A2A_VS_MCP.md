# A2A vs MCP: Protocol Comparison

## Overview

This document compares the AgentToAgent (A2A) and Model Context Protocol (MCP) implementations in the Agent Registry, highlighting their purposes, differences, and how they coexist.

## Protocol Purposes

### A2A (Agent-to-Agent)
**Purpose**: Enable AI agents to discover and communicate with each other

**Focus**:
- Agent registration and discovery
- Agent capabilities and skills
- Agent-to-agent communication
- Task delegation between agents

**Use Case**: "I need to find an agent that can translate documents"

### MCP (Model Context Protocol)
**Purpose**: Provide language models with context through standardized servers

**Focus**:
- Tool/function calling
- Resource access (files, APIs, databases)
- Prompt templates
- Context provision for LLMs

**Use Case**: "I need to give my LLM access to a weather API and file system"

## Key Differences

| Aspect | A2A | MCP |
|--------|-----|-----|
| **Entity** | AI Agents | Context Servers |
| **Communication** | Agent ↔ Agent | LLM ↔ Server |
| **Discovery** | Agent skills | Tools, resources, prompts |
| **Protocol** | JSON-RPC | JSON-RPC |
| **Transport** | JSONRPC, GRPC, HTTP+JSON | stdio, HTTP, SSE |
| **Focus** | Autonomous agents | LLM augmentation |
| **State** | Stateful (conversations) | Stateless (function calls) |

## Architecture Comparison

### A2A Architecture
```
┌──────────┐         ┌──────────┐         ┌──────────┐
│ Agent A  │◄───────►│ Registry │◄───────►│ Agent B  │
└──────────┘         └──────────┘         └──────────┘
     ↑                     ↑                     ↑
     │                     │                     │
Skills: translate    Discovers: agents    Skills: summarize
```

### MCP Architecture
```
┌──────────┐         ┌──────────┐         ┌──────────┐
│   LLM    │◄───────►│ Gateway  │◄───────►│   MCP    │
│          │         │          │         │  Server  │
└──────────┘         └──────────┘         └──────────┘
     ↑                     ↑                     ↑
     │                     │                     │
Uses: tools          Discovers: servers   Provides: context
```

## Data Model Comparison

### A2A Agent Card
```json
{
  "name": "Translation Agent",
  "description": "Translates text between languages",
  "version": "1.0.0",
  "protocolVersion": "0.3.0",
  "url": "https://translate.example.com/agent",
  "skills": [
    {
      "id": "translate",
      "name": "Translate Text",
      "description": "Translate text from one language to another",
      "tags": ["translation", "language", "nlp"]
    }
  ],
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "provider": {
    "organization": "TranslateCo",
    "url": "https://translateco.com"
  }
}
```

### MCP Server Capabilities
```json
{
  "type": "stdio",
  "description": "Translation MCP Server",
  "config": {
    "command": "python",
    "args": ["-m", "translate_server"]
  },
  "capabilities": {
    "tools": [
      {
        "name": "translate",
        "description": "Translate text",
        "inputSchema": {
          "type": "object",
          "properties": {
            "text": {"type": "string"},
            "from_lang": {"type": "string"},
            "to_lang": {"type": "string"}
          }
        }
      }
    ],
    "resources": [
      {
        "uri": "glossary://terms",
        "name": "Translation Glossary",
        "mimeType": "application/json"
      }
    ],
    "prompts": [
      {
        "name": "translate_formal",
        "description": "Translate with formal tone"
      }
    ]
  }
}
```

## API Comparison

### A2A Endpoints
```
POST   /agents/register           Register an agent
GET    /agents                    List/search agents
GET    /agents/{id}              Get agent details
POST   /agents/{id}/heartbeat    Update agent liveness
PUT    /agents/{id}              Update agent
DELETE /agents/{id}              Delete agent
GET    /agents/{id}/invoke_url   Get invocation URL
```

### MCP Endpoints
```
POST   /mcp/servers/register         Register MCP server
GET    /mcp/servers                  List MCP servers
GET    /mcp/servers/{id}            Get server details
GET    /mcp/search                  Search capabilities
POST   /mcp/servers/{id}/verify     Verify server
DELETE /mcp/servers/{id}            Delete server
```

## Search Comparison

### A2A Search
**What you search for**: Agent skills and capabilities

```bash
# Find agents with translation skill
GET /agents?skill=translate

# Find agents with streaming capability
GET /agents?capabilities=streaming

# Find active agents
GET /agents?only_alive=true
```

**Returns**: Complete agent cards

### MCP Search
**What you search for**: Tools, resources, and prompts

```bash
# Find tools related to translation
GET /mcp/search?query=translate&capability_type=tool

# Find all resources
GET /mcp/search?capability_type=resource

# Find prompts on stdio servers
GET /mcp/search?query=format&server_type=stdio
```

**Returns**: Matched capabilities with server details

## Registration Flow Comparison

### A2A Registration
```
1. Client submits agent card JSON
2. Validate against A2A schema
3. Store agent card
4. Return agent with ID and timestamps
```

### MCP Registration
```
1. Client submits server config
2. Connect to MCP server
3. Perform initialize handshake
4. Discover capabilities (tools/resources/prompts)
5. Store server config + capabilities
6. Return server with discovered capabilities
```

## Use Cases

### When to Use A2A

✅ **Building multi-agent systems**
- Agent orchestration
- Task delegation
- Agent collaboration
- Dynamic agent discovery

✅ **Agent marketplace**
- Publish agents for others to use
- Discover available agents
- Agent capability browsing

✅ **Microservices architecture with AI**
- Each service is an agent
- Service discovery
- Cross-service communication

### When to Use MCP

✅ **Augmenting LLMs with tools**
- Give LLMs access to APIs
- Enable function calling
- Dynamic tool discovery

✅ **Providing context to LLMs**
- File system access
- Database queries
- API data retrieval

✅ **Building AI assistants**
- Chatbots with external tools
- Code generation with API access
- Data analysis assistants

## Integration Patterns

### Pattern 1: A2A Agent Uses MCP Tools

An A2A agent can internally use MCP servers to enhance its capabilities:

```
┌─────────────────┐
│   A2A Agent     │
│  (Translation)  │
└────────┬────────┘
         │
         │ Uses internally
         ▼
┌─────────────────┐
│   MCP Server    │
│ (Dictionary API)│
└─────────────────┘
```

The A2A agent is registered as a translation agent, but internally it uses MCP tools to access dictionaries, terminology databases, etc.

### Pattern 2: LLM Discovers Agents via A2A

An LLM using MCP tools can discover specialized agents:

```
┌──────────┐         ┌──────────┐
│   LLM    │◄───────►│   MCP    │
│          │         │  Server  │
└──────────┘         └────┬─────┘
                          │
                          │ Queries
                          ▼
                    ┌──────────┐
                    │   A2A    │
                    │ Registry │
                    └──────────┘
```

The MCP server provides a tool that searches the A2A registry for specialized agents.

### Pattern 3: Unified Registry

Both protocols coexist in the same registry:

```
┌─────────────────────────────────┐
│      Agent Registry             │
│                                 │
│  ┌──────────┐   ┌────────────┐ │
│  │   A2A    │   │    MCP     │ │
│  │  Agents  │   │  Servers   │ │
│  └──────────┘   └────────────┘ │
│                                 │
└─────────────────────────────────┘
```

Clients can search both A2A agents and MCP servers from a single endpoint.

## Database Comparison

### A2A Tables
```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    agent_card TEXT NOT NULL,      -- Full agent card JSON
    owner TEXT,
    created_at TEXT NOT NULL,
    last_heartbeat TEXT,
    -- Generated columns
    name TEXT,
    capabilities TEXT
);
```

### MCP Tables
```sql
CREATE TABLE mcp_servers (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,             -- stdio, http, sse
    description TEXT,
    config TEXT NOT NULL,           -- Connection config JSON
    created_at TEXT NOT NULL,
    last_verified TEXT,
    status TEXT DEFAULT 'active'
);

CREATE TABLE mcp_tools (
    id INTEGER PRIMARY KEY,
    server_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    input_schema TEXT              -- JSON schema
);

CREATE TABLE mcp_resources (
    id INTEGER PRIMARY KEY,
    server_id TEXT,
    uri TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    mime_type TEXT
);

CREATE TABLE mcp_prompts (
    id INTEGER PRIMARY KEY,
    server_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    arguments TEXT                 -- JSON array
);
```

## Protocol Maturity

### A2A
- **Status**: Evolving standard
- **Version**: 0.3.0
- **Adoption**: Growing in multi-agent systems
- **Standardization**: Community-driven

### MCP
- **Status**: Established protocol
- **Version**: 2024-11-05
- **Adoption**: Supported by major AI companies
- **Standardization**: Anthropic-led specification

## Real-World Examples

### A2A Example
```
User: "I need to book a flight and hotel for my trip"

Discovery Registry finds:
1. Flight Booking Agent (skill: book-flight)
2. Hotel Booking Agent (skill: book-hotel)

Orchestrator Agent:
1. Delegates to Flight Booking Agent
2. Delegates to Hotel Booking Agent
3. Coordinates both results
```

### MCP Example
```
User: "What's the weather in Paris?"

LLM queries MCP Gateway for weather tools

Gateway returns: Weather MCP Server
- Tool: get_weather(location)

LLM calls: get_weather("Paris")

MCP Server executes and returns weather data

LLM formats response: "It's 18°C and sunny in Paris"
```

## Combining Both Protocols

### Scenario: AI Travel Assistant

```
┌─────────────────────────────────────────┐
│         AI Travel Assistant             │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌──────────────┐
│  A2A Registry │   │ MCP Gateway  │
└───────┬───────┘   └──────┬───────┘
        │                  │
        ▼                  ▼
┌───────────────┐   ┌──────────────┐
│ Booking Agents│   │ Context Tools│
│ - Flights     │   │ - Weather    │
│ - Hotels      │   │ - Currency   │
│ - Cars        │   │ - Maps       │
└───────────────┘   └──────────────┘
```

**Flow**:
1. User asks: "Plan a trip to Paris"
2. Assistant uses **MCP** to get weather, currency rates
3. Assistant uses **A2A** to find and delegate to booking agents
4. Assistant combines all information into response

## Performance Comparison

### A2A
- **Registration**: Fast (JSON validation + database insert)
- **Search**: Fast (indexed SQL queries)
- **Invocation**: Depends on agent implementation
- **Overhead**: Minimal (REST API)

### MCP
- **Registration**: Slower (handshake + capability discovery)
- **Search**: Fast (indexed SQL queries)
- **Invocation**: Depends on transport (stdio fast, HTTP moderate)
- **Overhead**: Higher (protocol handshake, subprocess management)

## Security Comparison

### A2A Security
- JWT signatures on agent cards
- OAuth2 for agent authentication
- API key support
- Transport security (HTTPS)
- Owner-based access control

### MCP Security
- Environment variable isolation
- HTTP header authentication
- Subprocess sandboxing
- Command validation
- Network policy enforcement

## Future Convergence

Potential future integration:

```
┌────────────────────────────────────┐
│      Unified Discovery API         │
├────────────────────────────────────┤
│                                    │
│  query: "translate"                │
│  ↓                                 │
│  Returns:                          │
│  - A2A Agent: Translation Service  │
│  - MCP Tool: translate_text        │
│  - MCP Resource: glossary://terms  │
│                                    │
└────────────────────────────────────┘
```

## Recommendations

### Use A2A when:
- Building autonomous agent networks
- Agents need to delegate to other agents
- Complex multi-step workflows
- Agent state management is important

### Use MCP when:
- Augmenting LLMs with external tools
- Providing context to language models
- Simple function calling patterns
- Stateless operations

### Use Both when:
- Building comprehensive AI systems
- Need both agent collaboration and tool access
- Want maximum flexibility
- Building AI platforms

## Summary

| Aspect | A2A | MCP |
|--------|-----|-----|
| **Best For** | Multi-agent systems | LLM augmentation |
| **Complexity** | Higher (agent coordination) | Lower (function calls) |
| **State** | Stateful | Stateless |
| **Discovery** | Agent skills | Tools/resources |
| **Communication** | Bidirectional | Request/response |
| **Use Case** | Agent orchestration | Context provision |

Both protocols serve different but complementary purposes. The Agent Registry supports both, enabling maximum flexibility for AI system builders.
