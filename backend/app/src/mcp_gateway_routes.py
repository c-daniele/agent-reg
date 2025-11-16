"""
MCP Gateway Routes

HTTP/SSE endpoints that expose all registered MCP servers through
a unified gateway interface.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Depends, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from database import AgentDatabase
from mcp_connection_manager import MCPConnectionManager, get_connection_manager
from mcp_gateway_models import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    ToolCallRequest,
    ToolCallResponse,
    ResourceReadRequest,
    ResourceReadResponse,
    PromptGetRequest,
    PromptGetResponse,
    ConnectionStatus,
    GatewayHealthResponse,
    GatewayEvent,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/mcp/gateway", tags=["MCP Gateway"])


def get_db() -> AgentDatabase:
    """Dependency to get database instance"""
    from main import db
    return db


@router.post("/{server_id}/message", response_model=JSONRPCResponse)
async def gateway_message_proxy(
    server_id: str = Path(..., description="MCP Server ID"),
    message: JSONRPCRequest = ...,
    manager: MCPConnectionManager = Depends(get_connection_manager),
    db: AgentDatabase = Depends(get_db),
):
    """
    HTTP JSON-RPC message proxy.

    Forward a single JSON-RPC message to the specified MCP server and return the response.
    This endpoint is stateless and uses connection pooling for efficiency.

    Args:
        server_id: The ID of the registered MCP server
        message: JSON-RPC 2.0 request message

    Returns:
        JSON-RPC 2.0 response

    Example:
        POST /mcp/gateway/{server_id}/message
        {
          "jsonrpc": "2.0",
          "id": 1,
          "method": "tools/list",
          "params": {}
        }
    """
    try:
        # Get connection to server
        conn = await manager.get_connection(server_id)

        # Route message based on method
        method = message.method

        if method == "tools/list":
            result = await conn.session.list_tools()
            return JSONRPCResponse(
                id=message.id,
                result={"tools": [tool.model_dump() for tool in result.tools]},
            )

        elif method == "resources/list":
            result = await conn.session.list_resources()
            return JSONRPCResponse(
                id=message.id,
                result={"resources": [res.model_dump() for res in result.resources]},
            )

        elif method == "prompts/list":
            result = await conn.session.list_prompts()
            return JSONRPCResponse(
                id=message.id,
                result={"prompts": [p.model_dump() for p in result.prompts]},
            )

        elif method == "tools/call":
            params = message.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                return JSONRPCResponse(
                    id=message.id,
                    error=JSONRPCError(
                        code=-32602, message="Missing required parameter: name"
                    ),
                )

            result = await conn.session.call_tool(tool_name, arguments)
            return JSONRPCResponse(
                id=message.id, result={"content": result.content, "isError": result.isError}
            )

        elif method == "resources/read":
            params = message.params or {}
            uri = params.get("uri")

            if not uri:
                return JSONRPCResponse(
                    id=message.id,
                    error=JSONRPCError(
                        code=-32602, message="Missing required parameter: uri"
                    ),
                )

            result = await conn.session.read_resource(uri)
            return JSONRPCResponse(
                id=message.id, result={"contents": result.contents}
            )

        elif method == "prompts/get":
            params = message.params or {}
            name = params.get("name")
            arguments = params.get("arguments", {})

            if not name:
                return JSONRPCResponse(
                    id=message.id,
                    error=JSONRPCError(
                        code=-32602, message="Missing required parameter: name"
                    ),
                )

            result = await conn.session.get_prompt(name, arguments)
            return JSONRPCResponse(
                id=message.id, result={"messages": result.messages}
            )

        else:
            return JSONRPCResponse(
                id=message.id,
                error=JSONRPCError(
                    code=-32601, message=f"Method not found: {method}"
                ),
            )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Server unavailable: {e}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Server timeout")
    except Exception as e:
        logger.error(f"Error in message proxy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/{server_id}/sse")
async def gateway_sse_proxy(
    server_id: str = Path(..., description="MCP Server ID"),
    request: Request = ...,
    manager: MCPConnectionManager = Depends(get_connection_manager),
    db: AgentDatabase = Depends(get_db),
):
    """
    SSE streaming proxy.

    Establish a Server-Sent Events connection to the specified MCP server.
    This enables real-time streaming of messages and notifications.

    Args:
        server_id: The ID of the registered MCP server

    Returns:
        EventSourceResponse with SSE events

    Events:
        - connected: Initial connection established
        - message: JSON-RPC message from server
        - error: Error occurred
        - disconnected: Connection closed
    """

    async def event_generator():
        conn = None
        try:
            # Get connection to server
            conn = await manager.get_connection(server_id)

            # Send connected event
            event = GatewayEvent(
                type="connected",
                server_id=server_id,
                data={"message": "Connected to MCP server"},
            )
            yield {"event": "connected", "data": event.model_dump_json()}

            # Keep connection alive and forward messages
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from SSE stream for {server_id}")
                    break

                # Send periodic ping to keep connection alive
                yield {"event": "ping", "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})}

                # Wait a bit before next iteration
                await asyncio.sleep(10)

        except ValueError as e:
            event = GatewayEvent(
                type="error", server_id=server_id, data={"error": str(e)}
            )
            yield {"event": "error", "data": event.model_dump_json()}

        except ConnectionError as e:
            event = GatewayEvent(
                type="error",
                server_id=server_id,
                data={"error": f"Server unavailable: {e}"},
            )
            yield {"event": "error", "data": event.model_dump_json()}

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for {server_id}")

        except Exception as e:
            logger.error(f"Error in SSE proxy: {e}", exc_info=True)
            event = GatewayEvent(
                type="error", server_id=server_id, data={"error": str(e)}
            )
            yield {"event": "error", "data": event.model_dump_json()}

        finally:
            # Send disconnected event
            event = GatewayEvent(
                type="disconnected",
                server_id=server_id,
                data={"message": "Disconnected from MCP server"},
            )
            yield {"event": "disconnected", "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


@router.post("/{server_id}/tools/{tool_name}", response_model=ToolCallResponse)
async def call_tool_direct(
    server_id: str = Path(..., description="MCP Server ID"),
    tool_name: str = Path(..., description="Tool name"),
    request_data: ToolCallRequest = ...,
    manager: MCPConnectionManager = Depends(get_connection_manager),
):
    """
    Direct tool invocation endpoint.

    Call an MCP tool directly via a simple REST interface.
    This is a convenience endpoint for non-MCP clients.

    Args:
        server_id: The ID of the registered MCP server
        tool_name: Name of the tool to call
        request_data: Tool arguments

    Returns:
        Tool execution result

    Example:
        POST /mcp/gateway/{server_id}/tools/get_weather
        {
          "arguments": {
            "location": "San Francisco"
          }
        }
    """
    try:
        conn = await manager.get_connection(server_id)
        result = await conn.session.call_tool(tool_name, request_data.arguments)

        return ToolCallResponse(
            tool=tool_name, content=result.content, isError=result.isError
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Server unavailable: {e}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Tool execution timeout")
    except Exception as e:
        logger.error(f"Error calling tool: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/resources/read", response_model=ResourceReadResponse)
async def read_resource_direct(
    server_id: str = Path(..., description="MCP Server ID"),
    request_data: ResourceReadRequest = ...,
    manager: MCPConnectionManager = Depends(get_connection_manager),
):
    """
    Direct resource read endpoint.

    Read an MCP resource directly via a simple REST interface.

    Args:
        server_id: The ID of the registered MCP server
        request_data: Resource URI to read

    Returns:
        Resource contents
    """
    try:
        conn = await manager.get_connection(server_id)
        result = await conn.session.read_resource(request_data.uri)

        return ResourceReadResponse(uri=request_data.uri, contents=result.contents)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Server unavailable: {e}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Resource read timeout")
    except Exception as e:
        logger.error(f"Error reading resource: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/prompts/get", response_model=PromptGetResponse)
async def get_prompt_direct(
    server_id: str = Path(..., description="MCP Server ID"),
    request_data: PromptGetRequest = ...,
    manager: MCPConnectionManager = Depends(get_connection_manager),
):
    """
    Direct prompt get endpoint.

    Get an MCP prompt directly via a simple REST interface.

    Args:
        server_id: The ID of the registered MCP server
        request_data: Prompt name and arguments

    Returns:
        Prompt messages
    """
    try:
        conn = await manager.get_connection(server_id)
        result = await conn.session.get_prompt(
            request_data.name, request_data.arguments
        )

        return PromptGetResponse(name=request_data.name, messages=result.messages)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Server unavailable: {e}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Prompt get timeout")
    except Exception as e:
        logger.error(f"Error getting prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/status", response_model=ConnectionStatus)
async def get_connection_status(
    server_id: str = Path(..., description="MCP Server ID"),
    manager: MCPConnectionManager = Depends(get_connection_manager),
):
    """
    Get connection status for a specific server.

    Returns:
        Connection status information
    """
    status = manager.get_connection_status(server_id)

    if not status:
        # No active connection
        return ConnectionStatus(
            server_id=server_id,
            status="disconnected",
            connected_at=None,
            last_activity=None,
            error_message=None,
            request_count=0,
        )

    return status


@router.get("/health", response_model=GatewayHealthResponse)
async def gateway_health(
    manager: MCPConnectionManager = Depends(get_connection_manager),
):
    """
    Get overall gateway health status.

    Returns:
        Health information for all connections
    """
    statuses = manager.get_all_connection_statuses()
    total_connections = len(statuses)
    active_servers = sum(1 for s in statuses.values() if s.status == "connected")

    # Determine overall health
    if total_connections == 0:
        overall_status = "healthy"
    elif active_servers == total_connections:
        overall_status = "healthy"
    elif active_servers > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return GatewayHealthResponse(
        status=overall_status,
        total_connections=total_connections,
        active_servers=active_servers,
        connections=list(statuses.values()),
    )
