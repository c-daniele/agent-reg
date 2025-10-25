"""
MCP Client Connector using Official MCP SDK

This module provides functionality to connect to MCP servers,
perform handshakes, and discover their capabilities using the
official Anthropic MCP SDK.
"""

from typing import Dict, Any
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from .mcp_models import MCPServerCapabilities


class MCPClientError(Exception):
    """Base exception for MCP client errors"""
    pass


class MCPClient:
    """Client for connecting to and discovering MCP server capabilities using official SDK"""

    def __init__(self, server_type: str, config: Dict[str, Any]):
        """
        Initialize MCP client

        Args:
            server_type: Type of server (stdio, http, sse)
            config: Server configuration (command/args/env for stdio, url/headers for http/sse)
        """
        self.server_type = server_type
        self.config = config
        self.timeout = 30  # seconds

    async def discover_capabilities(self) -> MCPServerCapabilities:
        """
        Connect to MCP server and discover its capabilities

        Returns:
            MCPServerCapabilities object with tools, resources, and prompts

        Raises:
            MCPClientError: If connection or capability discovery fails
        """
        if self.server_type == "stdio":
            return await self._discover_stdio_capabilities()
        elif self.server_type in ["http", "sse"]:
            return await self._discover_http_capabilities()
        else:
            raise MCPClientError(f"Unsupported server type: {self.server_type}")

    async def _discover_stdio_capabilities(self) -> MCPServerCapabilities:
        """Discover capabilities from a stdio-based MCP server using official SDK"""
        command = self.config.get("command")
        args = self.config.get("args", [])
        env = self.config.get("env")

        if not command:
            raise MCPClientError("stdio server requires 'command'")

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env
            )

            # Connect to server and create session
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    # Discover tools
                    tools = []
                    try:
                        tools_result = await session.list_tools()
                        tools = [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else None
                            }
                            for tool in tools_result.tools
                        ]
                    except Exception:
                        # Some servers may not support tools
                        pass

                    # Discover resources
                    resources = []
                    try:
                        resources_result = await session.list_resources()
                        resources = [
                            {
                                "uri": resource.uri,
                                "name": resource.name,
                                "description": resource.description if hasattr(resource, 'description') else None,
                                "mimeType": resource.mimeType if hasattr(resource, 'mimeType') else None
                            }
                            for resource in resources_result.resources
                        ]
                    except Exception:
                        # Some servers may not support resources
                        pass

                    # Discover prompts
                    prompts = []
                    try:
                        prompts_result = await session.list_prompts()
                        prompts = [
                            {
                                "name": prompt.name,
                                "description": prompt.description if hasattr(prompt, 'description') else None,
                                "arguments": [
                                    {
                                        "name": arg.name,
                                        "description": arg.description if hasattr(arg, 'description') else None,
                                        "required": arg.required if hasattr(arg, 'required') else False
                                    }
                                    for arg in (prompt.arguments if hasattr(prompt, 'arguments') else [])
                                ]
                            }
                            for prompt in prompts_result.prompts
                        ]
                    except Exception:
                        # Some servers may not support prompts
                        pass

                    return MCPServerCapabilities(
                        tools=tools,
                        resources=resources,
                        prompts=prompts
                    )

        except FileNotFoundError:
            raise MCPClientError(f"Command not found: {command}")
        except Exception as e:
            if not isinstance(e, MCPClientError):
                raise MCPClientError(f"Failed to connect to stdio server: {str(e)}")
            raise

    async def _discover_http_capabilities(self) -> MCPServerCapabilities:
        """Discover capabilities from an HTTP or SSE-based MCP server using official SDK"""
        url = self.config.get("url")
        headers = self.config.get("headers", {})

        if not url:
            raise MCPClientError("http/sse server requires 'url'")

        try:
            # Connect to HTTP server using streamable HTTP client
            async with streamablehttp_client(url, headers=headers) as (read, write, session_info):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    # Discover tools
                    tools = []
                    try:
                        tools_result = await session.list_tools()
                        tools = [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else None
                            }
                            for tool in tools_result.tools
                        ]
                    except Exception:
                        # Some servers may not support tools
                        pass

                    # Discover resources
                    resources = []
                    try:
                        resources_result = await session.list_resources()
                        resources = [
                            {
                                "uri": resource.uri,
                                "name": resource.name,
                                "description": resource.description if hasattr(resource, 'description') else None,
                                "mimeType": resource.mimeType if hasattr(resource, 'mimeType') else None
                            }
                            for resource in resources_result.resources
                        ]
                    except Exception:
                        # Some servers may not support resources
                        pass

                    # Discover prompts
                    prompts = []
                    try:
                        prompts_result = await session.list_prompts()
                        prompts = [
                            {
                                "name": prompt.name,
                                "description": prompt.description if hasattr(prompt, 'description') else None,
                                "arguments": [
                                    {
                                        "name": arg.name,
                                        "description": arg.description if hasattr(arg, 'description') else None,
                                        "required": arg.required if hasattr(arg, 'required') else False
                                    }
                                    for arg in (prompt.arguments if hasattr(prompt, 'arguments') else [])
                                ]
                            }
                            for prompt in prompts_result.prompts
                        ]
                    except Exception:
                        # Some servers may not support prompts
                        pass

                    return MCPServerCapabilities(
                        tools=tools,
                        resources=resources,
                        prompts=prompts
                    )

        except Exception as e:
            if not isinstance(e, MCPClientError):
                raise MCPClientError(f"Failed to connect to HTTP server: {str(e)}")
            raise


async def test_mcp_connection(server_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test connection to an MCP server and return capabilities

    Args:
        server_type: Type of server (stdio, http, sse)
        config: Server configuration

    Returns:
        Dict with status and capabilities or error message
    """
    try:
        client = MCPClient(server_type, config)
        capabilities = await client.discover_capabilities()
        return {
            "status": "success",
            "capabilities": capabilities.model_dump()
        }
    except MCPClientError as e:
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }
