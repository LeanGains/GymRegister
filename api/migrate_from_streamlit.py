#!/usr/bin/env python3
"""
Migration script to move data from Streamlit SQLite database to new FastAPI database structure.

This script:
1. Connects to the old Streamlit database (gym_assets.db)
2. Reads existing assets and audit_log data
3. Migrates data to new FastAPI database structure
4. Preserves all existing data while adding new fields
5. Creates backup of original database

Usage:
    python -m api.migrate_from_streamlit
"""

import sqlite3
import shutil
import os
from datetime import datetime
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import Base, Asset, AuditLog
import uuid

def backup_original_database(db_path: str) -> str:
    """Create backup of original database"""
    if not os.path.exists(db_path):
        print(f"Original database not found at {db_path}")
        return ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return ""

def connect_old_database(db_path: str):
    """Connect to old Streamlit database"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Old database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def migrate_assets(old_conn, new_session: Session) -> int:
    """Migrate assets from old to new database"""
    print("🔄 Migrating assets...")
    
    # Get old assets
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM assets")
    old_assets = cursor.fetchall()
    
    migrated_count = 0
    skipped_count = 0
    
    for old_asset in old_assets:
        try:
            # Check if asset already exists in new database
            existing = new_session.query(Asset).filter(Asset.asset_tag == old_asset['asset_tag']).first()
            if existing:
                print(f"   ⚠️  Asset {old_asset['asset_tag']} already exists, skipping")
                skipped_count += 1
                continue
            
            # Create new asset with migrated data
            new_asset = Asset(
                id=str(uuid.uuid4()),  # New UUID field
                asset_tag=old_asset['asset_tag'],
                name=None,  # New field, will be filled later if needed
                item_type=old_asset['item_type'],
                description=old_asset['description'],
                location=old_asset['location'],
                status=old_asset['status'] or 'Active',
                condition=old_asset['condition'] or 'Good',
                weight=old_asset['weight'],
                last_seen=datetime.fromisoformat(old_asset['last_seen']) if old_asset['last_seen'] else datetime.utcnow(),
                created_at=datetime.utcnow(),  # New field
                updated_at=datetime.utcnow(),  # New field
                notes=old_asset['notes'],
                metadata=None  # New field for additional data
            )
            
            new_session.add(new_asset)
            migrated_count += 1
            print(f"   ✅ Migrated asset: {old_asset['asset_tag']}")
            
        except Exception as e:
            print(f"   ❌ Failed to migrate asset {old_asset['asset_tag']}: {e}")
    
    new_session.commit()
    print(f"✅ Assets migration complete: {migrated_count} migrated, {skipped_count} skipped")
    return migrated_count

def migrate_audit_logs(old_conn, new_session: Session) -> int:
    """Migrate audit logs from old to new database"""
    print("🔄 Migrating audit logs...")
    
    # Check if audit_log table exists in old database
    cursor = old_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
    if not cursor.fetchone():
        print("   ⚠️  No audit_log table found in old database, skipping")
        return 0
    
    # Get old audit logs
    cursor.execute("SELECT * FROM audit_log")
    old_logs = cursor.fetchall()
    
    migrated_count = 0
    
    for old_log in old_logs:
        try:
            # Create new audit log
            new_log = AuditLog(
                id=str(uuid.uuid4()),  # New UUID field
                action=old_log['action'],
                resource_type='asset',  # New field - assume asset for old logs
                resource_id=None,  # New field - would need to map asset_tag to ID
                actor='migrated_user',  # New field
                endpoint=None,  # New field - not available in old logs
                payload={'legacy_notes': old_log['notes']} if old_log.get('notes') else None,  # New field
                timestamp=datetime.fromisoformat(old_log['timestamp']) if old_log['timestamp'] else datetime.utcnow(),
                ip_address=None,  # New field - not available
                user_agent=None  # New field - not available
            )
            
            new_session.add(new_log)
            migrated_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to migrate audit log: {e}")
    
    new_session.commit()
    print(f"✅ Audit logs migration complete: {migrated_count} migrated")
    return migrated_count

def verify_migration(new_session: Session) -> dict:
    """Verify migration results"""
    print("🔍 Verifying migration...")
    
    # Count new records
    asset_count = new_session.query(Asset).count()
    audit_count = new_session.query(AuditLog).count()
    
    # Sample some records
    sample_assets = new_session.query(Asset).limit(3).all()
    sample_audits = new_session.query(AuditLog).limit(3).all()
    
    results = {
        'asset_count': asset_count,
        'audit_count': audit_count,
        'sample_assets': [asset.asset_tag for asset in sample_assets],
        'sample_audits': [log.action for log in sample_audits]
    }
    
    print(f"✅ Migration verification complete:")
    print(f"   - Assets: {asset_count}")
    print(f"   - Audit logs: {audit_count}")
    print(f"   - Sample assets: {', '.join(results['sample_assets'])}")
    
    return results

def main():
    """Main migration function"""
    print("🚀 Starting migration from Streamlit to FastAPI database...")
    print("=" * 60)
    
    # Configuration
    old_db_path = "gym_assets.db"  # Old Streamlit database
    
    try:
        # Step 1: Create backup
        backup_path = backup_original_database(old_db_path)
        
        # Step 2: Create new database tables
        print("🔄 Creating new database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ New database tables created")
        
        # Step 3: Connect to databases
        print("🔄 Connecting to databases...")
        old_conn = connect_old_database(old_db_path)
        new_session = SessionLocal()
        
        try:
            # Step 4: Migrate data
            asset_count = migrate_assets(old_conn, new_session)
            audit_count = migrate_audit_logs(old_conn, new_session)
            
            # Step 5: Verify migration
            results = verify_migration(new_session)
            
            print("=" * 60)
            print("🎉 Migration completed successfully!")
            print(f"   - Backup created: {backup_path}")
            print(f"   - Assets migrated: {asset_count}")
            print(f"   - Audit logs migrated: {audit_count}")
            print(f"   - Total assets in new DB: {results['asset_count']}")
            print(f"   - Total audit logs in new DB: {results['audit_count']}")
            print("")
            print("Next steps:")
            print("1. Test the new FastAPI application")
            print("2. Verify all data is accessible via API endpoints")
            print("3. Update frontend to use new API endpoints")
            print("4. Archive or remove old Streamlit app when ready")
            
        finally:
            old_conn.close()
            new_session.close()
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("Check the error above and ensure:")
        print("1. Old database file exists")
        print("2. New database is accessible")
        print("3. No permission issues")
        raise

if __name__ == "__main__":
    main()