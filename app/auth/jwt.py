from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get JWT configs with fallback values
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "54e27b1d9448f232ea0569ae84109e878d9f266d0f24923902cdcf2316c747fa")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Log JWT configuration status
if not os.getenv("JWT_SECRET_KEY"):
    logger.warning("JWT_SECRET_KEY environment variable not set, using default value")
if not os.getenv("ALGORITHM"):
    logger.warning("ALGORITHM environment variable not set, using default value")
if not os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"):
    logger.warning("ACCESS_TOKEN_EXPIRE_MINUTES environment variable not set, using default value")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a password before storing it in the database."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Verifies if a password matches its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
