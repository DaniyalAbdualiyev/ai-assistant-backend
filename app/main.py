from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.database import Base, engine
from app.routers.users import router as user_router
from app.routers.auth import router as auth_router
from app.routers.assistants import router as assistants_router
from app.routers.messages import router as messages_router


# Initialize HTTP Bearer scheme
security_scheme = HTTPBearer()

app = FastAPI(
    title="AI Assistant API",
    description="API for AI Assistant application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (you can specify your frontend URL)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Create database tables
Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(assistants_router, prefix="/assistants", tags=["Assistants"])
app.include_router(messages_router, prefix="/messages", tags=["Messages"]) 