from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from app.models.message import Message
import os
from dotenv import load_dotenv
import json

from typing import Dict, List
from datetime import datetime

load_dotenv()

class ContextManager:
    def __init__(self, db_session=None):
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

class PromptEngine:
    def create_prompt(self, query: str, config: dict, context: str = "") -> str:
        """Create optimized prompt based on business type and configuration"""
        business_type = config.get('business_type', 'selling')
        
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
        Language: {config.get('language', 'en')}
        
        User Query: {query}
        
        Remember to:
        1. Stay in character as a {business_type} specialist
        2. Include required keywords and information
        3. Be specific and actionable
        """

        # Add tone modifications
        if config.get('tone') == 'expert':
            prompt += "\nProvide a detailed, professional explanation using industry terminology."
        elif config.get('tone') == 'simple':
            prompt += "\nExplain in simple, easy-to-understand terms."

        return prompt

class ResponseGenerator:
    def __init__(self, model: ChatOpenAI):
        self.model = model
    
    async def generate_response(self, prompt: str) -> str:
        try:
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
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(api_key=self.api_key)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vector_store = None
        self.conversations = {}  # Store by assistant_id
        self.context_manager = ContextManager()
        self.prompt_engine = PromptEngine()
        self.response_generator = ResponseGenerator(self.model)
        self.response_optimizer = ResponseOptimizer()

    def initialize_knowledge_base(self, documents):
        """Initialize vector store with documents"""
        doc_objects = [Document(page_content=doc, metadata={}) for doc in documents]
        self.vector_store = Chroma(embedding_function=self.embeddings)
        self.vector_store.add_documents(documents=doc_objects)

    async def get_response(self, query, config, assistant_id, user_id):
        try:
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

            # Generate response
            response = await self.response_generator.generate_response(prompt)

            # Optimize based on business type
            if config['business_type'] == 'selling':
                response = self.response_optimizer.optimize_sales_response(response)
            elif config['business_type'] == 'consulting':
                response = self.response_optimizer.optimize_consulting_response(response)

            # Store in conversation history (keeping your existing logic)
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
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def process_message(self, message: str, platform: str, assistant_id: int, user_id: int) -> dict:
        """Process and format messages for different platforms"""
        # Get base response from AI service
        response = await self.ai_service.get_response(
            query=message,
            config={"business_type": "selling", "language": "en"},  # Default config
            assistant_id=assistant_id,
            user_id=user_id
        )

        # Format response based on platform
        # Web-based chat formatting
        return {"text": response, "platform": "web"}

class ResponseFormatter:
    @staticmethod
    def format_for_web(response_text, **kwargs):
        """Format AI response for web-based chat"""
        # Add any web-specific formatting here
        buttons = kwargs.get('buttons', [])
        
        return {
            "text": response_text,
            "buttons": buttons
        }