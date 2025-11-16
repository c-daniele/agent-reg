"""
MCP Gateway Data Models

Models for the gateway proxy functionality that exposes all MCP servers
through unified HTTP/SSE endpoints.
"""

from typing import Optional, Dict, Any, List, Literal, Union
from pydantic import BaseModel, Field
from datetime import datetime


# JSON-RPC 2.0 Models
class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[Union[str, int]] = Field(None, description="Request ID")
    method: str = Field(..., description="Method to call")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Method parameters")


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 error"""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(None, description="Additional error data")


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[Union[str, int]] = Field(None, description="Request ID")
    result: Optional[Any] = Field(None, description="Result data")
    error: Optional[JSONRPCError] = Field(None, description="Error data")


# Gateway-specific Models
class ToolCallRequest(BaseModel):
    """Request to call a tool via gateway"""
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Response from tool call"""
    tool: str = Field(..., description="Tool name")
    content: List[Any] = Field(..., description="Tool result content")
    isError: bool = Field(default=False, description="Whether call resulted in error")


class ResourceReadRequest(BaseModel):
    """Request to read a resource via gateway"""
    uri: str = Field(..., description="Resource URI to read")


class ResourceReadResponse(BaseModel):
    """Response from resource read"""
    uri: str = Field(..., description="Resource URI")
    contents: List[Any] = Field(..., description="Resource contents")
    mimeType: Optional[str] = Field(None, description="Content MIME type")


class PromptGetRequest(BaseModel):
    """Request to get a prompt via gateway"""
    name: str = Field(..., description="Prompt name")
    arguments: Optional[Dict[str, str]] = Field(None, description="Prompt arguments")


class PromptGetResponse(BaseModel):
    """Response from prompt get"""
    name: str = Field(..., description="Prompt name")
    messages: List[Any] = Field(..., description="Prompt messages")


# Connection Status Models
class ConnectionStatus(BaseModel):
    """Status of a gateway connection to an MCP server"""
    server_id: str = Field(..., description="MCP server ID")
    status: Literal["connected", "connecting", "disconnected", "error"] = Field(
        ..., description="Connection status"
    )
    connected_at: Optional[datetime] = Field(None, description="When connection was established")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    error_message: Optional[str] = Field(None, description="Error message if status is error")
    request_count: int = Field(default=0, description="Number of requests handled")


class GatewayHealthResponse(BaseModel):
    """Health status of the gateway"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall health")
    total_connections: int = Field(..., description="Total active connections")
    active_servers: int = Field(..., description="Number of servers with active connections")
    connections: List[ConnectionStatus] = Field(..., description="Individual connection statuses")


# SSE Event Models
class SSEEvent(BaseModel):
    """Server-Sent Event"""
    event: Optional[str] = Field(None, description="Event type")
    data: str = Field(..., description="Event data (JSON string)")
    id: Optional[str] = Field(None, description="Event ID")
    retry: Optional[int] = Field(None, description="Reconnection time in ms")


class GatewayEvent(BaseModel):
    """Gateway-specific event"""
    type: Literal["connected", "message", "error", "disconnected"] = Field(
        ..., description="Event type"
    )
    server_id: str = Field(..., description="MCP server ID")
    data: Optional[Any] = Field(None, description="Event payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
