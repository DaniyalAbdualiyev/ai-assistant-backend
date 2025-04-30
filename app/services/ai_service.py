Peakperformer, [4/30/2025 8:11 AM]
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from app.models.message import Message
import os
from dotenv import load_dotenv
import json
from fastapi import APIRouter
from typing import Dict, List
from datetime import datetime

load_dotenv()

# Add this function to determine temperature based on business type
def get_business_temperature(business_type: str) -> float:
    """
    Return appropriate temperature for each business type.
    - Higher temperature (0.7-0.9): More creative, varied responses
    - Medium temperature (0.5-0.7): Balanced responses
    - Lower temperature (0.2-0.4): More deterministic, precise responses
    """
    temperature_mapping = {
        "selling": 0.8,        # More creative, varied for sales pitches
        "consulting": 0.6,     # Balanced approach for consulting
        "tech_support": 0.3,   # More precise, deterministic for technical information
        "customer_service": 0.5,  # Middle ground for customer service
        "healthcare": 0.4,     # More precise but still conversational
        "legal": 0.2,          # Highly precise for legal advice
        "creative": 0.9,       # Very creative for content generation
        "educational": 0.5     # Balanced for educational content
    }
    return temperature_mapping.get(business_type, 0.7)  # Default to 0.7 if type not found

class ContextManager:
    def init(self, db_session=None):
        self.db = db_session
        self.max_context_messages = 10
    
    async def get_conversation_context(self, assistant_id: int) -> list:
        """Get recent messages from database"""
        if not self.db:
            return []
            
        chat_history = self.db.query(Message).filter(
            Message.assistant_id == assistant_id
        ).order_by(Message.timestamp.desc()).limit(self.max_context_messages).all()
        
        # Return messages in reverse chronological order (newest first)
        return chat_history

Peakperformer, [4/30/2025 8:11 AM]
class PromptEngine:
    def create_prompt(self, query: str, config: dict, context: str = "") -> str:
        """Create optimized prompt based on business type and configuration"""
        business_type = config.get('business_type', 'selling')
        language = config.get('language', 'en')
        
        # Language instruction mapping
        language_instructions = {
            "en": "Respond in English.",
            "ru": "Отвечайте на русском языке.",
            "es": "Responda en español.",
            "fr": "Répondez en français.",
            "de": "Antworten Sie auf Deutsch.",
            "zh": "用中文回答。",
            "ja": "日本語で回答してください。",
            "ar": "الرجاء الرد باللغة العربية.",
            "hi": "कृपया हिंदी में जवाब दें।",
            "pt": "Responda em português."
            # Add more languages as needed
        }
        
        # Get specific language instruction or default to a general format
        language_instruction = language_instructions.get(
            language, 
            f"Respond in {language} language only. Do not use English unless specifically asked."
        )
        
        type_instructions = {
            "selling": """
                You are a sales assistant. Your responses MUST include information about:
                - Products
                - Prices
                - Availability
                Focus on product features, pricing, and availability.
                Always mention at least one specific product or price point.
            """,
            "consulting": """
                You are a professional consultant. Your responses MUST include:
                - Scheduling/appointment options
                - Consultation process
                - Professional advice
                Always mention scheduling or consultation possibilities.
            """,
            "tech_support": """
                You are a technical support specialist. Your responses MUST include:
                - Troubleshooting steps
                - Support options
                - Help/assistance terminology
                Always provide specific troubleshooting steps or support options.
            """
        }

        prompt = f"""
        Context: {context}
        Business Type: {business_type}
        
        IMPORTANT INSTRUCTIONS:
        {type_instructions.get(business_type, '')}
        
        LANGUAGE INSTRUCTION: {language_instruction}
        You MUST respond ONLY in {language} language. This is mandatory.
        
        User Query: {query}
        
        Remember to:
        1. Stay in character as a {business_type} specialist
        2. Include required keywords and information
        3. Be specific and actionable
        4. Respond ONLY in {language} language
        """

        # Add tone modifications
        if config.get('tone') == 'expert':
            prompt += "\nProvide a detailed, professional explanation using industry terminology."
        elif config.get('tone') == 'simple':
            prompt += "\nExplain in simple, easy-to-understand terms."

        return prompt

Peakperformer, [4/30/2025 8:11 AM]
class ResponseGenerator:
    def init(self, model: ChatOpenAI, api_key: str = None):
        self.model = model
        # Store API key directly or get from environment if not provided
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    async def generate_response(self, prompt: str, temperature: float = None) -> str:
        """Generate response with optional temperature override."""
        try:
            # If temperature is specified, create a new model with that temperature
            if temperature is not None:
                temp_model = ChatOpenAI(
                    api_key=self.api_key,
                    temperature=temperature
                )
                response = await temp_model.ainvoke(prompt)
            else:
                # Use the default model
                response = await self.model.ainvoke(prompt)
                
            return response.content
        except Exception as e:
            return f"I apologize, but I'm having trouble generating a response. {str(e)}"

class ResponseOptimizer:
    def optimize_sales_response(self, original_response: str) -> str:
        """Make responses more likely to lead to sales"""
        
        # Add call-to-action
        if "price" in original_response.lower():
            original_response += "\nWould you like to proceed with the purchase? I can help you place an order right now."
            
        # Add urgency when mentioning products
        if "product" in original_response.lower():
            original_response = original_response.replace(
                "available",
                "available now with special pricing"
            )
            
        # Add social proof
        if "interested" in original_response.lower():
            original_response += "\nMany customers have found this option perfect for their needs."
            
        return original_response

    def optimize_consulting_response(self, original_response: str) -> str:
        """Make responses more likely to lead to consultations"""
        
        # Add appointment suggestion
        if "help" in original_response.lower():
            original_response += "\nWould you like to schedule a free consultation to discuss this in detail?"
            
        # Add expertise proof
        if "advice" in original_response.lower():
            original_response += "\nOur experts have helped over 100 clients with similar situations."
            
        return original_response

class AIService:
    def init(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(api_key=self.api_key, temperature=0.7)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vector_store = None
        self.conversations = {}  # Store by assistant_id
        self.context_manager = ContextManager()
        self.prompt_engine = PromptEngine()
        # Pass API key to ResponseGenerator
        self.response_generator = ResponseGenerator(self.model, self.api_key)
        self.response_optimizer = ResponseOptimizer()

    def initialize_knowledge_base(self, documents):
        """Initialize vector store with documents"""
        doc_objects = [Document(page_content=doc, metadata={}) for doc in documents]
        self.vector_store = Chroma(embedding_function=self.embeddings)
        self.vector_store.add_documents(documents=doc_objects)

Peakperformer, [4/30/2025 8:11 AM]
async def get_response(self, query, config, assistant_id, user_id):
        try:
            # Get business type
            business_type = config.get('business_type', 'selling')
            
            # Get appropriate temperature for this business type
            # Use config temperature if provided, otherwise get from business type mapping
            temperature = config.get('temperature', get_business_temperature(business_type))
            
            # Get vector store context if available
            context = ""
            if self.vector_store:
                results = self.vector_store.similarity_search(query, k=2)
                context = "\n".join([doc.page_content[:2000] for doc in results])

            # Create optimized prompt
            prompt = self.prompt_engine.create_prompt(
                query=query,
                config=config,
                context=context
            )

            # Generate response with business-specific temperature
            response = await self.response_generator.generate_response(prompt, temperature)

            # Optimize based on business type
            if config['business_type'] == 'selling':
                response = self.response_optimizer.optimize_sales_response(response)
            elif config['business_type'] == 'consulting':
                response = self.response_optimizer.optimize_consulting_response(response)

            # Store in conversation history
            conversation_key = f"{assistant_id}_{user_id}"
            if conversation_key not in self.conversations:
                self.conversations[conversation_key] = []
            self.conversations[conversation_key].append(
                {"role": "user", "content": query}
            )
            self.conversations[conversation_key].append(
                {"role": "assistant", "content": response}
            )
            
            return response

        except Exception as e:
            return f"I apologize, but I'm having trouble processing your request. {str(e)}"

    async def detect_intent(self, query):
        """Detect user intent from query"""
        prompt = f"""
        Classify the user intent for: "{query}"
        Possible intents:
        - product_inquiry
        - pricing_question
        - support_request
        - complaint
        - general_information
        Response format: {{"intent": "category_name", "confidence": 0.0 to 1.0}}
        """
        response = await self.model.ainvoke(prompt)
        return json.loads(response.content)

    async def generate_suggestions(self, conversation_history):
        """Generate proactive suggestions based on conversation"""
        # Analyze conversation
        # Identify potential next steps
        # Generate relevant suggestions

    async def process_image_with_text(self, image_url, text_query):
        """Process queries with both image and text"""
        # Download image
        # Extract image features
        # Combine with text query
        # Generate response

class MessageProcessor:
    def init(self, ai_service: AIService):
        self.ai_service = ai_service

    async def process_message(self, message: str, platform: str, assistant_id: int, user_id: int) -> dict:
        """Process and format messages for different platforms"""
        # Get base response from AI service
        # Note: We're not changing the default config here to maintain backward compatibility
        # but the AIService will use the appropriate temperature for the business type
        response = await self.ai_service.get_response(
            query=message,
            config={"business_type": "selling", "language": "en"},
            assistant_id=assistant_id,
            user_id=user_id
        )

Peakperformer, [4/30/2025 8:11 AM]
# Format response based on platform
        if platform == "instagram":
            # Instagram has a 2000 character limit
            response = response[:1997] + "..." if len(response) > 2000 else response
            return {"text": response, "platform": "instagram"}
        
        elif platform == "whatsapp":
            # WhatsApp formatting
            return {"text": response, "platform": "whatsapp"}
        
        # Default formatting
        return {"text": response, "platform": "default"}

class ResponseFormatter:
    @staticmethod
    def format_for_instagram(response_text, **kwargs):
        """Format AI response for Instagram"""
        # Instagram has 2000 character limit
        if len(response_text) > 1950:
            response_text = response_text[:1950] + "..."
            
        # Add call-to-action buttons if needed
        buttons = kwargs.get('buttons', [])
        
        return {
            "text": response_text,
            "buttons": buttons
        }
    
    @staticmethod
    def format_for_whatsapp(response_text, **kwargs):
        """Format AI response for WhatsApp"""
        # Similar formatting but with WhatsApp-specific features

router = APIRouter()

@router.post("/webhooks/instagram")
async def instagram_webhook(data: dict):
    """Handle Instagram webhook events"""
    # Extract message content
    # Identify assistant and user
    # Process message
    # Return response
    
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(data: dict):
    """Handle WhatsApp webhook events"""
    # Similar handling for WhatsApp

def get_default_temperature(business_type: str) -> float:
    """Get default temperature based on business type"""
    default_temperatures = {
        "selling": 0.8,       # More creative for sales
        "consulting": 0.6,    # Balanced for consulting
        "tech_support": 0.3,  # More focused for technical support
        "customer_service": 0.5,  # Balanced for service
        "legal": 0.2,         # More precise for legal
        "healthcare": 0.4     # Careful but still conversational for healthcare
    }
    return default_temperatures.get(business_type, 0.7)  # Default to 0.7