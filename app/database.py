import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Use the database URL from the environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")  or os.getenv("DATABASE_URL_LOCAL") or os.getenv("DATABASE_URL_RENDER")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("No database URL found. Please set DATABASE_URL environment variable.")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


