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
