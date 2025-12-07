"""RAG Server: Main interface for RAG pipeline operations."""

import asyncio
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from src.memory.document_ingester import DocumentIngester
from src.memory.retriever import Retriever

logger = logging.getLogger(__name__)


class RAGServer:
    """
    RAG Server for long-term memory retrieval.
    
    Manages vector database (ChromaDB) and provides interface for:
    - Document ingestion and embedding
    - Context retrieval for queries
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "jarvis_memory"
    ):
        """
        Initialize RAG Server.
        
        Args:
            persist_directory: Directory to persist ChromaDB data (default: ~/.jarvis/memory)
            collection_name: Name of the ChromaDB collection
        """
        # Default to ~/.jarvis/memory on NVMe
        if persist_directory is None:
            home = Path.home()
            persist_directory = str(home / ".jarvis" / "memory")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        # Disable telemetry to avoid hangs on Pi5
        try:
            # Try new API first (ChromaDB 0.4+) with telemetry disabled
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry to prevent hangs
                    allow_reset=True
                )
            )
        except Exception as e:
            # If Settings causes issues, try without it
            logger.warning(f"ChromaDB Settings failed, trying without: {e}")
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory)
            )
        
        # Get or create collection
        # Note: ChromaDB will auto-detect embedding dimension from first add()
        # We use all-MiniLM-L6-v2 (384 dim) locally, API fallback uses 768 dim
        # To avoid dimension mismatch, we'll specify dimension if collection is new
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist, create with expected dimension
            # all-MiniLM-L6-v2 has 384 dimensions
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine", "embedding_dimension": 384}
            )
        
        logger.info(f"RAG Server initialized: {self.persist_directory}")
        logger.info(f"Collection '{collection_name}' has {self.collection.count()} documents")
        
        # Initialize components
        self.ingester = DocumentIngester()
        self.retriever = Retriever(self.collection)
    
    async def ingest_documents(
        self,
        file_paths: List[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Ingest documents into the vector database.
        
        Args:
            file_paths: List of file paths to ingest
            chunk_size: Size of text chunks (characters)
            chunk_overlap: Overlap between chunks (characters)
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Ingesting {len(file_paths)} document(s)")
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        for file_path in file_paths:
            try:
                chunks, metadatas = await self.ingester.ingest_file(
                    file_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                # Generate IDs for chunks (use full path hash to avoid duplicates)
                import hashlib
                file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                base_id = Path(file_path).stem
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{base_id}_{file_hash}_chunk_{i}"
                    all_ids.append(chunk_id)
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        **metadatas[i],
                        "chunk_index": i,
                        "file_path": file_path
                    })
                
                logger.info(f"Ingested {len(chunks)} chunks from {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
                continue
        
        if not all_chunks:
            return {
                "success": False,
                "message": "No chunks were ingested",
                "chunks_ingested": 0
            }
        
        # Generate embeddings and add to collection
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        print(f"   [INFO] Generating embeddings for {len(all_chunks)} chunks...")
        import sys
        sys.stdout.flush()
        
        try:
            embeddings = await asyncio.wait_for(
                self.ingester.embed_chunks(all_chunks),
                timeout=300  # 5 minute timeout for embedding
            )
            logger.info(f"Generated {len(embeddings)} embeddings")
            print(f"   [INFO] Generated {len(embeddings)} embeddings")
        except asyncio.TimeoutError:
            error_msg = f"Embedding generation timed out after 5 minutes for {len(all_chunks)} chunks"
            logger.error(error_msg)
            print(f"   [ERROR] {error_msg}")
            raise RuntimeError(error_msg)
        
        # Add to ChromaDB (run in executor to avoid blocking event loop)
        logger.info(f"Adding {len(all_chunks)} chunks to ChromaDB...")
        print(f"   [INFO] Adding {len(all_chunks)} chunks to ChromaDB...")
        sys.stdout.flush()
        
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.collection.add(
                        ids=all_ids,
                        documents=all_chunks,
                        embeddings=embeddings,
                        metadatas=all_metadatas
                    )
                ),
                timeout=300  # 5 minute timeout for ChromaDB add
            )
            logger.info(f"Added {len(all_chunks)} chunks to vector database")
            print(f"   [INFO] Added {len(all_chunks)} chunks to vector database")
        except asyncio.TimeoutError:
            error_msg = f"ChromaDB add operation timed out after 5 minutes for {len(all_chunks)} chunks"
            logger.error(error_msg)
            print(f"   [ERROR] {error_msg}")
            raise RuntimeError(error_msg)
        
        return {
            "success": True,
            "chunks_ingested": len(all_chunks),
            "files_processed": len(file_paths)
        }
    
    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            min_score: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of relevant chunks with metadata
        """
        return await self.retriever.retrieve(query, top_k=top_k, min_score=min_score)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "persist_directory": str(self.persist_directory)
        }
    
    def clear_memory(self) -> None:
        """Clear all documents from memory (use with caution!)."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.warning("Memory cleared!")

