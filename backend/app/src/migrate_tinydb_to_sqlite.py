#!/usr/bin/env python3
"""
Migration script to transfer data from TinyDB (agent_hub_nosql.json) to SQLite database.
This is a one-time migration script that can be run to migrate existing agent data.
"""

import json
import os
import sys
from typing import Dict, Any
from database import AgentDatabase

def migrate_tinydb_to_sqlite(tinydb_file: str, sqlite_db_path: str, backup_existing: bool = True):
    """
    Migrate data from TinyDB JSON file to SQLite database.
    
    Args:
        tinydb_file: Path to the TinyDB JSON file
        sqlite_db_path: Path for the new SQLite database
        backup_existing: Whether to backup existing SQLite DB if it exists
    """
    
    # Check if TinyDB file exists
    if not os.path.exists(tinydb_file):
        print(f"❌ TinyDB file not found: {tinydb_file}")
        return False
    
    # Backup existing SQLite database if it exists
    if backup_existing and os.path.exists(sqlite_db_path):
        backup_path = f"{sqlite_db_path}.backup.{int(__import__('time').time())}"
        os.rename(sqlite_db_path, backup_path)
        print(f"📁 Backed up existing database to: {backup_path}")
    
    try:
        # Load TinyDB data
        print(f"📖 Reading TinyDB file: {tinydb_file}")
        with open(tinydb_file, 'r') as f:
            tinydb_data = json.load(f)
        
        # Extract agents table data
        agents_data = tinydb_data.get('agents', {})
        print(f"📊 Found {len(agents_data)} agents to migrate")
        
        if not agents_data:
            print("⚠️  No agents found in TinyDB file")
            return True
        
        # Initialize SQLite database
        print(f"🗄️  Creating SQLite database: {sqlite_db_path}")
        db = AgentDatabase(sqlite_db_path)
        
        # Migrate each agent
        migrated_count = 0
        errors = []
        
        for tinydb_key, agent_doc in agents_data.items():
            try:
                # Extract agent data from TinyDB document format
                agent_id = agent_doc['id']
                agent_card = agent_doc['agent_card']
                owner = agent_doc.get('owner')
                created_at = agent_doc['created_at']
                last_heartbeat = agent_doc.get('last_heartbeat')
                
                # Insert into SQLite (bypassing the auto-generation of timestamps)
                with db._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO agents (id, agent_card, owner, created_at, last_heartbeat)
                        VALUES (?, ?, ?, ?, ?)
                    """, (agent_id, json.dumps(agent_card), owner, created_at, last_heartbeat))
                    conn.commit()
                
                migrated_count += 1
                print(f"✅ Migrated agent: {agent_id} ({agent_card.get('name', 'Unknown')})")
                
            except Exception as e:
                error_msg = f"❌ Failed to migrate agent {tinydb_key}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        # Summary
        print(f"\n📈 Migration Summary:")
        print(f"  • Total agents in TinyDB: {len(agents_data)}")
        print(f"  • Successfully migrated: {migrated_count}")
        print(f"  • Errors: {len(errors)}")
        
        if errors:
            print(f"\n❌ Errors encountered:")
            for error in errors:
                print(f"  {error}")
        
        # Verify migration
        print(f"\n🔍 Verifying migration...")
        final_count = db.count_agents()
        print(f"  • Agents in SQLite database: {final_count}")
        
        if final_count == migrated_count:
            print("✅ Migration completed successfully!")
            return True
        else:
            print("⚠️  Migration count mismatch!")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def main():
    """Main migration function with command-line interface"""
    
    # Default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_tinydb = os.path.join(script_dir, "agent_hub_nosql.json")
    default_sqlite = os.path.join(script_dir, "agent_hub.db")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        tinydb_file = sys.argv[1]
    else:
        tinydb_file = default_tinydb
    
    if len(sys.argv) > 2:
        sqlite_db = sys.argv[2]
    else:
        sqlite_db = default_sqlite
    
    print("🔄 TinyDB to SQLite Migration Tool")
    print("=" * 40)
    print(f"Source (TinyDB): {tinydb_file}")
    print(f"Target (SQLite): {sqlite_db}")
    print("=" * 40)
    
    # Confirm migration
    if os.path.exists(sqlite_db):
        confirm = input(f"⚠️  SQLite database already exists. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Perform migration
    success = migrate_tinydb_to_sqlite(tinydb_file, sqlite_db)
    
    if success:
        print(f"\n🎉 Migration completed! You can now:")
        print(f"   • Delete the old TinyDB file: {tinydb_file}")
        print(f"   • Use the new SQLite database: {sqlite_db}")
        sys.exit(0)
    else:
        print(f"\n💥 Migration failed! Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()