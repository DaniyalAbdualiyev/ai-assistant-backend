import requests
import os
import logging
from typing import Dict, Optional
from app.core.config import settings
import hmac
import hashlib

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_url = "https://graph.facebook.com/v18.0"  # Updated to latest version
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = f"{settings.WHATSAPP_APP_ID}|{settings.WHATSAPP_APP_SECRET}"
        
    async def setup_webhook(self, credentials: Dict):
        """Set up WhatsApp webhook with provided credentials"""
        try:
            # Validate required credentials
            if not credentials.get("access_token"):
                raise ValueError("WhatsApp access token is required")
                
            # In a real implementation, you would configure the webhook with Meta Graph API
            return True
                
        except Exception as e:
            logger.error(f"Failed to set up WhatsApp webhook: {str(e)}")
            raise
        
    async def send_message(self, phone_number: str, message: str, template_name: Optional[str] = None) -> bool:
        """Send a WhatsApp message using the Cloud API"""
        try:
            # Make sure phone number starts with country code and no +
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
                
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            if template_name:
                # Send template message
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": phone_number,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {
                            "code": "en"
                        }
                    }
                }
            else:
                # Send regular text message
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": phone_number,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": message
                    }
                }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False
            
    def verify_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify the webhook signature
        """
        try:
            expected_signature = hmac.new(
                self.access_token.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(
                f"sha256={expected_signature}",
                signature
            )
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False
            
    async def get_business_profile(self) -> Dict:
        """
        Get the WhatsApp business profile
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/whatsapp_business_profile"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get business profile: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting business profile: {str(e)}")
            return {} 