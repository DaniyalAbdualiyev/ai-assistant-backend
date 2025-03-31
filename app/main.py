from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.database import Base, engine
from app.routers import users, auth, assistants, messages, payments

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
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(assistants.router, prefix="/assistants", tags=["Assistants"])
app.include_router(messages.router, prefix="/messages", tags=["Messages"])
app.include_router(payments.router, prefix="/payments")  # The tags are already defined in the router