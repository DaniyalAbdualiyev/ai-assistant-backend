from typing import List, Dict
from openai import OpenAI
import os
from pinecone import Pinecone, ServerlessSpec
import uuid
import logging
from dotenv import load_dotenv
from .embedding_service import EmbeddingService

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create or connect to the index
index_name = "business-knowledge-base"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI's text-embedding-ada-002 dimension
        metric='cosine',
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Connect to the index
index = pc.Index(index_name)

def get_index_stats() -> Dict:
    """
    Get statistics about the index including vector counts per namespace
    """
    return EmbeddingService.get_index_stats()

def search_similar_texts(query: str, top_k: int = 5, namespace: str = None) -> List[Dict]:
    """
    Search for similar texts in the knowledge base
    
    Args:
        query: The search query
        top_k: Number of results to return
        namespace: Optional namespace to search in (e.g., business_123)
        
    Returns:
        List of matching documents with their similarity scores
    """
    if namespace:
        logger.info(f"Searching for similar texts in namespace: {namespace}")
    else:
        logger.info("Searching for similar texts without namespace specification")
        
    try:
        results = EmbeddingService.search_similar_texts(query, top_k, namespace=namespace)
        
        # Log the results
        if results:
            logger.info(f"Found {len(results)} similar documents in namespace: {namespace}")
            for i, result in enumerate(results):
                score = getattr(result, 'score', 'N/A')
                text_snippet = result.metadata.get('text', 'No text')[:100] + "..." if len(result.metadata.get('text', '')) > 100 else result.metadata.get('text', 'No text')
                logger.info(f"Match {i+1}: Score: {score}, Text snippet: {text_snippet}")
        else:
            logger.warning(f"No similar documents found in namespace: {namespace} for query: {query[:100]}...")
            
        return results
    except Exception as e:
        logger.error(f"Error searching for similar texts: {str(e)}", exc_info=True)
        raise

def add_to_knowledge_base(texts: List[str], metadata: List[Dict] = None, namespace: str = None):
    """
    Add texts to the knowledge base
    """
    vectors = EmbeddingService.prepare_vectors(texts, metadata)
    EmbeddingService.upsert_to_pinecone(vectors, namespace=namespace)

def store_embeddings(text: str, namespace: str = None) -> str:
    """
    Store a single text's embeddings in the knowledge base
    
    Args:
        text: The text to store in the knowledge base
        namespace: Optional namespace to store the embeddings in (e.g., business_123)
        
    Returns:
        The ID of the stored document
    """
    try:
        text_length = len(text)
        logger.info(f"Generating embeddings for text of length {text_length} characters")
        
        # Truncate the text if it's very long (for logging purposes)
        text_snippet = text[:100] + "..." if len(text) > 100 else text
        logger.debug(f"Text snippet: {text_snippet}")
        
        # Generate embeddings using OpenAI
        logger.info("Calling OpenAI API to generate embeddings")
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        
        # Get the embeddings
        embeddings = response.data[0].embedding
        embedding_dimensions = len(embeddings)
        logger.info(f"Embeddings generated successfully: {embedding_dimensions} dimensions")
        
        # Generate a unique ID for this document
        doc_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {doc_id}")
        
        # Prepare vector
        vector = {
            "id": doc_id,
            "values": embeddings,
            "metadata": {"text": text}
        }
        
        # Store in Pinecone with namespace if provided
        if namespace:
            logger.info(f"Storing embeddings in namespace: {namespace}")
            EmbeddingService.upsert_to_pinecone([vector], namespace=namespace)
        else:
            logger.info("Storing embeddings without namespace")
            EmbeddingService.upsert_to_pinecone([vector])
        
        # Get index stats after upsert
        stats = EmbeddingService.get_index_stats()
        total_vectors = stats.get('total_vector_count', 'unknown')
        logger.info(f"Vector storage complete. Total vectors in index: {total_vectors}")
        
        return doc_id
        
    except Exception as e:
        logger.error(f"Error generating and storing embeddings: {str(e)}", exc_info=True)
        raise Exception(f"Error generating and storing embeddings: {str(e)}") 