"""
MCP Connection Manager

Manages persistent connections to registered MCP servers, providing:
- Connection pooling (one session per server)
- Keep-alive for stdio servers
- Auto-reconnection on failure
- Connection health monitoring
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client

from database import AgentDatabase
from mcp_gateway_models import ConnectionStatus

logger = logging.getLogger(__name__)


class MCPConnection:
    """Represents a single connection to an MCP server"""

    def __init__(
        self,
        server_id: str,
        server_type: str,
        config: Dict[str, Any],
        session: ClientSession,
        read_stream: Any,
        write_stream: Any,
        client_context: Any = None,
        session_context: Any = None,
    ):
        self.server_id = server_id
        self.server_type = server_type
        self.config = config
        self.session = session
        self.read_stream = read_stream
        self.write_stream = write_stream
        self.client_context = client_context  # Store the client context manager
        self.session_context = session_context  # Store the session context manager
        self.connected_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.request_count = 0
        self.is_healthy = True
        self.error_message: Optional[str] = None
        self._lock = asyncio.Lock()

    async def update_activity(self):
        """Update last activity timestamp and increment request count"""
        self.last_activity = datetime.now(timezone.utc)
        self.request_count += 1

    async def health_check(self) -> bool:
        """Perform a health check on the connection"""
        try:
            # Try to ping the server (if supported) or list tools as a health check
            async with asyncio.timeout(5.0):
                await self.session.list_tools()
            self.is_healthy = True
            self.error_message = None
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.server_id}: {e}")
            self.is_healthy = False
            self.error_message = str(e)
            return False

    def get_status(self) -> ConnectionStatus:
        """Get current connection status"""
        status = "connected" if self.is_healthy else "error"
        return ConnectionStatus(
            server_id=self.server_id,
            status=status,
            connected_at=self.connected_at,
            last_activity=self.last_activity,
            error_message=self.error_message,
            request_count=self.request_count,
        )


class MCPConnectionManager:
    """
    Manages connections to all registered MCP servers.

    Features:
    - Connection pooling (reuse connections)
    - Auto-reconnection on failure
    - Idle connection cleanup
    - Health monitoring
    """

    def __init__(self, database: AgentDatabase, idle_timeout: int = 300):
        """
        Initialize connection manager.

        Args:
            database: Database instance for server lookups
            idle_timeout: Seconds before closing idle connections (default: 5 minutes)
        """
        self.db = database
        self.idle_timeout = idle_timeout
        self.connections: Dict[str, MCPConnection] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the connection manager and cleanup task"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("MCPConnectionManager started")

    async def stop(self):
        """Stop the connection manager and close all connections"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await self.close_all_connections()
        logger.info("MCPConnectionManager stopped")

    def _get_lock(self, server_id: str) -> asyncio.Lock:
        """Get or create a lock for the given server"""
        if server_id not in self._locks:
            self._locks[server_id] = asyncio.Lock()
        return self._locks[server_id]

    async def get_connection(self, server_id: str) -> MCPConnection:
        """
        Get or create a connection for the given server.

        Args:
            server_id: MCP server ID

        Returns:
            MCPConnection instance

        Raises:
            ValueError: If server not found
            ConnectionError: If connection fails
        """
        # Check if connection exists and is healthy
        if server_id in self.connections:
            conn = self.connections[server_id]
            if conn.is_healthy:
                await conn.update_activity()
                return conn
            else:
                # Connection is unhealthy, close and reconnect
                logger.info(f"Connection unhealthy for {server_id}, reconnecting...")
                await self._close_connection(server_id)

        # Acquire lock for this server to prevent duplicate connections
        lock = self._get_lock(server_id)
        async with lock:
            # Double-check after acquiring lock
            if server_id in self.connections:
                conn = self.connections[server_id]
                await conn.update_activity()
                return conn

            # Create new connection
            return await self._create_connection(server_id)

    async def _create_connection(self, server_id: str) -> MCPConnection:
        """Create a new connection to an MCP server"""
        # Get server details from database
        server = self.db.get_mcp_server(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")

        logger.info(f"Creating connection to {server_id} ({server['type']})")

        try:
            if server["type"] == "stdio":
                conn = await self._create_stdio_connection(server_id, server)
            elif server["type"] in ["http", "sse"]:
                conn = await self._create_http_connection(server_id, server)
            else:
                raise ValueError(f"Unsupported server type: {server['type']}")

            self.connections[server_id] = conn
            logger.info(f"Connected to {server_id}")
            return conn

        except Exception as e:
            logger.error(f"Failed to connect to {server_id}: {e}")
            raise ConnectionError(f"Failed to connect to server: {e}")

    async def _create_stdio_connection(
        self, server_id: str, server: Dict[str, Any]
    ) -> MCPConnection:
        """Create a stdio connection"""
        config = server["config"]
        params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env"),
        )

        # Create stdio client context and keep reference
        client_context = stdio_client(params)
        read_stream, write_stream = await client_context.__aenter__()

        # Create session context and keep reference
        session_context = ClientSession(read_stream, write_stream)
        session = await session_context.__aenter__()

        # Initialize session
        await session.initialize()

        return MCPConnection(
            server_id=server_id,
            server_type="stdio",
            config=config,
            session=session,
            read_stream=read_stream,
            write_stream=write_stream,
            client_context=client_context,
            session_context=session_context,
        )

    async def _create_http_connection(
        self, server_id: str, server: Dict[str, Any]
    ) -> MCPConnection:
        """Create an HTTP/SSE connection"""
        config = server["config"]
        url = config["url"]
        headers = config.get("headers", {})

        # Create HTTP client context and keep reference
        client_context = streamablehttp_client(url, headers=headers)
        read_stream, write_stream, session_info = await client_context.__aenter__()

        # Create session context and keep reference
        session_context = ClientSession(read_stream, write_stream)
        session = await session_context.__aenter__()

        # Initialize session
        await session.initialize()

        return MCPConnection(
            server_id=server_id,
            server_type=server["type"],
            config=config,
            session=session,
            read_stream=read_stream,
            write_stream=write_stream,
            client_context=client_context,
            session_context=session_context,
        )

    async def _close_connection(self, server_id: str):
        """Close a connection"""
        if server_id not in self.connections:
            return

        conn = self.connections[server_id]
        logger.info(f"Closing connection to {server_id}")

        try:
            # Close session context first
            if conn.session_context:
                try:
                    await conn.session_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"Error closing session for {server_id}: {e}")

            # Then close client context
            if conn.client_context:
                try:
                    await conn.client_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"Error closing client for {server_id}: {e}")

        except Exception as e:
            logger.error(f"Error closing connection to {server_id}: {e}")
        finally:
            del self.connections[server_id]

    async def close_all_connections(self):
        """Close all active connections"""
        server_ids = list(self.connections.keys())
        for server_id in server_ids:
            await self._close_connection(server_id)

    async def _cleanup_loop(self):
        """Periodically clean up idle connections"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_idle_connections(self):
        """Close connections that have been idle for too long"""
        now = datetime.now(timezone.utc)
        to_close = []

        for server_id, conn in self.connections.items():
            idle_seconds = (now - conn.last_activity).total_seconds()
            if idle_seconds > self.idle_timeout:
                logger.info(
                    f"Closing idle connection to {server_id} "
                    f"(idle for {idle_seconds:.0f}s)"
                )
                to_close.append(server_id)

        for server_id in to_close:
            await self._close_connection(server_id)

    async def health_check(self, server_id: str) -> bool:
        """
        Perform health check on a specific server connection.

        Args:
            server_id: MCP server ID

        Returns:
            True if healthy, False otherwise
        """
        if server_id not in self.connections:
            return False

        conn = self.connections[server_id]
        return await conn.health_check()

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all connections.

        Returns:
            Dict mapping server_id to health status
        """
        results = {}
        for server_id in self.connections:
            results[server_id] = await self.health_check(server_id)
        return results

    def get_connection_status(self, server_id: str) -> Optional[ConnectionStatus]:
        """Get status of a specific connection"""
        if server_id not in self.connections:
            return None
        return self.connections[server_id].get_status()

    def get_all_connection_statuses(self) -> Dict[str, ConnectionStatus]:
        """Get status of all connections"""
        return {
            server_id: conn.get_status()
            for server_id, conn in self.connections.items()
        }

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)


# Global connection manager instance
_connection_manager: Optional[MCPConnectionManager] = None


def get_connection_manager() -> MCPConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        raise RuntimeError("Connection manager not initialized")
    return _connection_manager


def initialize_connection_manager(database: AgentDatabase) -> MCPConnectionManager:
    """Initialize the global connection manager"""
    global _connection_manager
    _connection_manager = MCPConnectionManager(database)
    return _connection_manager
