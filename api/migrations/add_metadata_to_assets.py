"""
Migration script to add metadata column to existing assets table
Run this when upgrading from older versions without the metadata field
"""

from sqlalchemy import create_engine, text, inspect
from api.config import settings
import logging

logger = logging.getLogger(__name__)

def migrate_add_metadata_column():
    """Add asset_metadata column to assets table if it doesn't exist"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as connection:
            # Check if asset_metadata column already exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('assets')]
            
            # Handle migration from old 'metadata' column name to 'asset_metadata'
            if 'metadata' in columns and 'asset_metadata' not in columns:
                logger.info("Migrating metadata column to asset_metadata...")
                
                # Rename metadata column to asset_metadata
                if 'sqlite' in settings.database_url:
                    # SQLite doesn't support column rename directly, need to recreate table
                    # For simplicity, we'll add the new column and copy data
                    connection.execute(text(
                        "ALTER TABLE assets ADD COLUMN asset_metadata TEXT"
                    ))
                    connection.execute(text(
                        "UPDATE assets SET asset_metadata = metadata"
                    ))
                    # Note: In production, you might want to drop the old column
                else:
                    # PostgreSQL/MySQL syntax
                    connection.execute(text(
                        "ALTER TABLE assets RENAME COLUMN metadata TO asset_metadata"
                    ))
                
                connection.commit()
                logger.info("Successfully migrated metadata column to asset_metadata")
                
            elif 'asset_metadata' not in columns:
                logger.info("Adding asset_metadata column to assets table...")
                
                # Add the asset_metadata column
                if 'sqlite' in settings.database_url:
                    # SQLite syntax
                    connection.execute(text(
                        "ALTER TABLE assets ADD COLUMN asset_metadata TEXT"
                    ))
                else:
                    # PostgreSQL/MySQL syntax
                    connection.execute(text(
                        "ALTER TABLE assets ADD COLUMN asset_metadata JSON"
                    ))
                
                connection.commit()
                logger.info("Successfully added asset_metadata column to assets table")
            else:
                logger.info("asset_metadata column already exists in assets table")
                
    except Exception as e:
        logger.error(f"Failed to add/migrate asset_metadata column: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_add_metadata_column()