import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# First try to get the Render-specific database URL, then fall back to regular DATABASE_URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL_RENDER") or os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("No database URL found. Please set DATABASE_URL or DATABASE_URL_RENDER environment variable.")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
