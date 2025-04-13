from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

def upgrade():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # Add is_admin column if it doesn't exist
        connection.execute(text("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
        """))
        connection.commit()

if __name__ == "__main__":
    upgrade() 