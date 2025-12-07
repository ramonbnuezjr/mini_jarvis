"""Script to ingest documents into RAG memory."""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Ingest documents into RAG memory."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest documents into Mini-JARVIS RAG memory")
    parser.add_argument(
        "files",
        nargs="+",
        help="File paths to ingest (.txt, .md, .pdf)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size in characters (default: 1000)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap in characters (default: 200)"
    )
    parser.add_argument(
        "--memory-dir",
        type=str,
        default=None,
        help="Directory for RAG memory (default: ~/.jarvis/memory)"
    )
    
    args = parser.parse_args()
    
    # Initialize RAG server
    rag_server = RAGServer(persist_directory=args.memory_dir)
    
    # Check files exist
    file_paths = []
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            continue
        file_paths.append(str(path.absolute()))
    
    if not file_paths:
        logger.error("No valid files to ingest")
        return 1
    
    # Ingest documents
    logger.info(f"Ingesting {len(file_paths)} file(s)...")
    result = await rag_server.ingest_documents(
        file_paths,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    if result["success"]:
        logger.info(f"✅ Successfully ingested {result['chunks_ingested']} chunks from {result['files_processed']} file(s)")
        
        # Show stats
        stats = rag_server.get_stats()
        logger.info(f"Total chunks in memory: {stats['total_chunks']}")
        return 0
    else:
        logger.error(f"❌ Ingestion failed: {result.get('message', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

