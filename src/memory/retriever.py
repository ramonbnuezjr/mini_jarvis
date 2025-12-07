"""Retriever: Semantic search for RAG context retrieval."""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant context from vector database using semantic search.
    """
    
    def __init__(self, collection):
        """
        Initialize retriever.
        
        Args:
            collection: ChromaDB collection instance
        """
        self.collection = collection
        self._embedding_model = None
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            min_score: Minimum similarity score (0.0 to 1.0, cosine similarity)
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        # Generate query embedding
        query_embedding = await self._embed_query(query)
        
        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        chunks = []
        
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                # ChromaDB returns distances (lower is better for cosine)
                # Convert to similarity score (1 - distance)
                distance = results["distances"][0][i] if results.get("distances") else 0.0
                similarity = 1.0 - distance  # Cosine similarity
                
                if similarity >= min_score:
                    chunks.append({
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "score": similarity,
                        "distance": distance
                    })
        
        logger.info(f"Retrieved {len(chunks)} chunks for query (min_score={min_score})")
        
        return chunks
    
    async def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for query text."""
        # Use the same embedding logic as DocumentIngester
        # Must use local model to match document embeddings (384 dimensions)
        try:
            embeddings = await self._embed_local([query])
            return embeddings[0]
        except Exception as e:
            # Don't fallback to API - dimension mismatch
            raise RuntimeError(
                f"Query embedding failed: {e}. "
                "Local embeddings required for consistent dimension."
            ) from e
    
    async def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Local embeddings require sentence-transformers")
        
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        if self._embedding_model is None:
            import asyncio
            loop = asyncio.get_event_loop()
            self._embedding_model = await loop.run_in_executor(
                None,
                SentenceTransformer,
                model_name
            )
        
        import asyncio
        loop = asyncio.get_event_loop()
        def encode_texts():
            return self._embedding_model.encode(
                texts,
                normalize_embeddings=True
            )
        embeddings = await loop.run_in_executor(None, encode_texts)
        
        return embeddings.tolist()
    
    async def _embed_api(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using API (fallback)."""
        import os
        from dotenv import load_dotenv
        import httpx
        
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No embedding method available")
        
        async with httpx.AsyncClient() as client:
            embeddings = []
            for text in texts:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={api_key}"
                response = await client.post(
                    url,
                    json={
                        "model": "models/embedding-001",
                        "content": {"parts": [{"text": text}]}
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"]["values"])
            
            return embeddings
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string for LLM.
        
        Args:
            chunks: List of chunk dictionaries from retrieve()
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "unknown")
            text = chunk["text"]
            score = chunk.get("score", 0.0)
            
            context_parts.append(
                f"[Context {i} - Source: {source}, Relevance: {score:.2f}]\n{text}\n"
            )
        
        return "\n".join(context_parts)

