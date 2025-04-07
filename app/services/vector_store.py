from typing import List, Dict
from openai import OpenAI
import os
from pinecone import Pinecone
import uuid
from dotenv import load_dotenv

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
        spec={
            "serverless": {
                "cloud": "gcp",
                "region": "gcp-starter"
            }
        }
    )

# Connect to the index
index = pc.Index(index_name)

def store_embeddings(text: str) -> str:
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
        
        # Store in Pinecone
        index.upsert(
            vectors=[{
                "id": doc_id,
                "values": embeddings,
                "metadata": {"text": text}
            }]
        )
        
        return doc_id
        
    except Exception as e:
        raise Exception(f"Error generating and storing embeddings: {str(e)}")

def search_similar_texts(query: str, top_k: int = 3) -> List[Dict]:
    """Search for similar texts in the vector database"""
    try:
        # Generate embedding for the query
        response = client.embeddings.create(
            input=query,
            model="text-embedding-ada-002",
            encoding_format="float"
        )
        query_embedding = response.data[0].embedding
        
        # Search in Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return results.matches
        
    except Exception as e:
        raise Exception(f"Error searching similar texts: {str(e)}") 