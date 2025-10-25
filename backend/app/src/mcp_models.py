"""
MCP (Model Context Protocol) Server Data Models

This module defines Pydantic models for MCP server registration,
management, and capability tracking.
"""

from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field, field_validator


class MCPServerStdioConfig(BaseModel):
    """Configuration for stdio-based MCP servers"""
    command: str = Field(..., description="Command to execute")
    args: Optional[List[str]] = Field(default=None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")


class MCPServerHttpConfig(BaseModel):
    """Configuration for HTTP/SSE-based MCP servers"""
    url: str = Field(..., description="Server URL")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers")


class MCPToolCapability(BaseModel):
    """Represents a tool capability exposed by an MCP server"""
    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    inputSchema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for tool input")


class MCPResourceCapability(BaseModel):
    """Represents a resource capability exposed by an MCP server"""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mimeType: Optional[str] = Field(None, description="MIME type of the resource")


class MCPPromptCapability(BaseModel):
    """Represents a prompt capability exposed by an MCP server"""
    name: str = Field(..., description="Prompt name")
    description: Optional[str] = Field(None, description="Prompt description")
    arguments: Optional[List[Dict[str, Any]]] = Field(None, description="Prompt arguments")


class MCPServerCapabilities(BaseModel):
    """Capabilities discovered from an MCP server"""
    tools: Optional[List[MCPToolCapability]] = Field(default_factory=list)
    resources: Optional[List[MCPResourceCapability]] = Field(default_factory=list)
    prompts: Optional[List[MCPPromptCapability]] = Field(default_factory=list)


class MCPServerRegister(BaseModel):
    """Request model for registering an MCP server"""
    type: Literal["stdio", "http", "sse"] = Field(..., description="Server transport type")
    description: Optional[str] = Field(None, description="Server description")

    # stdio fields
    command: Optional[str] = Field(None, description="Command to execute (stdio only)")
    args: Optional[List[str]] = Field(None, description="Command arguments (stdio only)")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables (stdio only)")

    # http/sse fields
    url: Optional[str] = Field(None, description="Server URL (http/sse only)")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers (http/sse only)")

    @field_validator('command')
    @classmethod
    def validate_stdio_command(cls, v, info):
        """Validate that command is provided for stdio type"""
        if info.data.get('type') == 'stdio' and not v:
            raise ValueError("command is required for stdio type")
        return v

    @field_validator('url')
    @classmethod
    def validate_http_url(cls, v, info):
        """Validate that url is provided for http/sse types"""
        if info.data.get('type') in ['http', 'sse'] and not v:
            raise ValueError("url is required for http and sse types")
        return v

    def get_config(self) -> Dict[str, Any]:
        """Get the configuration dict for the server type"""
        if self.type == "stdio":
            return {
                "command": self.command,
                "args": self.args or [],
                "env": self.env or {}
            }
        else:  # http or sse
            return {
                "url": self.url,
                "headers": self.headers or {}
            }


class MCPServerResponse(BaseModel):
    """Response model for MCP server details"""
    id: str = Field(..., description="Server ID")
    type: Literal["stdio", "http", "sse"] = Field(..., description="Server transport type")
    description: Optional[str] = Field(None, description="Server description")
    config: Dict[str, Any] = Field(..., description="Server configuration")
    capabilities: MCPServerCapabilities = Field(..., description="Server capabilities")
    created_at: str = Field(..., description="Registration timestamp")
    last_verified: Optional[str] = Field(None, description="Last verification timestamp")
    status: Literal["active", "inactive", "error"] = Field(default="active", description="Server status")


class MCPServerUpdate(BaseModel):
    """Request model for updating an MCP server"""
    description: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None


class MCPSearchResult(BaseModel):
    """Search result for MCP capabilities"""
    server_id: str = Field(..., description="MCP Server ID")
    server_type: Literal["stdio", "http", "sse"] = Field(..., description="Server transport type")
    server_description: Optional[str] = Field(None, description="Server description")
    server_config: Dict[str, Any] = Field(..., description="Server configuration")

    # Matched capabilities
    matched_tools: Optional[List[MCPToolCapability]] = Field(default_factory=list)
    matched_resources: Optional[List[MCPResourceCapability]] = Field(default_factory=list)
    matched_prompts: Optional[List[MCPPromptCapability]] = Field(default_factory=list)

    relevance_score: Optional[float] = Field(None, description="Search relevance score")


class MCPSearchQuery(BaseModel):
    """Query model for searching MCP capabilities"""
    query: Optional[str] = Field(None, description="Search query string")
    capability_type: Optional[Literal["tool", "resource", "prompt"]] = Field(
        None, description="Filter by capability type"
    )
    server_type: Optional[Literal["stdio", "http", "sse"]] = Field(
        None, description="Filter by server type"
    )
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum results")
