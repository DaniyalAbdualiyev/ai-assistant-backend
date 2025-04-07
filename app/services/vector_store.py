from typing import List, Dict
from openai import OpenAI
import os
from pinecone import Pinecone, ServerlessSpec
import uuid
from dotenv import load_dotenv
from .embedding_service import EmbeddingService

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
    """
    return EmbeddingService.search_similar_texts(query, top_k, namespace=namespace)

def add_to_knowledge_base(texts: List[str], metadata: List[Dict] = None, namespace: str = None):
    """
    Add texts to the knowledge base
    """
    vectors = EmbeddingService.prepare_vectors(texts, metadata)
    EmbeddingService.upsert_to_pinecone(vectors, namespace=namespace)

def store_embeddings(text: str, namespace: str = None) -> str:
    """
    Store a single text's embeddings in the knowledge base
    """
    try:
        # Generate embeddings using OpenAI
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002",
            encoding_format="float"
        )
        
        # Get the embeddings
        embeddings = response.data[0].embedding
        
        # Generate a unique ID for this document
        doc_id = str(uuid.uuid4())
        
        # Prepare vector
        vector = {
            "id": doc_id,
            "values": embeddings,
            "metadata": {"text": text}
        }
        
        # Store in Pinecone
        EmbeddingService.upsert_to_pinecone([vector], namespace=namespace)
        
        return doc_id
        
    except Exception as e:
        raise Exception(f"Error generating and storing embeddings: {str(e)}") 