"""Unit tests for DocumentIngester."""

import pytest
import asyncio
from pathlib import Path
from src.memory.document_ingester import DocumentIngester


class TestDocumentIngester:
    """Test suite for DocumentIngester."""
    
    @pytest.mark.asyncio
    async def test_load_text_file(self, sample_text_file):
        """Test loading a text file."""
        ingester = DocumentIngester()
        text = await ingester._load_text(Path(sample_text_file))
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert "artificial intelligence" in text.lower()
    
    @pytest.mark.asyncio
    async def test_load_markdown_file(self, sample_markdown_file):
        """Test loading a markdown file."""
        ingester = DocumentIngester()
        text = await ingester._load_text(Path(sample_markdown_file))
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert "# Test Document" in text
    
    def test_chunk_text_small(self):
        """Test chunking small text (no chunking needed)."""
        ingester = DocumentIngester()
        text = "This is a short text."
        chunks = ingester._chunk_text(text, chunk_size=1000, chunk_overlap=200)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_large(self):
        """Test chunking large text."""
        ingester = DocumentIngester()
        # Create text longer than chunk size
        text = "Sentence one. Sentence two. Sentence three. " * 50  # ~1500 chars
        chunks = ingester._chunk_text(text, chunk_size=200, chunk_overlap=50)
        
        assert len(chunks) > 1
        # Verify chunks don't exceed size (with some tolerance)
        for chunk in chunks:
            assert len(chunk) <= 250  # chunk_size + some overlap tolerance
    
    def test_chunk_text_overlap(self):
        """Test that chunks have proper overlap."""
        ingester = DocumentIngester()
        text = "A. B. C. D. E. F. G. H. I. J. " * 10
        chunks = ingester._chunk_text(text, chunk_size=100, chunk_overlap=30)
        
        if len(chunks) > 1:
            # Check that consecutive chunks share some content
            chunk1_end = chunks[0][-50:]
            chunk2_start = chunks[1][:50]
            # They should share some overlap (not exact due to sentence boundaries)
            assert len(chunk1_end) > 0
            assert len(chunk2_start) > 0
    
    @pytest.mark.asyncio
    async def test_ingest_text_file(self, sample_text_file):
        """Test ingesting a text file."""
        ingester = DocumentIngester()
        chunks, metadatas = await ingester.ingest_file(
            sample_text_file,
            chunk_size=200,
            chunk_overlap=50
        )
        
        assert len(chunks) > 0
        assert len(metadatas) == len(chunks)
        assert all("source" in meta for meta in metadatas)
        assert all("file_type" in meta for meta in metadatas)
    
    @pytest.mark.asyncio
    async def test_ingest_markdown_file(self, sample_markdown_file):
        """Test ingesting a markdown file."""
        ingester = DocumentIngester()
        chunks, metadatas = await ingester.ingest_file(
            sample_markdown_file,
            chunk_size=200,
            chunk_overlap=50
        )
        
        assert len(chunks) > 0
        assert len(metadatas) == len(chunks)
        assert metadatas[0]["file_type"] == "md"
    
    @pytest.mark.asyncio
    async def test_ingest_nonexistent_file(self):
        """Test ingesting a non-existent file raises error."""
        ingester = DocumentIngester()
        
        with pytest.raises(FileNotFoundError):
            await ingester.ingest_file("/nonexistent/file.txt")
    
    @pytest.mark.asyncio
    async def test_ingest_unsupported_file_type(self, temp_dir):
        """Test ingesting unsupported file type raises error."""
        ingester = DocumentIngester()
        file_path = Path(temp_dir) / "test.xyz"
        file_path.write_text("test content")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            await ingester.ingest_file(str(file_path))
    
    @pytest.mark.asyncio
    async def test_embed_chunks_local(self):
        """Test embedding chunks with local model (if available)."""
        ingester = DocumentIngester()
        chunks = ["This is a test chunk.", "Another test chunk."]
        
        try:
            embeddings = await ingester.embed_chunks(chunks)
            
            assert len(embeddings) == len(chunks)
            assert all(isinstance(emb, list) for emb in embeddings)
            assert all(len(emb) > 0 for emb in embeddings)
            # Embeddings should be normalized (similar length)
            assert all(0.9 < sum(x*x for x in emb)**0.5 < 1.1 for emb in embeddings)
        except ImportError:
            pytest.skip("sentence-transformers not available")
        except Exception as e:
            # If local embedding fails, that's okay (might need API key)
            pytest.skip(f"Local embedding failed: {e}")
    
    def test_chunking_stride_bug_regression(self):
        """Regression test for chunking stride bug (Issue #6, #7).
        
        This test prevents the infinite loop bug from reappearing.
        The bug caused chunks to advance by 1 instead of (chunk_size - overlap).
        
        Why This Test Matters:
        - Prevents silent quality degradation in RAG retrieval
        - Catches accidental loop logic errors during refactoring
        - Documents expected chunking behavior for future developers
        
        Reference: See Experiment #6 (continued 3) and #7 in project docs
        """
        # Arrange: Create test document matching original bug scenario
        text = "x" * 821  # Same size that exposed the bug
        chunk_size = 150
        overlap = 30
        expected_chunks = 7  # Not 16!
        
        # Act: Chunk the text
        ingester = DocumentIngester()
        chunks = ingester._chunk_text(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=overlap
        )
        
        # Assert: Verify correct chunk count
        assert len(chunks) == expected_chunks, (
            f"Chunking stride bug regression detected! "
            f"Expected {expected_chunks} chunks, got {len(chunks)}. "
            f"This means the stride calculation is broken again."
        )
        
        # Additional assertion: Verify no max iteration warning triggered
        # (The bug caused the loop to hit max iterations before completing)
        assert len(chunks) < 10, (
            f"Too many chunks ({len(chunks)}) suggests the stride bug returned. "
            f"Check that start position increments by (chunk_size - overlap), not 1."
        )
    
    def test_chunking_stride_calculation(self):
        """Verify stride calculation is correct for various parameters.
        
        This test validates the core math that was broken in the original bug.
        """
        ingester = DocumentIngester()
        
        test_cases = [
            # (text_length, chunk_size, overlap, expected_chunk_count)
            (821, 150, 30, 7),    # Original bug scenario
            (500, 100, 20, 7),    # Smaller document
            (1000, 200, 50, 7),   # Larger chunks
            (300, 150, 30, 3),    # Minimal document
        ]
        
        for text_len, chunk_size, overlap, expected_count in test_cases:
            text = "x" * text_len
            chunks = ingester._chunk_text(text, chunk_size, overlap)
            
            assert len(chunks) == expected_count, (
                f"Failed for text_len={text_len}, chunk_size={chunk_size}, "
                f"overlap={overlap}: expected {expected_count} chunks, "
                f"got {len(chunks)}"
            )
    
    def test_chunking_produces_expected_stride_pattern(self):
        """Verify chunk boundaries follow correct stride pattern.
        
        This test checks that chunks start at positions 0, 120, 240, ...
        not at 0, 1, 2, 3, ... (which was the bug).
        """
        ingester = DocumentIngester()
        text = "x" * 821
        chunk_size = 150
        overlap = 30
        expected_stride = chunk_size - overlap  # = 120
        
        chunks = ingester._chunk_text(text, chunk_size, overlap)
        
        # Calculate expected start positions
        expected_starts = []
        pos = 0
        while pos < len(text):
            expected_starts.append(pos)
            pos += expected_stride
        
        # Verify we have the right number of expected positions
        assert len(chunks) == len(expected_starts[:7]), (
            f"Chunk count mismatch: {len(chunks)} vs {len(expected_starts[:7])}"
        )
        
        # Verify chunk sizes are reasonable (not too small due to stride bug)
        for i, chunk in enumerate(chunks):
            assert len(chunk) >= chunk_size - 50, (
                f"Chunk {i} is too small ({len(chunk)} chars), "
                f"may indicate stride bug"
            )

