from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.auth.jwt import verify_password
from app.database import SessionLocal
from app.models.user import User
from jose import jwt, JWTError
from app.auth.jwt import SECRET_KEY, ALGORITHM, create_access_token
import os
from datetime import timedelta

class AdminAuth(AuthenticationBackend):
    """
    Authentication backend for SQLAdmin that uses the existing User model
    and only allows admin users to access the admin panel.
    """
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")  # SQLAdmin uses "username" field in login form
        password = form.get("password")
        
        if not email or not password:
            return False
            
        # Verify user credentials
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False
                
            # Check if password is correct
            if not verify_password(password, user.password_hash):
                return False
                
            # Check if user is an admin
            if not user.is_admin:
                return False
                
            # Create JWT token for admin session
            access_token_expires = timedelta(hours=8)  # Longer session for admin
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            # Set token in session
            request.session["admin_token"] = access_token
            return True
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        # Clear admin token from session
        request.session.pop("admin_token", None)
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("admin_token")
        if not token:
            return False
            
        # Verify token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if not email:
                return False
                
            # Verify user is still an admin
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()
                if not user or not user.is_admin:
                    return False
                return True
            finally:
                db.close()
        except JWTError:
            return False
