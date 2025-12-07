"""Metadata Tracker: SQLite-based tracking for document versioning, TTL, and access patterns."""

import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class MetadataTracker:
    """
    Tracks document metadata in SQLite database.
    
    Features:
    - Version hashing (detect document changes)
    - TTL (Time To Live) for ephemeral documents
    - Access tracking (last accessed, access count)
    - Tier management (core/reference/ephemeral)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize metadata tracker.
        
        Args:
            db_path: Path to SQLite database (default: ~/.jarvis/memory/metadata.db)
        """
        if db_path is None:
            home = Path.home()
            db_path = str(home / ".jarvis" / "memory" / "metadata.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Documents table: tracks file-level metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'reference',
                ttl_seconds INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT DEFAULT '{}'
            )
        """)
        
        # Chunks table: tracks chunk-level metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT NOT NULL UNIQUE,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                last_accessed TIMESTAMP DEFAULT NULL,
                access_count INTEGER DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id 
            ON chunks(document_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_last_accessed 
            ON chunks(last_accessed)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_tier 
            ON documents(tier)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_ttl 
            ON documents(ttl_seconds)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Metadata tracker initialized: {self.db_path}")
    
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hexadecimal hash string
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def register_document(
        self,
        file_path: str,
        tier: str = "reference",
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Register or update a document in the tracker.
        
        Args:
            file_path: Path to document file
            tier: Memory tier ('core', 'reference', or 'ephemeral')
            ttl_seconds: Time to live in seconds (None = permanent)
            metadata: Additional metadata dictionary
            
        Returns:
            Document ID
        """
        if tier not in ['core', 'reference', 'ephemeral']:
            raise ValueError(f"Invalid tier: {tier}. Must be 'core', 'reference', or 'ephemeral'")
        
        file_hash = self.compute_file_hash(file_path)
        metadata_json = json.dumps(metadata or {})
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check if document exists
        cursor.execute(
            "SELECT id, file_hash FROM documents WHERE file_path = ?",
            (file_path,)
        )
        result = cursor.fetchone()
        
        if result:
            doc_id, old_hash = result
            if old_hash != file_hash:
                # Document changed - update hash and timestamp
                cursor.execute("""
                    UPDATE documents 
                    SET file_hash = ?, 
                        tier = ?,
                        ttl_seconds = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        metadata_json = ?
                    WHERE id = ?
                """, (file_hash, tier, ttl_seconds, metadata_json, doc_id))
                logger.info(f"Document updated: {file_path} (hash changed)")
            else:
                # Document unchanged - just update tier/metadata if needed
                cursor.execute("""
                    UPDATE documents 
                    SET tier = ?,
                        ttl_seconds = ?,
                        metadata_json = ?
                    WHERE id = ?
                """, (tier, ttl_seconds, metadata_json, doc_id))
        else:
            # New document
            cursor.execute("""
                INSERT INTO documents (file_path, file_hash, tier, ttl_seconds, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (file_path, file_hash, tier, ttl_seconds, metadata_json))
            doc_id = cursor.lastrowid
            logger.info(f"Document registered: {file_path} (tier={tier})")
        
        conn.commit()
        conn.close()
        
        return doc_id
    
    def register_chunks(
        self,
        document_id: int,
        chunk_ids: List[str]
    ) -> None:
        """
        Register chunks for a document.
        
        Args:
            document_id: Document ID from register_document()
            chunk_ids: List of chunk IDs (must match ChromaDB chunk IDs)
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        for i, chunk_id in enumerate(chunk_ids):
            cursor.execute("""
                INSERT OR IGNORE INTO chunks (chunk_id, document_id, chunk_index)
                VALUES (?, ?, ?)
            """, (chunk_id, document_id, i))
        
        conn.commit()
        conn.close()
        logger.debug(f"Registered {len(chunk_ids)} chunks for document {document_id}")
    
    def track_access(self, chunk_id: str) -> None:
        """
        Track access to a chunk (for analytics and prioritization).
        
        Args:
            chunk_id: ChromaDB chunk ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE chunks 
            SET last_accessed = CURRENT_TIMESTAMP,
                access_count = access_count + 1
            WHERE chunk_id = ?
        """, (chunk_id,))
        
        conn.commit()
        conn.close()
    
    def get_document_tier(self, file_path: str) -> Optional[str]:
        """
        Get tier for a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Tier name or None if not registered
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT tier FROM documents WHERE file_path = ?",
            (file_path,)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else None
    
    def get_chunk_tier(self, chunk_id: str) -> Optional[str]:
        """
        Get tier for a chunk (via its document).
        
        Args:
            chunk_id: ChromaDB chunk ID
            
        Returns:
            Tier name or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d.tier 
            FROM documents d
            JOIN chunks c ON c.document_id = d.id
            WHERE c.chunk_id = ?
        """, (chunk_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_expired_documents(self) -> List[Dict[str, Any]]:
        """
        Get list of documents that have expired (TTL exceeded).
        
        Returns:
            List of document dictionaries with 'file_path' and 'chunk_ids'
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Find documents where TTL has expired
        cursor.execute("""
            SELECT d.id, d.file_path, d.created_at, d.ttl_seconds,
                   GROUP_CONCAT(c.chunk_id) as chunk_ids
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            WHERE d.ttl_seconds IS NOT NULL
              AND (julianday('now') - julianday(d.created_at)) * 86400 > d.ttl_seconds
            GROUP BY d.id
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        expired = []
        for row in results:
            doc_id, file_path, created_at, ttl_seconds, chunk_ids_str = row
            chunk_ids = chunk_ids_str.split(',') if chunk_ids_str else []
            expired.append({
                'document_id': doc_id,
                'file_path': file_path,
                'created_at': created_at,
                'ttl_seconds': ttl_seconds,
                'chunk_ids': chunk_ids
            })
        
        return expired
    
    def delete_document(self, document_id: int) -> None:
        """
        Delete a document and all its chunks from tracker.
        
        Args:
            document_id: Document ID to delete
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Delete chunks first (foreign key constraint)
        cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        
        # Delete document
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Deleted document {document_id} from tracker")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked documents."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Count by tier
        cursor.execute("""
            SELECT tier, COUNT(*) 
            FROM documents 
            GROUP BY tier
        """)
        tier_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total chunks
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]
        
        # Expired documents count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM documents 
            WHERE ttl_seconds IS NOT NULL
              AND (julianday('now') - julianday(created_at)) * 86400 > ttl_seconds
        """)
        expired_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'tier_counts': tier_counts,
            'total_chunks': total_chunks,
            'expired_documents': expired_count
        }

