import os
import logging
import requests
from typing import Dict, Optional
from app.core.config import settings
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.business_profile import BusinessProfile
from app.models.verification_code import VerificationCode
import random
import string
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WhatsAppVerificationService:
    def __init__(self):
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.access_token = f"{settings.WHATSAPP_APP_ID}|{settings.WHATSAPP_APP_SECRET}"
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.rate_limit_minutes = 5
        
    async def verify_phone_number(self, phone_number: str, db: Session) -> str:
        """Start phone number verification process"""
        # Check if number is already verified
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.whatsapp_number == phone_number,
            BusinessProfile.whatsapp_verified == True
        ).first()
        
        if profile:
            raise HTTPException(
                status_code=400,
                detail="Phone number is already verified"
            )
            
        # Check rate limiting
        recent_attempts = db.query(VerificationCode).filter(
            VerificationCode.phone_number == phone_number,
            VerificationCode.created_at > datetime.utcnow() - timedelta(minutes=self.rate_limit_minutes)
        ).count()
        
        if recent_attempts >= self.max_attempts:
            raise HTTPException(
                status_code=429,
                detail=f"Too many verification attempts. Please try again in {self.rate_limit_minutes} minutes."
            )
            
        # Generate verification code
        code = ''.join(random.choices(string.digits, k=self.code_length))
        
        # Store verification code
        verification_code = VerificationCode(
            phone_number=phone_number,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes)
        )
        db.add(verification_code)
        db.commit()
        
        # Send verification code via WhatsApp
        # TODO: Implement actual WhatsApp message sending
        logger.info(f"Verification code for {phone_number}: {code}")
        
        return "Verification code sent successfully"

    async def verify_code(self, phone_number: str, code: str, db: Session) -> bool:
        """Verify the provided code"""
        # Find the most recent verification code
        verification_code = db.query(VerificationCode).filter(
            VerificationCode.phone_number == phone_number,
            VerificationCode.code == code,
            VerificationCode.expires_at > datetime.utcnow(),
            VerificationCode.used == False
        ).order_by(VerificationCode.created_at.desc()).first()
        
        if not verification_code:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired verification code"
            )
            
        # Mark code as used
        verification_code.used = True
        verification_code.used_at = datetime.utcnow()
        db.commit()
        
        # Update business profile
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.whatsapp_number == phone_number
        ).first()
        
        if profile:
            profile.whatsapp_verified = True
            profile.whatsapp_verified_at = datetime.utcnow()
            db.commit()
            
        return True

    async def register_phone_number(self, phone_number: str, business_profile_id: int, db: Session) -> bool:
        """Register a new phone number for verification"""
        # Check if number is already registered
        existing_profile = db.query(BusinessProfile).filter(
            BusinessProfile.whatsapp_number == phone_number
        ).first()
        
        if existing_profile:
            raise HTTPException(
                status_code=400,
                detail="Phone number is already registered"
            )
            
        # Update business profile with phone number
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == business_profile_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Business profile not found"
            )
            
        profile.whatsapp_number = phone_number
        profile.whatsapp_verified = False
        db.commit()
        
        return True

    async def verify_phone_number_api(self, phone_number: str) -> Dict:
        """
        Verify a phone number for WhatsApp Business API
        """
        try:
            # Remove any non-digit characters
            phone_number = ''.join(filter(str.isdigit, phone_number))
            
            # Make sure phone number starts with country code
            if not phone_number.startswith('1'):  # Assuming US numbers for now
                phone_number = '1' + phone_number
                
            url = f"{self.base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": "verify_phone_number",
                    "language": {
                        "code": "en"
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": "123456"  # This would be a generated verification code
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Verification code sent",
                    "data": response.json()
                }
            else:
                logger.error(f"Failed to send verification code: {response.text}")
                return {
                    "status": "error",
                    "message": "Failed to send verification code",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error verifying phone number: {str(e)}")
            raise
            
    async def register_phone_number_api(self, business_profile_id: int, phone_number: str) -> Dict:
        """
        Register a verified phone number with a business profile
        """
        try:
            # In a real implementation, you would:
            # 1. Verify the phone number is not already registered
            # 2. Update the business profile with the phone number
            # 3. Set up webhook for this number
            # 4. Return success status
            
            return {
                "status": "success",
                "message": "Phone number registered successfully",
                "phone_number": phone_number
            }
            
        except Exception as e:
            logger.error(f"Error registering phone number: {str(e)}")
            raise 