import requests
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_url = "https://graph.facebook.com/v16.0"  # Update to latest version
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        
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
        
    async def send_message(self, phone_number: str, message: str) -> bool:
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