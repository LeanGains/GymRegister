"""
Migration script to add metadata column to existing assets table
Run this when upgrading from older versions without the metadata field
"""

from sqlalchemy import create_engine, text, inspect
from api.config import settings
import logging

logger = logging.getLogger(__name__)

def migrate_add_metadata_column():
    """Add metadata column to assets table if it doesn't exist"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as connection:
            # Check if metadata column already exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('assets')]
            
            if 'metadata' not in columns:
                logger.info("Adding metadata column to assets table...")
                
                # Add the metadata column
                if 'sqlite' in settings.database_url:
                    # SQLite syntax
                    connection.execute(text(
                        "ALTER TABLE assets ADD COLUMN metadata TEXT"
                    ))
                else:
                    # PostgreSQL/MySQL syntax
                    connection.execute(text(
                        "ALTER TABLE assets ADD COLUMN metadata JSON"
                    ))
                
                connection.commit()
                logger.info("Successfully added metadata column to assets table")
            else:
                logger.info("Metadata column already exists in assets table")
                
    except Exception as e:
        logger.error(f"Failed to add metadata column: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_add_metadata_column()