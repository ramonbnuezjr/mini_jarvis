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
    parser.add_argument(
        "--tier",
        type=str,
        choices=["core", "reference", "ephemeral"],
        default="reference",
        help="Memory tier: 'core' (boosted), 'reference' (normal), 'ephemeral' (deprioritized, can expire)"
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=None,
        help="Time to live in seconds (only for ephemeral tier, default: permanent)"
    )
    parser.add_argument(
        "--no-tiering",
        action="store_true",
        help="Disable tiered memory (use single collection, backward compatible)"
    )
    
    args = parser.parse_args()
    
    # Initialize RAG server with tiering enabled by default
    rag_server = RAGServer(
        persist_directory=args.memory_dir,
        enable_tiering=not args.no_tiering
    )
    
    # Check files exist
    file_paths = []
    missing_files = []
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            missing_files.append(file_path)
            logger.error(f"❌ File not found: {file_path}")
            # Check if it's a relative path issue
            if not path.is_absolute():
                logger.info(f"   💡 Tip: Use absolute path or check current directory: {Path.cwd()}")
            continue
        file_paths.append(str(path.absolute()))
    
    if not file_paths:
        logger.error("❌ No valid files to ingest")
        if missing_files:
            logger.error(f"   Missing files: {', '.join(missing_files)}")
            logger.info("   💡 Make sure the file paths are correct and the files exist")
        return 1
    
    # Ingest documents
    tier_info = f" (tier: {args.tier})" if not args.no_tiering else ""
    if args.ttl and args.tier == "ephemeral":
        tier_info += f", TTL: {args.ttl}s"
    logger.info(f"Ingesting {len(file_paths)} file(s){tier_info}...")
    
    result = await rag_server.ingest_documents(
        file_paths,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        tier=args.tier if not args.no_tiering else "reference",
        ttl_seconds=args.ttl if args.tier == "ephemeral" else None
    )
    
    if result["success"]:
        logger.info(f"✅ Successfully ingested {result['chunks_ingested']} chunks from {result['files_processed']} file(s)")
        
        # Show stats
        stats = rag_server.get_stats()
        if stats.get('tiering_enabled'):
            logger.info(f"Total chunks in memory: {stats['total_chunks']}")
            logger.info(f"Tier distribution: {stats.get('tier_counts', {})}")
        else:
            logger.info(f"Total chunks in memory: {stats['total_chunks']}")
        return 0
    else:
        logger.error(f"❌ Ingestion failed: {result.get('message', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

