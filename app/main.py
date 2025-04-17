from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.database import Base, engine
from app.routers import users, auth, assistants, messages, payments, webhook
from app.routers.web_chat import router as web_chat

import os
from dotenv import load_dotenv

load_dotenv()

# Initialize HTTP Bearer scheme
security_scheme = HTTPBearer()

app = FastAPI(
    title="AI Assistant API",
    description="API for AI Assistant application",
    version="1.0.0"
)

# Get allowed origins from environment variable or use default
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the origins from environment variable
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Create database tables
Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(auth, prefix="/auth", tags=["Auth"])
app.include_router(users, prefix="/users", tags=["Users"])
app.include_router(assistants, prefix="/assistants", tags=["Assistants"])
app.include_router(messages, prefix="/messages", tags=["Messages"])
app.include_router(payments, prefix="/payments")  # The tags are already defined in the router

app.include_router(webhook, tags=["Webhooks"])
app.include_router(web_chat, prefix="/web-chat", tags=["Web Chat"])