"""
Migration script to clean up any remaining integration references in the database.
"""
from sqlalchemy import create_engine, text
from app.database import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to clean up any remaining integration references.
    """
    # Create a connection to the database
    conn = engine.connect()
    
    try:
        # Check if there are any foreign key constraints related to integrations
        # This is a safer approach than trying to drop constraints directly
        # as it will only attempt to modify tables that actually exist
        
        # List all tables in the database
        tables_result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        
        tables = [row[0] for row in tables_result]
        logger.info(f"Found {len(tables)} tables in the database")
        
        # For each table, check for columns that might reference integrations
        for table in tables:
            # Check for columns with 'integration' in the name
            columns_result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name LIKE '%integration%'
            """))
            
            integration_columns = [row[0] for row in columns_result]
            
            if integration_columns:
                logger.info(f"Found integration-related columns in table {table}: {integration_columns}")
                
                # For each column, set it to NULL (if nullable) or remove the constraint
                for column in integration_columns:
                    try:
                        # Try to set the column to NULL
                        conn.execute(text(f"""
                            UPDATE {table} 
                            SET {column} = NULL 
                            WHERE {column} IS NOT NULL
                        """))
                        conn.commit()
                        logger.info(f"Set {column} to NULL in table {table}")
                    except Exception as e:
                        logger.warning(f"Could not set {column} to NULL in table {table}: {str(e)}")
        
        logger.info("Successfully cleaned up integration references")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
