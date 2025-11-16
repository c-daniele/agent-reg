"""
Agent-Reg (Agent Registry) - baseline implementation
A FastAPI app implementing a minimal A2A-compliant registry:

Features:
- POST /agents/register : register an Agent Card JSON
- GET  /agents          : list + search agents
- GET  /agents/{id}     : retrieve an agent card
- POST /agents/{id}/heartbeat : update agent liveness
- PUT  /agents/{id}     : update agent (simple owner-less update)
- DELETE /agents/{id}   : delete agent

Storage: SQLite with JSON extension (scalable NoSQL-like storage with SQL performance)
Run: pip install -r requirements.txt
     uvicorn main:app --reload --port 8000

"""

import os
import json
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Path, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from database import AgentDatabase
from jsonschema import ValidationError
import logging as logger
from agent_card_validator import AgentCardValidator
from agent_card_models import AgentCreate, AgentUpdate
from mcp_models import (
    MCPServerRegister, MCPServerResponse, MCPSearchQuery,
    MCPSearchResult, MCPServerCapabilities
)
from mcp_client import MCPClient, MCPClientError, test_mcp_connection
from mcp_gateway_routes import router as gateway_router
from mcp_connection_manager import initialize_connection_manager, get_connection_manager

from dotenv import load_dotenv

load_dotenv()


# Load the schema on startup
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "a2a_agent_card_schema.json")
# with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
#     AGENT_CARD_SCHEMA = json.load(f)

logger.basicConfig(level=logger.INFO)

# -----------------------------
# DB setup
# -----------------------------
db = AgentDatabase(os.environ.get("DATABASE_PATH", "agent_reg.db"))

# -----------------------------
# App
# -----------------------------
app = FastAPI(title="AI-R: A2A Agent Registry (baseline with Schema validation)")

# Allow CORS for development/demo pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# MCP Gateway Connection Manager
# -----------------------------
connection_manager = initialize_connection_manager(db)

@app.on_event("startup")
async def startup_event():
    """Start the MCP connection manager on application startup"""
    await connection_manager.start()
    logger.info("MCP Gateway connection manager started")

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown all MCP connections on application shutdown"""
    await connection_manager.stop()
    logger.info("MCP Gateway connection manager stopped")

# -----------------------------
# Helpers
# -----------------------------

def fetch_agent(agent_id: str) -> Dict[str, Any]:
    result = db.get_agent(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result

# -----------------------------
# Routes
# -----------------------------
@app.post("/agents/register", status_code=status.HTTP_201_CREATED)
async def register_agent(request: Request):
    """Register a new agent by providing an Agent Card (AgentCreate).
    The registry stores the card and returns the persistent Agent record (including generated id and timestamps).
    """
    payload = await request.json()
    # Validate against Schema
    try:
        # validate(instance=payload, schema=AGENT_CARD_SCHEMA)
        validator = AgentCardValidator(SCHEMA_PATH)
        is_valid, error_message = validator.validate_string(json.dumps(payload))
        if not is_valid:
            raise HTTPException(status_code=422, detail=error_message)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e.msg}")
        
    # except ValidationError as e:
    #     raise HTTPException(
    #         status_code=422,
    #         detail=f"JSON Schema validation error: {e.message}"
    #     )

    # If valid, store complete agent card
    agent_create = AgentCreate(**payload)
    agent_id = str(uuid4())
    
    # Store the complete agent card with metadata
    result = db.insert_agent(
        agent_id=agent_id,
        agent_card=agent_create.model_dump(exclude={'owner'}),
        owner=agent_create.owner
    )
    
    return result

@app.get("/agents")
def list_agents(
    skill: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    capabilities: Optional[str] = Query(None),  # Accept as comma-separated string
    only_alive: Optional[bool] = Query(False),
):
    """
    List and search agents. Filters are applied efficiently at the database level.
    - skill: matches if any skill.id == skill
    - name: SQL LIKE on agent.name
    - streaming: expects capabilities['streaming'] == True
    - push_notifications: expects capabilities['pushNotifications'] == True
    - state_transition_history: expects capabilities['stateTransitionHistory'] == True
    - only_alive: filters agents whose last_heartbeat is within 5 minutes
    - capabilities: comma-separated list, e.g. "streaming,push_notifications"
    """
    # Parse capabilities string into boolean flags
    capabilities_list = []
    if capabilities:
        capabilities_list = [c.strip() for c in capabilities.split(",") if c.strip()]

    streaming = "streaming" in capabilities_list
    push_notifications = "push_notifications" in capabilities_list or "pushNotifications" in capabilities_list
    state_transition_history = "state_transition_history" in capabilities_list or "stateTransitionHistory" in capabilities_list

    # Use database method with efficient WHERE conditions
    return db.list_agents(
        skill=skill,
        name=name,
        owner=owner,
        streaming=streaming,
        push_notifications=push_notifications,
        state_transition_history=state_transition_history,
        only_alive=only_alive
    )

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str = Path(...)):
    return fetch_agent(agent_id)

@app.post("/agents/{agent_id}/heartbeat")
def heartbeat(agent_id: str):
    """Agent calls this endpoint periodically to update its last_heartbeat.
    This helps the registry mark agents alive/stale.
    """
    success = db.update_heartbeat(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    return fetch_agent(agent_id)

@app.put("/agents/{agent_id}")
def update_agent(agent_id: str, upd: AgentUpdate):
    # Check if agent exists
    if not db.get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update fields
    updates = upd.model_dump(exclude_none=True)
    success = db.update_agent(agent_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return fetch_agent(agent_id)

@app.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str):
    success = db.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None


# -----------------------------
# MCP Server Management Routes
# -----------------------------

@app.post("/mcp/servers/register", status_code=status.HTTP_201_CREATED)
async def register_mcp_server(server_data: MCPServerRegister):
    """
    Register a new MCP server

    This endpoint:
    1. Validates the MCP server configuration
    2. Performs handshake with the MCP server to verify availability
    3. Discovers server capabilities (tools, resources, prompts)
    4. Stores the server details and capabilities in the database
    5. Returns the registered server ID and full details
    """
    # Get configuration from the request
    config = server_data.get_config()

    # Test connection and discover capabilities
    # try:
    client = MCPClient(server_data.type, config)
    capabilities = await client.discover_capabilities()
    # except MCPClientError as e:

    #     raise HTTPException(
    #         status_code=422,
    #         detail=f"Failed to connect to MCP server: {str(e)}"
    #     )
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Unexpected error connecting to MCP server: {str(e)}"
    #     )

    # Generate server ID and store in database
    server_id = str(uuid4())

    try:
        result = db.insert_mcp_server(
            server_id=server_id,
            server_type=server_data.type,
            description=server_data.description,
            config=config,
            capabilities=capabilities.model_dump()
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store MCP server: {str(e)}"
        )


@app.get("/mcp/servers")
def list_mcp_servers(
    server_type: Optional[str] = Query(None, description="Filter by server type (stdio, http, sse)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (active, inactive, error)")
):
    """
    List all registered MCP servers with their capabilities

    Optional filters:
    - server_type: Filter by transport type (stdio, http, sse)
    - status: Filter by server status (active, inactive, error)
    """
    try:
        servers = db.list_mcp_servers(server_type=server_type, status=status_filter)
        return servers
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list MCP servers: {str(e)}"
        )


@app.get("/mcp/servers/{server_id}")
def get_mcp_server(server_id: str = Path(..., description="MCP Server ID")):
    """
    Get detailed information about a specific MCP server including its capabilities
    """
    result = db.get_mcp_server(server_id)
    if not result:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return result


@app.get("/mcp/search")
def search_mcp_capabilities(
    query: Optional[str] = Query(None, description="Search query string"),
    capability_type: Optional[str] = Query(None, description="Filter by capability type (tool, resource, prompt)"),
    server_type: Optional[str] = Query(None, description="Filter by server type (stdio, http, sse)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """
    Search for tools, resources, or prompts across all registered MCP servers

    This endpoint searches across all active MCP servers and returns:
    - Matched servers with their configuration
    - The specific capabilities (tools/resources/prompts) that matched the query

    Query parameters:
    - query: Keywords to search for in capability names and descriptions
    - capability_type: Narrow search to specific capability type (tool, resource, prompt)
    - server_type: Filter by server transport type (stdio, http, sse)
    - limit: Maximum number of results to return (default: 100)
    """
    try:
        results = db.search_mcp_capabilities(
            query=query,
            capability_type=capability_type,
            server_type=server_type,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search MCP capabilities: {str(e)}"
        )


@app.delete("/mcp/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mcp_server(server_id: str = Path(..., description="MCP Server ID")):
    """
    Delete an MCP server and all its associated capabilities
    """
    success = db.delete_mcp_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return None


@app.post("/mcp/servers/{server_id}/verify")
async def verify_mcp_server(server_id: str = Path(..., description="MCP Server ID")):
    """
    Verify connection to an MCP server and update its status

    This endpoint attempts to reconnect to the server and update:
    - Server status (active, inactive, error)
    - Last verification timestamp
    """
    server = db.get_mcp_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    try:
        client = MCPClient(server['type'], server['config'])
        capabilities = await client.discover_capabilities()

        # Update status to active
        db.update_mcp_server_status(server_id, 'active')

        return {
            "server_id": server_id,
            "status": "active",
            "message": "Server is reachable and responding",
            "capabilities": capabilities.model_dump()
        }
    except MCPClientError as e:
        # Update status to error
        db.update_mcp_server_status(server_id, 'error')

        raise HTTPException(
            status_code=503,
            detail=f"Server verification failed: {str(e)}"
        )


# -----------------------------
# MCP Gateway Routes
# -----------------------------
# Include the gateway router for HTTP/SSE proxy endpoints
app.include_router(gateway_router)


# -----------------------------
# Simple health and UI helpers
# -----------------------------

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# -----------------------------
# Example utility: generate invocation URL
# -----------------------------

@app.get("/agents/{agent_id}/invoke_url")
def get_invoke_url(agent_id: str):
    """Return the agent's invocation URL and summarized invocation guidance.
    The client should use the returned URL and follow the A2A protocol (JSON-RPC over HTTPS) to invoke the agent.
    """
    agent = fetch_agent(agent_id)
    return {
        "agent_id": agent["id"],
        "invoke_url": agent.get("url"),
        "note": "Use this endpoint as per A2A JSON-RPC spec.",
        "agent_card": {k: v for k, v in agent.items() 
                      if k not in ['id', 'owner', 'created_at', 'last_heartbeat']}
    }


# -----------------------------
# If run as script, start uvicorn
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
