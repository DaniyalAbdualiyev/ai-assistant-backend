import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Set up log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Define log filenames with timestamps for different components
current_date = datetime.now().strftime("%Y-%m-%d")
GENERAL_LOG_FILE = os.path.join(LOG_DIR, f"app-{current_date}.log")
KNOWLEDGE_BASE_LOG_FILE = os.path.join(LOG_DIR, f"knowledge-base-{current_date}.log")
CHAT_LOG_FILE = os.path.join(LOG_DIR, f"chat-{current_date}.log")

# Configure general logger
def configure_logging():
    # Clear any existing handlers
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Set default level for root logger
    root_logger.setLevel(logging.INFO)
    
    # Create console handler with INFO level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # Create file handler for general logs
    file_handler = RotatingFileHandler(
        GENERAL_LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_knowledge_base_logger()
    configure_chat_logger()
    
    return root_logger

# Configure knowledge base specific logger
def configure_knowledge_base_logger():
    knowledge_logger = logging.getLogger('app.services.vector_store')
    knowledge_logger.setLevel(logging.DEBUG)
    
    file_handler = RotatingFileHandler(
        KNOWLEDGE_BASE_LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    knowledge_logger.addHandler(file_handler)
    
    # Add file processor logs to knowledge base log file
    file_processor_logger = logging.getLogger('app.services.file_processor')
    file_processor_logger.setLevel(logging.DEBUG)
    file_processor_logger.addHandler(file_handler)
    
    return knowledge_logger

# Configure chat specific logger
def configure_chat_logger():
    chat_logger = logging.getLogger('app.routers.messages')
    chat_logger.setLevel(logging.DEBUG)
    
    file_handler = RotatingFileHandler(
        CHAT_LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    chat_logger.addHandler(file_handler)
    
    # Also add web_chat logs to the chat log file
    web_chat_logger = logging.getLogger('app.routers.web_chat')
    web_chat_logger.setLevel(logging.DEBUG)
    web_chat_logger.addHandler(file_handler)
    
    return chat_logger 