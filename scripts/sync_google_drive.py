#!/usr/bin/env python3
"""Google Drive Sync for Mini-JARVIS RAG Memory.

Syncs Google Drive folders to tiered RAG memory:
- JARVIS-Core/ → core tier (1.5x retrieval boost)
- JARVIS-Reference/ → reference tier (1.0x normal weight)
- JARVIS-Ephemeral/ → ephemeral tier (0.7x weight, auto-expire)

Features:
- OAuth 2.0 authentication
- Incremental sync (only changed files)
- Version hash tracking
- Folder-to-tier mapping
- Last sync timestamp tracking
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Google Drive API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
except ImportError as e:
    print(f"❌ Missing Google Drive API dependencies: {e}")
    print("   Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.rag_server import RAGServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Folder-to-tier mapping
FOLDER_TIER_MAP = {
    'JARVIS-Core': 'core',
    'JARVIS-Reference': 'reference',
    'JARVIS-Ephemeral': 'ephemeral'
}

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.txt', '.md', '.markdown', '.pdf', '.docx', '.doc'}


class GoogleDriveSync:
    """Google Drive sync manager for RAG memory."""
    
    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        sync_state_file: str = ".drive_sync_state.json",
        memory_dir: Optional[str] = None
    ):
        """
        Initialize Google Drive sync.
        
        Args:
            credentials_file: Path to OAuth 2.0 credentials JSON file
            token_file: Path to store OAuth token
            sync_state_file: Path to sync state (last sync time, file hashes)
            memory_dir: Directory for RAG memory (default: ~/.jarvis/memory)
        """
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self.sync_state_file = Path(sync_state_file)
        self.memory_dir = memory_dir
        
        # Load sync state
        self.sync_state = self._load_sync_state()
        
        # Initialize RAG server
        self.rag_server = RAGServer(
            persist_directory=memory_dir,
            enable_tiering=True
        )
        
        # Google Drive service (initialized after auth)
        self.service = None
    
    def _load_sync_state(self) -> Dict:
        """Load sync state from file."""
        if self.sync_state_file.exists():
            try:
                with open(self.sync_state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sync state: {e}")
        
        return {
            'last_sync': None,
            'file_hashes': {},  # file_id -> hash
            'file_versions': {}  # file_id -> version (modifiedTime)
        }
    
    def _save_sync_state(self):
        """Save sync state to file."""
        try:
            with open(self.sync_state_file, 'w') as f:
                json.dump(self.sync_state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")
    
    def _authenticate(self) -> bool:
        """Authenticate with Google Drive API using OAuth 2.0."""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired token...")
                creds.refresh(Request())
            else:
                if not self.credentials_file.exists():
                    logger.error(f"❌ Credentials file not found: {self.credentials_file}")
                    logger.error("   Download credentials.json from Google Cloud Console:")
                    logger.error("   1. Go to https://console.cloud.google.com/")
                    logger.error("   2. Create/select a project")
                    logger.error("   3. Enable Google Drive API")
                    logger.error("   4. Create OAuth 2.0 credentials (Desktop app)")
                    logger.error("   5. Download as credentials.json")
                    return False
                
                logger.info("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for future use
            try:
                with open(self.token_file, 'w') as f:
                    f.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to save token: {e}")
                return False
        
        # Build service
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Authenticated with Google Drive")
            return True
        except Exception as e:
            logger.error(f"Failed to build Drive service: {e}")
            return False
    
    def _get_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def _find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """Find Google Drive folder by name."""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=10
            ).execute()
            
            folders = results.get('files', [])
            if not folders:
                logger.warning(f"Folder not found: {folder_name}")
                return None
            
            if len(folders) > 1:
                logger.warning(f"Multiple folders named '{folder_name}', using first: {folders[0]['id']}")
            
            return folders[0]['id']
        except HttpError as e:
            logger.error(f"Error finding folder '{folder_name}': {e}")
            return None
    
    def _list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """List all files in a Google Drive folder (recursively)."""
        files = []
        page_token = None
        
        # Google Docs export formats
        GOOGLE_DOCS_EXPORT = {
            'application/vnd.google-apps.document': 'text/plain',  # Export as plain text
            'application/vnd.google-apps.spreadsheet': 'text/csv',  # Export as CSV
            'application/vnd.google-apps.presentation': 'text/plain',  # Export as plain text
        }
        
        try:
            while True:
                # Query for files in folder
                query = f"'{folder_id}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                    pageToken=page_token,
                    pageSize=100
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    mime_type = item.get('mimeType', '')
                    
                    # If it's a folder, recurse
                    if mime_type == 'application/vnd.google-apps.folder':
                        subfolder_files = self._list_files_in_folder(item['id'])
                        files.extend(subfolder_files)
                    else:
                        file_name = item.get('name', '')
                        ext = Path(file_name).suffix.lower()
                        
                        # Check if it's a Google Docs file (needs export)
                        if mime_type in GOOGLE_DOCS_EXPORT:
                            # Add export format to metadata
                            item['export_mime_type'] = GOOGLE_DOCS_EXPORT[mime_type]
                            files.append(item)
                        # Check if regular file type is supported
                        elif ext in SUPPORTED_EXTENSIONS or mime_type.startswith('text/'):
                            files.append(item)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
        
        except HttpError as e:
            logger.error(f"Error listing files in folder {folder_id}: {e}")
        
        return files
    
    def _download_file(self, file_id: str, file_name: str, export_mime_type: Optional[str] = None) -> Optional[bytes]:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            file_name: File name (for logging)
            export_mime_type: MIME type for Google Docs export (e.g., 'text/plain')
        
        Returns:
            File content as bytes, or None on error
        """
        try:
            if export_mime_type:
                # Google Docs files need to be exported
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            else:
                # Regular files can be downloaded directly
                request = self.service.files().get_media(fileId=file_id)
            
            file_content = request.execute()
            return file_content
        except HttpError as e:
            logger.error(f"Error downloading file {file_name} ({file_id}): {e}")
            return None
    
    def _should_sync_file(self, file_id: str, modified_time: str, file_hash: Optional[str] = None) -> bool:
        """Check if file should be synced (new or modified)."""
        # Check if file is new
        if file_id not in self.sync_state['file_hashes']:
            return True
        
        # Check if file was modified
        stored_version = self.sync_state['file_versions'].get(file_id)
        if stored_version != modified_time:
            return True
        
        # If hash provided, check if content changed
        if file_hash and self.sync_state['file_hashes'].get(file_id) != file_hash:
            return True
        
        return False
    
    async def sync_folder(self, folder_name: str, tier: str) -> Dict[str, int]:
        """
        Sync a Google Drive folder to RAG memory tier.
        
        Args:
            folder_name: Name of Google Drive folder (e.g., 'JARVIS-Core')
            tier: Memory tier ('core', 'reference', or 'ephemeral')
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'files_found': 0,
            'files_synced': 0,
            'files_skipped': 0,
            'chunks_ingested': 0,
            'errors': 0
        }
        
        logger.info(f"📁 Syncing folder '{folder_name}' → tier '{tier}'...")
        
        # Find folder
        folder_id = self._find_folder_by_name(folder_name)
        if not folder_id:
            logger.warning(f"   ⚠️  Folder '{folder_name}' not found, skipping")
            return stats
        
        # List files
        files = self._list_files_in_folder(folder_id)
        stats['files_found'] = len(files)
        logger.info(f"   Found {len(files)} file(s)")
        
        if not files:
            return stats
        
        # Create temp directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files_to_ingest = []
            
            for file_item in files:
                file_id = file_item['id']
                file_name = file_item['name']
                modified_time = file_item.get('modifiedTime', '')
                
                # Check if file should be synced
                if not self._should_sync_file(file_id, modified_time):
                    stats['files_skipped'] += 1
                    logger.debug(f"   ⏭️  Skipping unchanged: {file_name}")
                    continue
                
                # Download file
                logger.info(f"   📥 Downloading: {file_name}")
                export_mime_type = file_item.get('export_mime_type')
                file_content = self._download_file(file_id, file_name, export_mime_type)
                
                if not file_content:
                    stats['errors'] += 1
                    continue
                
                # Calculate hash
                file_hash = self._get_file_hash(file_content)
                
                # Save to temp file
                # For Google Docs, use .txt extension
                if export_mime_type:
                    ext = '.txt'
                else:
                    ext = Path(file_name).suffix or '.txt'
                temp_file = temp_path / f"{file_id}{ext}"
                temp_file.write_bytes(file_content)
                
                files_to_ingest.append({
                    'path': str(temp_file),
                    'file_id': file_id,
                    'file_name': file_name,
                    'hash': file_hash,
                    'modified_time': modified_time
                })
            
            # Ingest files into RAG
            if files_to_ingest:
                logger.info(f"   📝 Ingesting {len(files_to_ingest)} file(s) into tier '{tier}'...")
                
                file_paths = [f['path'] for f in files_to_ingest]
                
                # Determine TTL for ephemeral tier
                ttl_seconds = None
                if tier == 'ephemeral':
                    # Default: 30 days for ephemeral
                    ttl_seconds = 30 * 24 * 60 * 60
                
                result = await self.rag_server.ingest_documents(
                    file_paths,
                    tier=tier,
                    ttl_seconds=ttl_seconds,
                    metadata={'source': 'google_drive', 'folder': folder_name}
                )
                
                if result['success']:
                    stats['chunks_ingested'] = result['chunks_ingested']
                    stats['files_synced'] = len(files_to_ingest)
                    
                    # Update sync state
                    for file_info in files_to_ingest:
                        self.sync_state['file_hashes'][file_info['file_id']] = file_info['hash']
                        self.sync_state['file_versions'][file_info['file_id']] = file_info['modified_time']
                    
                    logger.info(f"   ✅ Ingested {result['chunks_ingested']} chunks from {len(files_to_ingest)} file(s)")
                else:
                    stats['errors'] += len(files_to_ingest)
                    logger.error(f"   ❌ Ingestion failed: {result.get('message', 'Unknown error')}")
        
        return stats
    
    async def sync_all(self) -> Dict[str, any]:
        """
        Sync all configured Google Drive folders.
        
        Returns:
            Dictionary with overall sync statistics
        """
        if not self.service:
            logger.error("❌ Not authenticated. Run authenticate() first.")
            return {}
        
        logger.info("="*60)
        logger.info("Starting Google Drive Sync")
        logger.info("="*60)
        
        overall_stats = {
            'folders_synced': 0,
            'total_files_found': 0,
            'total_files_synced': 0,
            'total_files_skipped': 0,
            'total_chunks_ingested': 0,
            'total_errors': 0,
            'folder_stats': {}
        }
        
        # Sync each folder
        for folder_name, tier in FOLDER_TIER_MAP.items():
            stats = await self.sync_folder(folder_name, tier)
            
            overall_stats['folders_synced'] += 1
            overall_stats['total_files_found'] += stats['files_found']
            overall_stats['total_files_synced'] += stats['files_synced']
            overall_stats['total_files_skipped'] += stats['files_skipped']
            overall_stats['total_chunks_ingested'] += stats['chunks_ingested']
            overall_stats['total_errors'] += stats['errors']
            overall_stats['folder_stats'][folder_name] = stats
        
        # Update last sync time
        self.sync_state['last_sync'] = datetime.now().isoformat()
        self._save_sync_state()
        
        # Print summary
        logger.info("="*60)
        logger.info("Sync Summary")
        logger.info("="*60)
        logger.info(f"Folders synced: {overall_stats['folders_synced']}")
        logger.info(f"Files found: {overall_stats['total_files_found']}")
        logger.info(f"Files synced: {overall_stats['total_files_synced']}")
        logger.info(f"Files skipped (unchanged): {overall_stats['total_files_skipped']}")
        logger.info(f"Chunks ingested: {overall_stats['total_chunks_ingested']}")
        logger.info(f"Errors: {overall_stats['total_errors']}")
        
        if overall_stats['total_errors'] == 0:
            logger.info("✅ Sync completed successfully")
        else:
            logger.warning(f"⚠️  Sync completed with {overall_stats['total_errors']} error(s)")
        
        return overall_stats


async def main():
    """Main entry point for Google Drive sync."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sync Google Drive folders to Mini-JARVIS RAG memory"
    )
    parser.add_argument(
        "--credentials",
        type=str,
        default="credentials.json",
        help="Path to OAuth 2.0 credentials file (default: credentials.json)"
    )
    parser.add_argument(
        "--token",
        type=str,
        default="token.json",
        help="Path to OAuth token file (default: token.json)"
    )
    parser.add_argument(
        "--sync-state",
        type=str,
        default=".drive_sync_state.json",
        help="Path to sync state file (default: .drive_sync_state.json)"
    )
    parser.add_argument(
        "--memory-dir",
        type=str,
        default=None,
        help="Directory for RAG memory (default: ~/.jarvis/memory)"
    )
    parser.add_argument(
        "--folder",
        type=str,
        choices=list(FOLDER_TIER_MAP.keys()),
        help="Sync only a specific folder (default: sync all folders)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without actually syncing"
    )
    
    args = parser.parse_args()
    
    # Initialize sync
    sync = GoogleDriveSync(
        credentials_file=args.credentials,
        token_file=args.token,
        sync_state_file=args.sync_state,
        memory_dir=args.memory_dir
    )
    
    # Authenticate
    if not sync._authenticate():
        return 1
    
    # Dry run
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be synced")
        # TODO: Implement dry run logic
        return 0
    
    # Sync
    if args.folder:
        # Sync single folder
        tier = FOLDER_TIER_MAP[args.folder]
        stats = await sync.sync_folder(args.folder, tier)
        sync._save_sync_state()
    else:
        # Sync all folders
        stats = await sync.sync_all()
    
    return 0 if stats.get('total_errors', 0) == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

