from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.database import Base, engine
from app.routers.users import router as user_router
from app.routers.auth import router as auth_router

# Initialize HTTP Bearer scheme
security_scheme = HTTPBearer()

app = FastAPI(
    title="AI Assistant API",
    description="API for AI Assistant application",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
