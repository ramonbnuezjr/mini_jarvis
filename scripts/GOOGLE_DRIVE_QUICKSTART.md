# Google Drive Sync - Quick Start

## One-Time Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project → Enable Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download as `credentials.json` to project root

3. **Create folders in Google Drive:**
   - `JARVIS-Core/` (important docs)
   - `JARVIS-Reference/` (reference materials)
   - `JARVIS-Ephemeral/` (temporary docs)

4. **First sync (authenticates):**
   ```bash
   python scripts/sync_google_drive.py
   ```

## Usage

**Sync all folders:**
```bash
python scripts/sync_google_drive.py
```

**Sync specific folder:**
```bash
python scripts/sync_google_drive.py --folder JARVIS-Core
```

**Dry run:**
```bash
python scripts/sync_google_drive.py --dry-run
```

## Folder → Tier Mapping

| Folder | Tier | Weight | TTL |
|--------|------|--------|-----|
| JARVIS-Core/ | `core` | 1.5x | Permanent |
| JARVIS-Reference/ | `reference` | 1.0x | Permanent |
| JARVIS-Ephemeral/ | `ephemeral` | 0.7x | 30 days |

## Features

✅ **Incremental sync** - Only downloads changed files  
✅ **Google Docs support** - Exports Docs/Sheets/Slides as text  
✅ **Version tracking** - Tracks file hashes and modification times  
✅ **Automatic tiering** - Maps folders to RAG memory tiers  

## Files Created

- `token.json` - OAuth token (auto-generated, keep private)
- `.drive_sync_state.json` - Sync state (safe to commit)

For detailed setup, see [SETUP_GOOGLE_DRIVE.md](SETUP_GOOGLE_DRIVE.md)

