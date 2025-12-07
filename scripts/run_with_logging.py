#!/usr/bin/env python3
"""Run a script with full error logging to a file.

Usage:
    python scripts/run_with_logging.py scripts/manual_test_rag_2_pdf_chunking.py
"""

import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Setup logging to both file and console
log_file = Path(__file__).parent.parent / "logs" / f"rag_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_file.parent.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if len(sys.argv) < 2:
    print("Usage: python scripts/run_with_logging.py <script_to_run> [args...]")
    sys.exit(1)

script_to_run = sys.argv[1]
script_args = sys.argv[2:]

logger.info(f"Running script: {script_to_run}")
logger.info(f"Log file: {log_file}")
logger.info(f"Arguments: {script_args}")

try:
    # Import and run the script
    import importlib.util
    spec = importlib.util.spec_from_file_location("script", script_to_run)
    if spec is None:
        logger.error(f"Could not load script: {script_to_run}")
        sys.exit(1)
    
    module = importlib.util.module_from_spec(spec)
    sys.argv = [script_to_run] + script_args
    
    logger.info("="*60)
    logger.info("Starting script execution...")
    logger.info("="*60)
    
    spec.loader.exec_module(module)
    
    logger.info("="*60)
    logger.info("Script completed successfully")
    logger.info("="*60)
    
except KeyboardInterrupt:
    logger.warning("Script interrupted by user")
    sys.exit(130)
except Exception as e:
    logger.error(f"Script failed with error: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

