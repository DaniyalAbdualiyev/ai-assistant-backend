"""
Migration script to remove the integrations table from the database.
"""
from sqlalchemy import create_engine, text
from app.database import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to remove the integrations table from the database.
    """
    # Create a connection to the database
    conn = engine.connect()
    
    try:
        # Check if the table exists before attempting to drop it
        check_table = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'integrations'
            );
        """))
        
        table_exists = check_table.scalar()
        
        if table_exists:
            # Drop the integrations table
            conn.execute(text("DROP TABLE IF EXISTS integrations;"))
            conn.commit()
            logger.info("Successfully dropped the integrations table.")
        else:
            logger.info("Integrations table does not exist, no action needed.")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
