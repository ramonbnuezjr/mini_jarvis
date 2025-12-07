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
from src.memory.metadata_tracker import MetadataTracker

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
        collection_name: str = "jarvis_memory",
        enable_tiering: bool = True
    ):
        """
        Initialize RAG Server.
        
        Args:
            persist_directory: Directory to persist ChromaDB data (default: ~/.jarvis/memory)
            collection_name: Name of the ChromaDB collection (base name for tiered mode)
            enable_tiering: Enable tiered memory (core/reference/ephemeral collections)
        """
        # Default to ~/.jarvis/memory on NVMe
        if persist_directory is None:
            home = Path.home()
            persist_directory = str(home / ".jarvis" / "memory")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        self.enable_tiering = enable_tiering
        
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
        
        # Initialize metadata tracker
        self.metadata_tracker = MetadataTracker()
        
        # Initialize collections (tiered or single)
        if enable_tiering:
            self.collections = self._init_tiered_collections()
            logger.info("Tiered memory enabled: core/reference/ephemeral")
        else:
            # Single collection mode (backward compatible)
            self.collection = self._get_or_create_collection(collection_name)
            self.collections = None
            logger.info(f"Single collection mode: '{collection_name}'")
        
        logger.info(f"RAG Server initialized: {self.persist_directory}")
        
        # Initialize components
        self.ingester = DocumentIngester()
        if enable_tiering:
            # Retriever will use tiered collections
            self.retriever = Retriever(None, collections=self.collections, metadata_tracker=self.metadata_tracker)
        else:
            self.retriever = Retriever(self.collection)
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            collection = self.client.get_collection(name=name)
        except Exception:
            # Collection doesn't exist, create with expected dimension
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine", "embedding_dimension": 384}
            )
        return collection
    
    def _init_tiered_collections(self) -> Dict[str, Any]:
        """Initialize tiered collections (core, reference, ephemeral)."""
        collections = {}
        for tier in ['core', 'reference', 'ephemeral']:
            collection_name = f"{self.collection_name}_{tier}"
            collections[tier] = self._get_or_create_collection(collection_name)
            count = collections[tier].count()
            logger.info(f"Collection '{collection_name}' ({tier}) has {count} documents")
        return collections
    
    async def ingest_documents(
        self,
        file_paths: List[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        tier: str = "reference",
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest documents into the vector database.
        
        Args:
            file_paths: List of file paths to ingest
            chunk_size: Size of text chunks (characters)
            chunk_overlap: Overlap between chunks (characters)
            tier: Memory tier ('core', 'reference', or 'ephemeral')
            ttl_seconds: Time to live in seconds (None = permanent, only for ephemeral)
            metadata: Additional metadata dictionary
            
        Returns:
            Dictionary with ingestion statistics
        """
        if tier not in ['core', 'reference', 'ephemeral']:
            raise ValueError(f"Invalid tier: {tier}. Must be 'core', 'reference', or 'ephemeral'")
        
        logger.info(f"Ingesting {len(file_paths)} document(s) into tier '{tier}'")
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        document_registrations = []
        
        for file_path in file_paths:
            try:
                chunks, metadatas = await self.ingester.ingest_file(
                    file_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                # Register document in metadata tracker
                doc_id = self.metadata_tracker.register_document(
                    file_path=file_path,
                    tier=tier,
                    ttl_seconds=ttl_seconds,
                    metadata=metadata
                )
                document_registrations.append((doc_id, file_path, len(chunks)))
                
                # Generate IDs for chunks (use full path hash to avoid duplicates)
                import hashlib
                file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                base_id = Path(file_path).stem
                chunk_ids_for_file = []
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{base_id}_{file_hash}_chunk_{i}"
                    chunk_ids_for_file.append(chunk_id)
                    all_ids.append(chunk_id)
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        **metadatas[i],
                        "chunk_index": i,
                        "file_path": file_path,
                        "tier": tier  # Add tier to metadata
                    })
                
                # Register chunks in metadata tracker
                self.metadata_tracker.register_chunks(doc_id, chunk_ids_for_file)
                
                logger.info(f"Ingested {len(chunks)} chunks from {file_path} (tier={tier})")
                
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
        
        # Add to ChromaDB (tiered or single collection)
        logger.info(f"Adding {len(all_chunks)} chunks to ChromaDB (tier={tier})...")
        print(f"   [INFO] Adding {len(all_chunks)} chunks to ChromaDB (tier={tier})...")
        sys.stdout.flush()
        
        # Select target collection
        if self.enable_tiering:
            target_collection = self.collections[tier]
        else:
            target_collection = self.collection
        
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: target_collection.add(
                        ids=all_ids,
                        documents=all_chunks,
                        embeddings=embeddings,
                        metadatas=all_metadatas
                    )
                ),
                timeout=300  # 5 minute timeout for ChromaDB add
            )
            logger.info(f"Added {len(all_chunks)} chunks to {tier} tier")
            print(f"   [INFO] Added {len(all_chunks)} chunks to {tier} tier")
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
        if self.enable_tiering:
            tier_counts = {}
            total_chunks = 0
            for tier, collection in self.collections.items():
                count = collection.count()
                tier_counts[tier] = count
                total_chunks += count
            metadata_stats = self.metadata_tracker.get_stats()
            return {
                "total_chunks": total_chunks,
                "tier_counts": tier_counts,
                "persist_directory": str(self.persist_directory),
                "tiering_enabled": True,
                "metadata_stats": metadata_stats
            }
        else:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "persist_directory": str(self.persist_directory),
                "tiering_enabled": False
            }
    
    def clear_memory(self, tier: Optional[str] = None) -> None:
        """
        Clear documents from memory (use with caution!).
        
        Args:
            tier: If specified, clear only this tier. If None, clear all.
        """
        if self.enable_tiering:
            if tier:
                if tier not in ['core', 'reference', 'ephemeral']:
                    raise ValueError(f"Invalid tier: {tier}")
                self.client.delete_collection(f"{self.collection_name}_{tier}")
                self.collections[tier] = self._get_or_create_collection(f"{self.collection_name}_{tier}")
                logger.warning(f"Memory cleared for tier '{tier}'!")
            else:
                for tier_name in ['core', 'reference', 'ephemeral']:
                    self.client.delete_collection(f"{self.collection_name}_{tier_name}")
                    self.collections[tier_name] = self._get_or_create_collection(f"{self.collection_name}_{tier_name}")
                logger.warning("All memory cleared!")
        else:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection(self.collection_name)
            logger.warning("Memory cleared!")
    
    async def cleanup_expired(self) -> Dict[str, Any]:
        """
        Clean up expired ephemeral documents (TTL exceeded).
        
        Returns:
            Dictionary with cleanup statistics
        """
        expired = self.metadata_tracker.get_expired_documents()
        
        if not expired:
            return {
                "expired_count": 0,
                "chunks_deleted": 0,
                "message": "No expired documents found"
            }
        
        logger.info(f"Cleaning up {len(expired)} expired documents")
        
        total_chunks_deleted = 0
        
        for doc_info in expired:
            doc_id = doc_info['document_id']
            chunk_ids = doc_info['chunk_ids']
            
            # Delete from ChromaDB (ephemeral collection)
            if self.enable_tiering and chunk_ids:
                try:
                    self.collections['ephemeral'].delete(ids=chunk_ids)
                    total_chunks_deleted += len(chunk_ids)
                except Exception as e:
                    logger.error(f"Failed to delete chunks from ChromaDB: {e}")
            
            # Delete from metadata tracker
            self.metadata_tracker.delete_document(doc_id)
        
        return {
            "expired_count": len(expired),
            "chunks_deleted": total_chunks_deleted,
            "message": f"Cleaned up {len(expired)} expired documents"
        }

