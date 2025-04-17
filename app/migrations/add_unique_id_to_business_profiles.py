"""
Migration script to add unique_id field to business_profiles table.
"""
import uuid
from sqlalchemy import Column, String
from app.database import engine, Base, SessionLocal
from app.models.business_profile import BusinessProfile

def run_migration():
    """
    Run the migration to add unique_id field to business_profiles table.
    """
    # Create a connection to the database
    conn = engine.connect()
    
    try:
        # Add the unique_id column if it doesn't exist
        conn.execute('ALTER TABLE business_profiles ADD COLUMN IF NOT EXISTS unique_id VARCHAR(255) UNIQUE;')
        
        # Update existing rows with a UUID if unique_id is NULL
        db = SessionLocal()
        try:
            # Get all business profiles without a unique_id
            profiles = db.query(BusinessProfile).filter(BusinessProfile.unique_id.is_(None)).all()
            
            # Update each profile with a new UUID
            for profile in profiles:
                profile.unique_id = str(uuid.uuid4())
            
            # Commit the changes
            db.commit()
            
            # Make the column not nullable after all rows have been updated
            conn.execute('ALTER TABLE business_profiles ALTER COLUMN unique_id SET NOT NULL;')
            
            print(f"Migration completed successfully. Updated {len(profiles)} business profiles.")
            
        except Exception as e:
            db.rollback()
            print(f"Error updating business profiles: {str(e)}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
