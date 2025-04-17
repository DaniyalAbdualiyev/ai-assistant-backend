"""
Migration script to remove Instagram integrations from the database.
"""
from sqlalchemy import create_engine, text
from app.database import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to remove Instagram integrations from the database.
    """
    # Create a connection to the database
    conn = engine.connect()
    
    try:
        # Delete all Instagram integrations
        result = conn.execute(text("""
            DELETE FROM integrations 
            WHERE platform = 'instagram';
        """))
        conn.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Successfully removed {deleted_count} Instagram integrations from the database.")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
