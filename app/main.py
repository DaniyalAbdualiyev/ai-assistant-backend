from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware
from app.database import Base, engine
from app.routers import users, auth, assistants, messages, payments, webhook
from app.routers.web_chat import router as web_chat
from app.routers.analytics import router as analytics
from app.admin import setup_admin
from app.admin.auth import AdminAuth

import os
from dotenv import load_dotenv

load_dotenv()

security_scheme = HTTPBearer()

app = FastAPI(
    title="AI Assistant API",
    description="API for AI Assistant application",
    version="1.0.0"
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))

# Configure CORS settings
env = os.getenv("ENVIRONMENT", "local")
if env == "production":
    # In production, only allow specific origins
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    origins = [origin.strip() for origin in allowed_origins if origin.strip()]
else:
    # In development/local environment, be more permissive
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth, prefix="/auth", tags=["Auth"])
app.include_router(users, prefix="/users", tags=["Users"])
app.include_router(assistants, prefix="/assistants", tags=["Assistants"])
app.include_router(messages, prefix="/messages", tags=["Messages"])
app.include_router(payments, prefix="/payments")
app.include_router(webhook, tags=["Webhooks"])
app.include_router(web_chat, prefix="/web-chat", tags=["Web Chat"])
app.include_router(analytics)

admin = setup_admin(app)
admin.authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY", "your-secret-key"))