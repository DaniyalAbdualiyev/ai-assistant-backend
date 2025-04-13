import requests
import os
import logging
import json
import time
from typing import Dict, Optional, List, Union
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, phone_number_id=None, access_token=None):
        """Initialize WhatsApp service with credentials
        
        Args:
            phone_number_id: Optional override for phone number ID from env
            access_token: Optional override for access token from env
        """
        self.api_url = "https://graph.facebook.com/v17.0"  # Updated to latest version
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not fully configured")
            
    def get_headers(self) -> Dict:
        """Get API request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
    
    async def setup_webhook(self, credentials: Dict) -> bool:
        """Set up WhatsApp webhook with provided credentials
        
        Args:
            credentials: Dict containing access_token and other required fields
            
        Returns:
            bool: True if setup was successful
            
        Raises:
            ValueError: If required credentials are missing
            Exception: For other errors during setup
        """
        try:
            # Validate required credentials
            if not credentials.get("access_token"):
                raise ValueError("WhatsApp access token is required")
            
            if not credentials.get("phone_number_id"):
                raise ValueError("WhatsApp phone number ID is required")
                
            # Update instance variables with new credentials
            self.access_token = credentials.get("access_token")
            self.phone_number_id = credentials.get("phone_number_id")
            
            # Verify credentials by making a test API call
            url = f"{self.api_url}/{self.phone_number_id}?fields=display_phone_number,quality_score"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                logger.info(f"WhatsApp credentials verified successfully")
                return True
            else:
                logger.error(f"Failed to verify WhatsApp credentials: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set up WhatsApp webhook: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def send_message(self, phone_number: str, message: str) -> Dict:
        """Send a text message via WhatsApp
        
        Args:
            phone_number: Recipient's phone number (with country code)
            message: Text message to send
            
        Returns:
            Dict: API response data
            
        Raises:
            Exception: For errors during message sending
        """
        return await self._send_whatsapp_payload(
            phone_number=phone_number,
            message_type="text",
            content={
                "preview_url": True,  # Allow URL previews
                "body": message
            }
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def send_template_message(self, phone_number: str, template_name: str, 
                                   language_code: str = "en_US", 
                                   components: Optional[List[Dict]] = None) -> Dict:
        """Send a template message via WhatsApp
        
        Args:
            phone_number: Recipient's phone number
            template_name: Name of the approved template
            language_code: Language code for the template
            components: Template components (header, body, buttons)
            
        Returns:
            Dict: API response data
        """
        return await self._send_whatsapp_payload(
            phone_number=phone_number,
            message_type="template",
            content={
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": components or []
            }
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def send_image_message(self, phone_number: str, image_url: str, caption: Optional[str] = None) -> Dict:
        """Send an image message via WhatsApp
        
        Args:
            phone_number: Recipient's phone number
            image_url: URL of the image to send
            caption: Optional caption for the image
            
        Returns:
            Dict: API response data
        """
        content = {"link": image_url}
        if caption:
            content["caption"] = caption
            
        return await self._send_whatsapp_payload(
            phone_number=phone_number,
            message_type="image",
            content=content
        )
    
    async def _send_whatsapp_payload(self, phone_number: str, message_type: str, 
                                    content: Dict) -> Dict:
        """Send a WhatsApp message with the specified payload
        
        Args:
            phone_number: Recipient's phone number
            message_type: Type of message (text, template, image, etc.)
            content: Content specific to the message type
            
        Returns:
            Dict: API response data
            
        Raises:
            Exception: For errors during message sending
        """
        try:
            # Normalize phone number format (remove + if present)
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
                
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": message_type,
                message_type: content
            }
            
            logger.info(f"Sending WhatsApp {message_type} message to {phone_number}")
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone_number}")
                return response_data
            else:
                error_msg = f"Failed to send message: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            raise
    
    async def get_business_profile(self) -> Dict:
        """Get the WhatsApp Business Profile information
        
        Returns:
            Dict: Business profile data
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/whatsapp_business_profile"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get business profile: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting WhatsApp business profile: {str(e)}")
            return {}