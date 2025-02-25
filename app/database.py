import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # Load envronment variables from .env file

# Determine if running locally or in Render
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
DATABASE_URL = (
    os.getenv("DATABASE_URL_LOCAL") if ENVIRONMENT == "local" else os.getenv("DATABASE_URL_RENDER")
)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
