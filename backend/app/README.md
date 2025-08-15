# AI-R: A2A Agent Registry (Baseline)

This project implements a minimal agent registry service using FastAPI and TinyDB, compliant with the A2A protocol. It allows registering, searching, updating, and deleting agent cards, as well as tracking agent liveness.

## Features

- **Register Agent**: `POST /agents/register`  
  Register a new agent by submitting an Agent Card JSON.

- **List/Search Agents**: `GET /agents`  
  List all agents or filter by skill, name, owner, streaming capability, or liveness.

- **Retrieve Agent Card**: `GET /agents/{id}`  
  Get details of a specific agent.

- **Heartbeat**: `POST /agents/{id}/heartbeat`  
  Update agent's liveness timestamp.

- **Update Agent**: `PUT /agents/{id}`  
  Update agent details.

- **Delete Agent**: `DELETE /agents/{id}`  
  Remove an agent from the registry.

- **Health Check**: `GET /health`  
  Simple health endpoint.

- **Invocation URL**: `GET /agents/{id}/invoke_url`  
  Get the agent's endpoint and invocation guidance.

## Storage

- Uses SQLite with JSON extension for data storage.

## Setup

1. **Install dependencies**:
    ```
    pip install -r requirements.txt
    ```

2. **Run the server**:
    ```
    uvicorn ai_r_registry:app --reload --port 8000
    ```

## API Models

- **AgentCard**: Basic agent metadata (name, description, url, version, capabilities, skills).
- **Skill**: Skill metadata (id, name, description, inputs, outputs).
- **Agent**: Persistent agent record (includes id, timestamps, owner).

## Example Usage

Register an agent:
```bash
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","url":"https://example.com/agent","skills":[{"id":"skill1"}]}'
```

List agents:
```bash
curl http://localhost:8000/agents
```

## Development

- CORS is enabled for all origins for development/demo purposes.
- The app is a single-file FastAPI implementation (`src/main.py`).

## License

MIT