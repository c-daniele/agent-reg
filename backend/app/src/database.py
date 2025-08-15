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
        """Initialize database with agents table"""
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