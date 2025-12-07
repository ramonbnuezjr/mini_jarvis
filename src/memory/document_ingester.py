"""Document Ingestion: Load and chunk documents for RAG."""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re

logger = logging.getLogger(__name__)


class DocumentIngester:
    """
    Handles document loading, chunking, and embedding.
    
    Supports:
    - Text files (.txt)
    - Markdown files (.md)
    - PDF files (.pdf) - requires PyPDF2 or pdfplumber
    """
    
    def __init__(self):
        """Initialize document ingester."""
        self._embedding_model = None
    
    async def ingest_file(
        self,
        file_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Load and chunk a document file.
        
        Args:
            file_path: Path to document file
            chunk_size: Size of chunks (characters)
            chunk_overlap: Overlap between chunks (characters)
            
        Returns:
            Tuple of (chunks, metadatas)
        """
        logger.info(f"Ingesting file: {file_path}")
        print(f"   [INFO] Loading file: {file_path}")
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load document based on extension
        ext = path.suffix.lower()
        logger.info(f"File type: {ext}")
        print(f"   [INFO] File type: {ext}")
        
        if ext == ".txt":
            text = await self._load_text(path)
        elif ext == ".md":
            text = await self._load_text(path)
        elif ext == ".pdf":
            text = await self._load_pdf(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        logger.info(f"Loaded {len(text)} characters from file")
        print(f"   [INFO] Loaded {len(text)} characters, chunking...")
        import sys
        sys.stdout.flush()
        
        # Chunk the text
        logger.info(f"Starting chunking with chunk_size={chunk_size}, overlap={chunk_overlap}")
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        logger.info(f"Created {len(chunks)} chunks")
        print(f"   [INFO] Created {len(chunks)} chunks")
        sys.stdout.flush()
        
        # Create metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "source": path.name,
                "file_type": ext[1:],  # Remove leading dot
                "total_chunks": len(chunks)
            })
        
        return chunks, metadatas
    
    async def _load_text(self, path: Path) -> str:
        """Load text or markdown file."""
        loop = asyncio.get_event_loop()
        with open(path, "r", encoding="utf-8") as f:
            text = await loop.run_in_executor(None, f.read)
        return text
    
    async def _load_pdf(self, path: Path) -> str:
        """Load PDF file."""
        try:
            import PyPDF2
        except ImportError:
            try:
                import pdfplumber
            except ImportError:
                raise ImportError(
                    "PDF support requires PyPDF2 or pdfplumber. "
                    "Install with: pip install PyPDF2"
                )
        
        # Try pdfplumber first (better text extraction)
        try:
            import pdfplumber
            loop = asyncio.get_event_loop()
            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = await loop.run_in_executor(None, page.extract_text)
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except ImportError:
            # Fallback to PyPDF2
            import PyPDF2
            loop = asyncio.get_event_loop()
            text_parts = []
            with open(path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    page_text = await loop.run_in_executor(None, page.extract_text)
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (characters)
            chunk_overlap: Overlap between chunks (characters)
            
        Returns:
            List of text chunks
        """
        logger.debug(f"_chunk_text called: text_len={len(text)}, chunk_size={chunk_size}, overlap={chunk_overlap}")
        
        if len(text) <= chunk_size:
            logger.debug("Text fits in single chunk, returning as-is")
            return [text]
        
        chunks = []
        start = 0
        stride = chunk_size - chunk_overlap  # Amount to advance each iteration
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at sentence boundary (optional optimization)
            if end < len(text):
                # Look for sentence endings near the end
                sentence_end = max(
                    text.rfind(". ", start, end),
                    text.rfind("! ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("\n\n", start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Advance by stride (chunk_size - overlap) for proper overlapping chunks
            start += stride
            
            # Safety check: ensure we always advance
            if start >= len(text):
                break
        
        return chunks
    
    async def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks.
        
        Uses local embedding model (sentence-transformers) for privacy.
        Falls back to API if local model unavailable.
        
        Note: Local model (all-MiniLM-L6-v2) produces 384-dim embeddings.
        API fallback (Gemini embedding-001) produces 768-dim embeddings.
        ChromaDB collections must use consistent dimensions.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of embedding vectors
        """
        # Try local embedding model first (384 dimensions)
        try:
            return await self._embed_local(chunks)
        except Exception as e:
            logger.warning(f"Local embedding failed: {e}")
            # Don't use API fallback if local fails - dimension mismatch will break ChromaDB
            # Instead, re-raise the error so caller knows embedding failed
            raise RuntimeError(
                f"Embedding failed: {e}. "
                "Local embeddings are required for consistent dimension (384). "
                "Install sentence-transformers: pip install sentence-transformers"
            ) from e
    
    async def _embed_local(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "Local embeddings require sentence-transformers. "
                "Install with: pip install sentence-transformers"
            )
        
        # Use lightweight model for Raspberry Pi
        # all-MiniLM-L6-v2 is ~80MB and works well on CPU
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {model_name}")
            print(f"   [INFO] Loading embedding model: {model_name}")
            print(f"   [INFO] Model loading can take 1-3 minutes on Pi5...")
            print(f"   [INFO] Please wait, this is a one-time initialization...")
            import sys
            sys.stdout.flush()
            
            loop = asyncio.get_event_loop()
            try:
                # Use wait_for to add timeout protection
                self._embedding_model = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        SentenceTransformer,
                        model_name
                    ),
                    timeout=300  # 5 minute timeout for model loading
                )
                print(f"   [INFO] Model loaded successfully!")
            except asyncio.TimeoutError:
                error_msg = (
                    f"Model loading timed out after 5 minutes. "
                    f"This may indicate a system issue. "
                    f"Try: python scripts/preload_embedding_model.py"
                )
                logger.error(error_msg)
                print(f"   [ERROR] {error_msg}")
                raise RuntimeError(error_msg)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        print(f"   [INFO] Generating embeddings for {len(chunks)} chunks...")
        loop = asyncio.get_event_loop()
        # sentence-transformers encode() takes normalize_embeddings as a keyword arg
        def encode_chunks():
            return self._embedding_model.encode(
                chunks,
                normalize_embeddings=True,  # Normalize for cosine similarity
                show_progress_bar=False  # Disable progress bar in executor
            )
        embeddings = await loop.run_in_executor(None, encode_chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")
        print(f"   [INFO] Generated {len(embeddings)} embeddings")
        
        return embeddings.tolist()
    
    async def _embed_api(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings using API (fallback)."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Try Gemini embedding API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "No embedding method available. "
                "Install sentence-transformers or set GEMINI_API_KEY"
            )
        
        # Use Gemini's embedding API
        import httpx
        
        async with httpx.AsyncClient() as client:
            embeddings = []
            for chunk in chunks:
                # Gemini embedding API endpoint
                url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={api_key}"
                
                response = await client.post(
                    url,
                    json={
                        "model": "models/embedding-001",
                        "content": {"parts": [{"text": chunk}]}
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"]["values"])
            
            return embeddings

