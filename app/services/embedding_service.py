from typing import List, Dict
from openai import OpenAI
import os
import time
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

class EmbeddingService:
    @staticmethod
    def get_index_stats(index_name: str = "business-knowledge-base") -> Dict:
        """
        Get statistics about the index including vector counts per namespace
        """
        try:
            index = pc.Index(index_name)
            return index.describe_index_stats()
        except Exception as e:
            print(f"Error getting index stats: {str(e)}")
            raise

    @staticmethod
    def generate_embeddings(texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI's text-embedding-ada-002 model
        """
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            raise

    @staticmethod
    def wait_for_index_ready(index_name: str):
        """
        Wait for the index to be ready
        """
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    @staticmethod
    def upsert_to_pinecone(vectors: List[Dict], index_name: str = "business-knowledge-base", namespace: str = None):
        """
        Upsert vectors to Pinecone index
        """
        try:
            # Wait for index to be ready
            EmbeddingService.wait_for_index_ready(index_name)
            
            # Get the index
            index = pc.Index(index_name)
            
            # Prepare upsert parameters
            upsert_params = {"vectors": vectors}
            if namespace:
                upsert_params["namespace"] = namespace
                
            # Perform upsert
            index.upsert(**upsert_params)
            
            # Log the operation
            stats = EmbeddingService.get_index_stats(index_name)
            print(f"Upserted {len(vectors)} vectors. Current index stats: {stats}")
        except Exception as e:
            print(f"Error upserting to Pinecone: {str(e)}")
            raise

    @staticmethod
    def prepare_vectors(texts: List[str], metadata: List[Dict] = None) -> List[Dict]:
        """
        Prepare vectors for Pinecone upsert
        """
        embeddings = EmbeddingService.generate_embeddings(texts)
        vectors = []
        
        for i, embedding in enumerate(embeddings):
            vector = {
                "id": f"vec_{i}",
                "values": embedding,
                "metadata": metadata[i] if metadata else {"text": texts[i]}
            }
            vectors.append(vector)
        
        return vectors

    @staticmethod
    def search_similar_texts(query: str, top_k: int = 5, index_name: str = "business-knowledge-base", namespace: str = None) -> List[Dict]:
        """
        Search for similar texts in Pinecone index
        """
        try:
            # Generate embedding for the query
            query_embedding = EmbeddingService.generate_embeddings([query])[0]
            
            # Search in Pinecone
            index = pc.Index(index_name)
            
            # Prepare query parameters
            query_params = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": True
            }
            if namespace:
                query_params["namespace"] = namespace
                
            results = index.query(**query_params)
            
            return results.matches
        except Exception as e:
            print(f"Error searching similar texts: {str(e)}")
            raise 