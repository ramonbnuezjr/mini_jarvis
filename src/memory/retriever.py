"""Retriever: Semantic search for RAG context retrieval."""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant context from vector database using semantic search.
    Supports tiered memory with weighted retrieval.
    """
    
    def __init__(self, collection=None, collections=None, metadata_tracker=None):
        """
        Initialize retriever.
        
        Args:
            collection: Single ChromaDB collection (backward compatible)
            collections: Dict of tiered collections {'core': coll, 'reference': coll, 'ephemeral': coll}
            metadata_tracker: MetadataTracker instance for tier lookup
        """
        self.collection = collection
        self.collections = collections
        self.metadata_tracker = metadata_tracker
        self._embedding_model = None
        
        # Tier weights for weighted retrieval
        self.tier_weights = {
            'core': 1.5,      # Boost core documents
            'reference': 1.0, # Normal weight
            'ephemeral': 0.7  # Deprioritize ephemeral
        }
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        Supports tiered memory with weighted retrieval.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            min_score: Minimum similarity score (0.0 to 1.0, cosine similarity)
            
        Returns:
            List of relevant chunks with metadata and scores (weighted)
        """
        # Generate query embedding
        query_embedding = await self._embed_query(query)
        
        # Retrieve from tiered collections or single collection
        if self.collections:
            # Tiered retrieval: query all tiers and merge with weights
            all_chunks = []
            
            for tier, collection in self.collections.items():
                weight = self.tier_weights.get(tier, 1.0)
                
                # Query more results per tier to account for weighting
                tier_top_k = max(top_k, 10)  # Get more candidates per tier
                
                try:
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=tier_top_k
                    )
                    
                    if results["ids"] and len(results["ids"][0]) > 0:
                        for i in range(len(results["ids"][0])):
                            distance = results["distances"][0][i] if results.get("distances") else 0.0
                            similarity = 1.0 - distance  # Cosine similarity
                            
                            # Apply tier weight to similarity score
                            weighted_score = similarity * weight
                            
                            if weighted_score >= min_score:
                                chunk_id = results["ids"][0][i]
                                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                                
                                # Track access
                                if self.metadata_tracker:
                                    self.metadata_tracker.track_access(chunk_id)
                                
                                all_chunks.append({
                                    "text": results["documents"][0][i],
                                    "metadata": {**metadata, "tier": tier},
                                    "score": weighted_score,
                                    "base_score": similarity,  # Original score before weighting
                                    "tier": tier,
                                    "weight": weight,
                                    "distance": distance,
                                    "chunk_id": chunk_id
                                })
                except Exception as e:
                    logger.warning(f"Error querying {tier} tier: {e}")
                    continue
            
            # Sort by weighted score and take top_k
            all_chunks.sort(key=lambda x: x["score"], reverse=True)
            chunks = all_chunks[:top_k]
            
        else:
            # Single collection mode (backward compatible)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            chunks = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i] if results.get("distances") else 0.0
                    similarity = 1.0 - distance  # Cosine similarity
                    
                    if similarity >= min_score:
                        chunk_id = results["ids"][0][i]
                        chunks.append({
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                            "score": similarity,
                            "distance": distance,
                            "chunk_id": chunk_id
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

