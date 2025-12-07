#!/usr/bin/env python3
"""Diagnose RAG ingestion with full logging to file."""

import asyncio
import sys
import time
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging to file
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"rag_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from src.memory.rag_server import RAGServer

async def diagnose():
    logger.info("="*60)
    logger.info("RAG Ingestion Diagnostic - Full Log")
    logger.info("="*60)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {datetime.now()}")
    
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Temp directory: {temp_dir}")
    
    try:
        # Create test document (same as manual test)
        logger.info("\n" + "="*60)
        logger.info("Step 1: Creating test document")
        logger.info("="*60)
        
        test_file = Path(temp_dir) / "test_document.md"
        content = """# Technical Documentation

## Introduction
This is a technical document with multiple sections.
The system consists of multiple components working together.

## Section 1: Overview
This section provides an overview of the system architecture.
Each component has specific responsibilities and interfaces.

## Section 2: Implementation
Implementation details are critical for understanding the system.
Multiple test types are used: unit tests, integration tests, and UAT.

## Section 3: Testing
Testing ensures system reliability and correctness.
The system must be deployed to production environments safely.

## Section 4: Deployment
Deployment involves multiple steps and careful planning.
This document covers all major aspects of the system.

## Conclusion
This document provides comprehensive technical documentation."""
        
        test_file.write_text(content)
        logger.info(f"Created: {test_file}")
        logger.info(f"Size: {len(content)} characters")
        
        # Calculate expected chunks
        chunk_size = 150
        chunk_overlap = 30
        expected_chunks = max(1, (len(content) - chunk_overlap) // (chunk_size - chunk_overlap) + 1)
        logger.info(f"Expected chunks (chunk_size={chunk_size}, overlap={chunk_overlap}): ~{expected_chunks}")
        
        # Initialize RAG server
        logger.info("\n" + "="*60)
        logger.info("Step 2: Initializing RAG server")
        logger.info("="*60)
        
        start = time.time()
        try:
            rag_server = RAGServer(
                persist_directory=temp_dir,
                collection_name="diagnostic_test"
            )
            elapsed = time.time() - start
            logger.info(f"✅ RAG server initialized in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"❌ RAG server initialization failed after {elapsed:.2f}s: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return
        
        # Test ingestion
        logger.info("\n" + "="*60)
        logger.info("Step 3: Testing ingestion")
        logger.info("="*60)
        logger.info(f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        logger.info("Starting ingestion with 5 minute timeout...")
        
        start = time.time()
        try:
            result = await asyncio.wait_for(
                rag_server.ingest_documents(
                    [str(test_file)],
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                ),
                timeout=300
            )
            elapsed = time.time() - start
            logger.info(f"\n✅ Ingestion completed in {elapsed:.2f}s")
            logger.info(f"   Chunks ingested: {result.get('chunks_ingested', 0)}")
            logger.info(f"   Files processed: {result.get('files_processed', 0)}")
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            logger.error(f"\n❌ Ingestion TIMED OUT after {elapsed:.2f}s")
            logger.error("   This indicates a hang in the ingestion process")
            logger.error("   Check the log above to see where it stopped")
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"\n❌ Ingestion FAILED after {elapsed:.2f}s: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("\n" + "="*60)
        logger.info("Diagnostic complete")
        logger.info("="*60)
        logger.info(f"Full log saved to: {log_file}")
        
    except Exception as e:
        logger.error(f"Diagnostic script error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temp directory: {temp_dir}")

if __name__ == "__main__":
    print(f"Running diagnostic - log will be saved to: logs/rag_diagnostic_*.log")
    asyncio.run(diagnose())

