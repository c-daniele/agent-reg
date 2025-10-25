"""
SQLite database module with JSON support for Agent Registry
Replaces TinyDB with more scalable SQLite solution
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from contextlib import contextmanager

class AgentDatabase:
    """SQLite database wrapper with JSON support for agent storage"""
    
    def __init__(self, db_path: str = "agent_hub.db"):
        self.db_path = db_path
        self._connection = None
        if db_path == ':memory:':
            # For in-memory databases, keep a persistent connection
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        self._init_database()
    
    def _init_database(self):
        """Initialize database with agents table and MCP tables"""
        if self._connection:
            conn = self._connection
            close_after = False
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            close_after = True

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    agent_card TEXT NOT NULL,  -- JSON string
                    owner TEXT,
                    created_at TEXT NOT NULL,
                    last_heartbeat TEXT,
                    -- Extracted fields for efficient querying
                    name TEXT GENERATED ALWAYS AS (json_extract(agent_card, '$.name')) STORED,
                    capabilities TEXT GENERATED ALWAYS AS (json_extract(agent_card, '$.capabilities')) STORED
                )
            """)

            # Create indexes for efficient querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_last_heartbeat ON agents(last_heartbeat)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON agents(capabilities)")

            # Create MCP servers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,  -- stdio, http, sse
                    description TEXT,
                    config TEXT NOT NULL,  -- JSON string
                    created_at TEXT NOT NULL,
                    last_verified TEXT,
                    status TEXT DEFAULT 'active'  -- active, inactive, error
                )
            """)

            # Create MCP capabilities tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    input_schema TEXT,  -- JSON string
                    FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    mime_type TEXT,
                    FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    arguments TEXT,  -- JSON string
                    FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for MCP tables
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_servers_type ON mcp_servers(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_servers_status ON mcp_servers(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_tools_server_id ON mcp_tools(server_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_tools_name ON mcp_tools(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_resources_server_id ON mcp_resources(server_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_resources_name ON mcp_resources(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_prompts_server_id ON mcp_prompts(server_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_prompts_name ON mcp_prompts(name)")

            conn.commit()
        finally:
            if close_after:
                conn.close()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        if self._connection:
            # For in-memory databases, reuse the persistent connection
            yield self._connection
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()
    
    def insert_agent(self, agent_id: str, agent_card: Dict[str, Any], owner: Optional[str] = None) -> Dict[str, Any]:
        """Insert a new agent"""
        now = datetime.now(timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO agents (id, agent_card, owner, created_at, last_heartbeat)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, json.dumps(agent_card), owner, now, now))
            conn.commit()
        
        return self.get_agent(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a single agent by ID"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT id, agent_card, owner, created_at, last_heartbeat
                FROM agents WHERE id = ?
            """, (agent_id,)).fetchone()
            
            if not row:
                return None
            
            agent_data = json.loads(row['agent_card'])
            agent_data.update({
                'id': row['id'],
                'owner': row['owner'],
                'created_at': row['created_at'],
                'last_heartbeat': row['last_heartbeat']
            })
            return agent_data
    
    def list_agents(self, 
                   skill: Optional[str] = None,
                   name: Optional[str] = None,
                   owner: Optional[str] = None,
                   streaming: bool = False,
                   push_notifications: bool = False,
                   state_transition_history: bool = False,
                   only_alive: bool = False) -> List[Dict[str, Any]]:
        """List agents with efficient WHERE conditions"""
        
        # Build WHERE clause dynamically
        conditions = []
        params = []
        
        if owner:
            conditions.append("owner = ?")
            params.append(owner)
        
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name.lower()}%")
        
        if only_alive:
            cutoff_time = datetime.now(timezone.utc)
            cutoff_iso = (cutoff_time.timestamp() - 300) * 1000  # 5 minutes ago in ms
            conditions.append("datetime(last_heartbeat) > datetime(?, 'unixepoch')")
            params.append(cutoff_iso / 1000)
        
        if streaming:
            conditions.append("json_extract(capabilities, '$.streaming') = 1")
        
        if push_notifications:
            conditions.append("(json_extract(capabilities, '$.pushNotifications') = 1 OR json_extract(capabilities, '$.push_notifications') = 1)")
        
        if state_transition_history:
            conditions.append("(json_extract(capabilities, '$.stateTransitionHistory') = 1 OR json_extract(capabilities, '$.state_transition_history') = 1)")
        
        if skill:
            conditions.append("EXISTS (SELECT 1 FROM json_each(agent_card, '$.skills') WHERE json_extract(value, '$.id') = ?)")
            params.append(skill)
        
        # Build final query
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""
            SELECT id, agent_card, owner, created_at, last_heartbeat
            FROM agents{where_clause}
            ORDER BY created_at DESC
        """
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            
            results = []
            for row in rows:
                agent_data = json.loads(row['agent_card'])
                agent_data.update({
                    'id': row['id'],
                    'owner': row['owner'],
                    'created_at': row['created_at'],
                    'last_heartbeat': row['last_heartbeat']
                })
                results.append(agent_data)
            
            return results
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent card data"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # Remove metadata fields from agent before updating
        agent_card = {k: v for k, v in agent.items() 
                     if k not in ['id', 'owner', 'created_at', 'last_heartbeat']}
        
        # Apply updates to agent card
        for field, value in updates.items():
            if hasattr(value, 'model_dump'):
                agent_card[field] = value.model_dump()
            elif field == "url":
                agent_card[field] = str(value)
            else:
                agent_card[field] = value
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE agents SET agent_card = ? WHERE id = ?
            """, (json.dumps(agent_card), agent_id))
            conn.commit()
            return conn.total_changes > 0
    
    def update_heartbeat(self, agent_id: str) -> bool:
        """Update agent's last heartbeat"""
        now = datetime.now(timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE agents SET last_heartbeat = ? WHERE id = ?
            """, (now, agent_id))
            conn.commit()
            return conn.total_changes > 0

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            conn.commit()
            return conn.total_changes > 0

    def count_agents(self) -> int:
        """Get total count of agents"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM agents").fetchone()
            return row['count'] if row else 0

    # ========== MCP Server Methods ==========

    def insert_mcp_server(self, server_id: str, server_type: str, description: Optional[str],
                         config: Dict[str, Any], capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new MCP server with its capabilities"""
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            # Insert server
            conn.execute("""
                INSERT INTO mcp_servers (id, type, description, config, created_at, last_verified, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (server_id, server_type, description, json.dumps(config), now, now, 'active'))

            # Insert tools
            if capabilities.get('tools'):
                for tool in capabilities['tools']:
                    conn.execute("""
                        INSERT INTO mcp_tools (server_id, name, description, input_schema)
                        VALUES (?, ?, ?, ?)
                    """, (server_id, tool.get('name'), tool.get('description'),
                          json.dumps(tool.get('inputSchema')) if tool.get('inputSchema') else None))

            # Insert resources
            if capabilities.get('resources'):
                for resource in capabilities['resources']:
                    conn.execute("""
                        INSERT INTO mcp_resources (server_id, uri, name, description, mime_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (server_id, resource.get('uri'), resource.get('name'),
                          resource.get('description'), resource.get('mimeType')))

            # Insert prompts
            if capabilities.get('prompts'):
                for prompt in capabilities['prompts']:
                    conn.execute("""
                        INSERT INTO mcp_prompts (server_id, name, description, arguments)
                        VALUES (?, ?, ?, ?)
                    """, (server_id, prompt.get('name'), prompt.get('description'),
                          json.dumps(prompt.get('arguments')) if prompt.get('arguments') else None))

            conn.commit()

        return self.get_mcp_server(server_id)

    def get_mcp_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get an MCP server with its capabilities"""
        with self._get_connection() as conn:
            server_row = conn.execute("""
                SELECT id, type, description, config, created_at, last_verified, status
                FROM mcp_servers WHERE id = ?
            """, (server_id,)).fetchone()

            if not server_row:
                return None

            # Get tools
            tools = conn.execute("""
                SELECT name, description, input_schema FROM mcp_tools WHERE server_id = ?
            """, (server_id,)).fetchall()

            # Get resources
            resources = conn.execute("""
                SELECT uri, name, description, mime_type FROM mcp_resources WHERE server_id = ?
            """, (server_id,)).fetchall()

            # Get prompts
            prompts = conn.execute("""
                SELECT name, description, arguments FROM mcp_prompts WHERE server_id = ?
            """, (server_id,)).fetchall()

            return {
                'id': server_row['id'],
                'type': server_row['type'],
                'description': server_row['description'],
                'config': json.loads(server_row['config']),
                'created_at': server_row['created_at'],
                'last_verified': server_row['last_verified'],
                'status': server_row['status'],
                'capabilities': {
                    'tools': [{'name': t['name'], 'description': t['description'],
                              'inputSchema': json.loads(t['input_schema']) if t['input_schema'] else None}
                             for t in tools],
                    'resources': [{'uri': r['uri'], 'name': r['name'],
                                  'description': r['description'], 'mimeType': r['mime_type']}
                                 for r in resources],
                    'prompts': [{'name': p['name'], 'description': p['description'],
                                'arguments': json.loads(p['arguments']) if p['arguments'] else None}
                               for p in prompts]
                }
            }

    def list_mcp_servers(self, server_type: Optional[str] = None,
                        status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all MCP servers with their capabilities"""
        conditions = []
        params = []

        if server_type:
            conditions.append("type = ?")
            params.append(server_type)

        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT id FROM mcp_servers{where_clause} ORDER BY created_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self.get_mcp_server(row['id']) for row in rows]

    def search_mcp_capabilities(self, query: Optional[str] = None,
                               capability_type: Optional[str] = None,
                               server_type: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Search for MCP capabilities across all servers"""
        results = []

        with self._get_connection() as conn:
            # Build server filter
            server_filter = ""
            server_params = []
            if server_type:
                server_filter = " AND s.type = ?"
                server_params.append(server_type)

            # Search tools
            if not capability_type or capability_type == 'tool':
                tool_query = f"""
                    SELECT DISTINCT s.id as server_id
                    FROM mcp_servers s
                    JOIN mcp_tools t ON s.id = t.server_id
                    WHERE s.status = 'active'{server_filter}
                """
                tool_params = server_params.copy()

                if query:
                    tool_query += " AND (t.name LIKE ? OR t.description LIKE ?)"
                    tool_params.extend([f"%{query}%", f"%{query}%"])

                tool_query += " LIMIT ?"
                tool_params.append(limit)

                tool_rows = conn.execute(tool_query, tool_params).fetchall()
                for row in tool_rows:
                    server = self.get_mcp_server(row['server_id'])
                    if server:
                        # Filter matched tools
                        matched_tools = server['capabilities']['tools']
                        if query:
                            matched_tools = [t for t in matched_tools
                                           if query.lower() in (t.get('name', '') or '').lower()
                                           or query.lower() in (t.get('description', '') or '').lower()]

                        results.append({
                            'server_id': server['id'],
                            'server_type': server['type'],
                            'server_description': server['description'],
                            'server_config': server['config'],
                            'matched_tools': matched_tools,
                            'matched_resources': [],
                            'matched_prompts': []
                        })

            # Search resources
            if not capability_type or capability_type == 'resource':
                resource_query = f"""
                    SELECT DISTINCT s.id as server_id
                    FROM mcp_servers s
                    JOIN mcp_resources r ON s.id = r.server_id
                    WHERE s.status = 'active'{server_filter}
                """
                resource_params = server_params.copy()

                if query:
                    resource_query += " AND (r.name LIKE ? OR r.description LIKE ? OR r.uri LIKE ?)"
                    resource_params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

                resource_query += " LIMIT ?"
                resource_params.append(limit)

                resource_rows = conn.execute(resource_query, resource_params).fetchall()
                for row in resource_rows:
                    server = self.get_mcp_server(row['server_id'])
                    if server:
                        # Filter matched resources
                        matched_resources = server['capabilities']['resources']
                        if query:
                            matched_resources = [r for r in matched_resources
                                               if query.lower() in (r.get('name', '') or '').lower()
                                               or query.lower() in (r.get('description', '') or '').lower()
                                               or query.lower() in (r.get('uri', '') or '').lower()]

                        # Check if server already in results
                        existing = next((r for r in results if r['server_id'] == server['id']), None)
                        if existing:
                            existing['matched_resources'] = matched_resources
                        else:
                            results.append({
                                'server_id': server['id'],
                                'server_type': server['type'],
                                'server_description': server['description'],
                                'server_config': server['config'],
                                'matched_tools': [],
                                'matched_resources': matched_resources,
                                'matched_prompts': []
                            })

            # Search prompts
            if not capability_type or capability_type == 'prompt':
                prompt_query = f"""
                    SELECT DISTINCT s.id as server_id
                    FROM mcp_servers s
                    JOIN mcp_prompts p ON s.id = p.server_id
                    WHERE s.status = 'active'{server_filter}
                """
                prompt_params = server_params.copy()

                if query:
                    prompt_query += " AND (p.name LIKE ? OR p.description LIKE ?)"
                    prompt_params.extend([f"%{query}%", f"%{query}%"])

                prompt_query += " LIMIT ?"
                prompt_params.append(limit)

                prompt_rows = conn.execute(prompt_query, prompt_params).fetchall()
                for row in prompt_rows:
                    server = self.get_mcp_server(row['server_id'])
                    if server:
                        # Filter matched prompts
                        matched_prompts = server['capabilities']['prompts']
                        if query:
                            matched_prompts = [p for p in matched_prompts
                                             if query.lower() in (p.get('name', '') or '').lower()
                                             or query.lower() in (p.get('description', '') or '').lower()]

                        # Check if server already in results
                        existing = next((r for r in results if r['server_id'] == server['id']), None)
                        if existing:
                            existing['matched_prompts'] = matched_prompts
                        else:
                            results.append({
                                'server_id': server['id'],
                                'server_type': server['type'],
                                'server_description': server['description'],
                                'server_config': server['config'],
                                'matched_tools': [],
                                'matched_resources': [],
                                'matched_prompts': matched_prompts
                            })

            return results[:limit]

    def delete_mcp_server(self, server_id: str) -> bool:
        """Delete an MCP server and all its capabilities"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM mcp_servers WHERE id = ?", (server_id,))
            conn.commit()
            return conn.total_changes > 0

    def update_mcp_server_status(self, server_id: str, status: str,
                                 last_verified: Optional[str] = None) -> bool:
        """Update MCP server status and verification timestamp"""
        if last_verified is None:
            last_verified = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE mcp_servers SET status = ?, last_verified = ? WHERE id = ?
            """, (status, last_verified, server_id))
            conn.commit()
            return conn.total_changes > 0