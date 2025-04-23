import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL") or os.getenv("DATABASE_URL_RENDER")

if not DATABASE_URL:
    raise ValueError("No database URL found. Please set DATABASE_URL environment variable.")

def run_migration():
    """Add duration and duration_months columns to subscription_plans table if they don't exist"""
    logger.info("Starting migration to add duration columns to subscription_plans table")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check if the columns already exist
            result = connection.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'subscription_plans' AND column_name IN ('duration', 'duration_months')"
            ))
            existing_columns = [row[0] for row in result]
            
            # Begin transaction
            trans = connection.begin()
            
            try:
                # Add duration column if it doesn't exist
                if 'duration' not in existing_columns:
                    logger.info("Adding duration column to subscription_plans table")
                    connection.execute(text(
                        "ALTER TABLE subscription_plans "
                        "ADD COLUMN duration VARCHAR(10) NOT NULL DEFAULT 'monthly'"
                    ))
                    logger.info("Successfully added duration column")
                else:
                    logger.info("duration column already exists")
                
                # Add duration_months column if it doesn't exist
                if 'duration_months' not in existing_columns:
                    logger.info("Adding duration_months column to subscription_plans table")
                    connection.execute(text(
                        "ALTER TABLE subscription_plans "
                        "ADD COLUMN duration_months INTEGER NOT NULL DEFAULT 1"
                    ))
                    logger.info("Successfully added duration_months column")
                else:
                    logger.info("duration_months column already exists")
                
                # Commit transaction
                trans.commit()
                logger.info("Migration completed successfully")
                
            except Exception as e:
                # Rollback transaction on error
                trans.rollback()
                logger.error(f"Error during migration: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
