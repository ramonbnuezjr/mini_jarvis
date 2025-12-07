"""Unit tests for MetadataTracker."""

import pytest
import tempfile
import time
from pathlib import Path
from src.memory.metadata_tracker import MetadataTracker


class TestMetadataTracker:
    """Test suite for MetadataTracker."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def tracker(self, temp_db):
        """Create MetadataTracker instance."""
        return MetadataTracker(db_path=temp_db)
    
    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample text file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("This is a test document.")
        return str(file_path)
    
    def test_init_database(self, temp_db):
        """Test database initialization."""
        tracker = MetadataTracker(db_path=temp_db)
        assert Path(temp_db).exists()
        
        # Check stats (should be empty)
        stats = tracker.get_stats()
        assert stats['total_chunks'] == 0
        assert stats['expired_documents'] == 0
    
    def test_compute_file_hash(self, tracker, sample_file):
        """Test file hash computation."""
        hash1 = tracker.compute_file_hash(sample_file)
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex length
        
        # Same file should produce same hash
        hash2 = tracker.compute_file_hash(sample_file)
        assert hash1 == hash2
    
    def test_register_document(self, tracker, sample_file):
        """Test document registration."""
        doc_id = tracker.register_document(
            file_path=sample_file,
            tier="core",
            ttl_seconds=None,
            metadata={"author": "test"}
        )
        
        assert isinstance(doc_id, int)
        assert doc_id > 0
        
        # Verify tier
        tier = tracker.get_document_tier(sample_file)
        assert tier == "core"
    
    def test_register_document_all_tiers(self, tracker, sample_file):
        """Test registering documents in all tiers."""
        for tier in ['core', 'reference', 'ephemeral']:
            doc_id = tracker.register_document(
                file_path=f"{sample_file}_{tier}",
                tier=tier
            )
            assert doc_id > 0
    
    def test_register_document_invalid_tier(self, tracker, sample_file):
        """Test that invalid tier raises error."""
        with pytest.raises(ValueError, match="Invalid tier"):
            tracker.register_document(sample_file, tier="invalid")
    
    def test_register_document_with_ttl(self, tracker, sample_file):
        """Test document registration with TTL."""
        doc_id = tracker.register_document(
            file_path=sample_file,
            tier="ephemeral",
            ttl_seconds=3600  # 1 hour
        )
        assert doc_id > 0
    
    def test_register_document_update_on_change(self, tracker, sample_file):
        """Test that document hash change triggers update."""
        # Register initial document
        doc_id1 = tracker.register_document(sample_file, tier="core")
        
        # Modify file
        Path(sample_file).write_text("Modified content")
        
        # Re-register (should update)
        doc_id2 = tracker.register_document(sample_file, tier="reference")
        
        # Should be same document ID (updated, not new)
        assert doc_id1 == doc_id2
        
        # Tier should be updated
        tier = tracker.get_document_tier(sample_file)
        assert tier == "reference"
    
    def test_register_chunks(self, tracker, sample_file):
        """Test chunk registration."""
        doc_id = tracker.register_document(sample_file, tier="core")
        
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        tracker.register_chunks(doc_id, chunk_ids)
        
        # Verify chunks can be looked up
        for chunk_id in chunk_ids:
            tier = tracker.get_chunk_tier(chunk_id)
            assert tier == "core"
    
    def test_track_access(self, tracker, sample_file):
        """Test access tracking."""
        doc_id = tracker.register_document(sample_file, tier="core")
        chunk_ids = ["chunk_1", "chunk_2"]
        tracker.register_chunks(doc_id, chunk_ids)
        
        # Track access
        tracker.track_access("chunk_1")
        tracker.track_access("chunk_1")  # Second access
        
        # Verify tier lookup still works
        tier = tracker.get_chunk_tier("chunk_1")
        assert tier == "core"
    
    def test_get_chunk_tier(self, tracker, sample_file):
        """Test getting tier for a chunk."""
        doc_id = tracker.register_document(sample_file, tier="ephemeral")
        chunk_ids = ["test_chunk"]
        tracker.register_chunks(doc_id, chunk_ids)
        
        tier = tracker.get_chunk_tier("test_chunk")
        assert tier == "ephemeral"
    
    def test_get_chunk_tier_not_found(self, tracker):
        """Test getting tier for non-existent chunk."""
        tier = tracker.get_chunk_tier("nonexistent_chunk")
        assert tier is None
    
    def test_get_expired_documents(self, tracker, tmp_path):
        """Test getting expired documents."""
        # Create ephemeral document with short TTL
        file_path = tmp_path / "ephemeral.txt"
        file_path.write_text("Temporary content")
        
        doc_id = tracker.register_document(
            file_path=str(file_path),
            tier="ephemeral",
            ttl_seconds=1  # 1 second TTL
        )
        chunk_ids = ["ephemeral_chunk"]
        tracker.register_chunks(doc_id, chunk_ids)
        
        # Should not be expired yet
        expired = tracker.get_expired_documents()
        assert len(expired) == 0
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired now
        expired = tracker.get_expired_documents()
        assert len(expired) == 1
        assert expired[0]['document_id'] == doc_id
        assert expired[0]['chunk_ids'] == chunk_ids
    
    def test_delete_document(self, tracker, sample_file):
        """Test document deletion."""
        doc_id = tracker.register_document(sample_file, tier="core")
        chunk_ids = ["chunk_1", "chunk_2"]
        tracker.register_chunks(doc_id, chunk_ids)
        
        # Delete document
        tracker.delete_document(doc_id)
        
        # Verify chunks are gone
        for chunk_id in chunk_ids:
            tier = tracker.get_chunk_tier(chunk_id)
            assert tier is None
    
    def test_get_stats(self, tracker, tmp_path):
        """Test statistics retrieval."""
        # Register documents in different tiers
        for tier in ['core', 'reference', 'ephemeral']:
            file_path = tmp_path / f"{tier}.txt"
            file_path.write_text(f"Content for {tier}")
            doc_id = tracker.register_document(str(file_path), tier=tier)
            tracker.register_chunks(doc_id, [f"{tier}_chunk_1", f"{tier}_chunk_2"])
        
        stats = tracker.get_stats()
        
        assert stats['tier_counts']['core'] == 1
        assert stats['tier_counts']['reference'] == 1
        assert stats['tier_counts']['ephemeral'] == 1
        assert stats['total_chunks'] == 6

