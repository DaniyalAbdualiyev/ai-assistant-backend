"""
Migration script to remove the WhatsApp integration table.
"""
from sqlalchemy import create_engine, text
from app.database import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to remove the WhatsApp integrations table.
    """
    # Create a connection to the database
    conn = engine.connect()
    
    try:
        # Check if the table exists before attempting to drop it
        check_table = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'whatsapp_integrations'
            );
        """))
        
        table_exists = check_table.scalar()
        
        if table_exists:
            # Drop the WhatsApp integrations table
            conn.execute(text("DROP TABLE IF EXISTS whatsapp_integrations;"))
            conn.commit()
            logger.info("Successfully dropped the WhatsApp integrations table.")
        else:
            logger.info("WhatsApp integrations table does not exist, no action needed.")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
