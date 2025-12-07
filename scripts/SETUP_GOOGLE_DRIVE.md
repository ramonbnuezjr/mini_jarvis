# Google Drive Sync Setup Guide

This guide walks you through setting up Google Drive sync for Mini-JARVIS RAG memory.

## Overview

The Google Drive sync automatically syncs your Google Drive folders to the tiered RAG memory system:

- **JARVIS-Core/** → `core` tier (1.5x retrieval boost)
- **JARVIS-Reference/** → `reference` tier (1.0x normal weight)
- **JARVIS-Ephemeral/** → `ephemeral` tier (0.7x weight, auto-expire after 30 days)

## Prerequisites

1. **Google Account** with Google Drive access
2. **Google Cloud Project** (free tier is sufficient)
3. **Python dependencies** installed (see below)

## Step 1: Install Dependencies

```bash
cd /home/ramon/ai_projects/mini_jarvis
source venv/bin/activate
pip install -r requirements.txt
```

This installs:
- `google-api-python-client` - Google Drive API client
- `google-auth-httplib2` - HTTP transport for authentication
- `google-auth-oauthlib` - OAuth 2.0 flow

## Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing):
   - Click "Select a project" → "New Project"
   - Name it (e.g., "Mini-JARVIS")
   - Click "Create"

## Step 3: Enable Google Drive API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Google Drive API"
3. Click on it and press **Enable**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (unless you have Google Workspace)
   - App name: "Mini-JARVIS"
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue**
   - Scopes: Click **Add or Remove Scopes**, search for "drive.readonly", check it, click **Update**
   - Test users: Add your Google account email
   - Click **Save and Continue** → **Back to Dashboard**
4. Create OAuth client:
   - Application type: **Desktop app**
   - Name: "Mini-JARVIS Drive Sync"
   - Click **Create**
5. Download credentials:
   - Click **Download JSON**
   - Save as `credentials.json` in the project root (`/home/ramon/ai_projects/mini_jarvis/`)

## Step 5: Set Up Google Drive Folders

Create the following folders in your Google Drive (at the root level):

1. **JARVIS-Core/** - Important documents (project specs, personal notes, system docs)
2. **JARVIS-Reference/** - Reference materials (research papers, manuals, tutorials)
3. **JARVIS-Ephemeral/** - Temporary documents (news articles, drafts, temp notes)

**Note:** Folder names must match exactly (case-sensitive).

## Step 6: First-Time Authentication

Run the sync script to authenticate:

```bash
cd /home/ramon/ai_projects/mini_jarvis
source venv/bin/activate
python scripts/sync_google_drive.py
```

On first run:
1. A browser window will open
2. Sign in with your Google account
3. Grant permission to "View your Google Drive files"
4. The token will be saved to `token.json` for future use

## Step 7: Run Sync

After authentication, the sync will:
- Scan all three folders
- Download new or modified files
- Ingest them into the appropriate RAG memory tier
- Track sync state (file hashes, modification times)

### Sync Options

**Sync all folders:**
```bash
python scripts/sync_google_drive.py
```

**Sync specific folder:**
```bash
python scripts/sync_google_drive.py --folder JARVIS-Core
```

**Dry run (see what would sync):**
```bash
python scripts/sync_google_drive.py --dry-run
```

**Custom paths:**
```bash
python scripts/sync_google_drive.py \
  --credentials /path/to/credentials.json \
  --token /path/to/token.json \
  --sync-state /path/to/.drive_sync_state.json \
  --memory-dir ~/.jarvis/memory
```

## How It Works

### Incremental Sync

The sync script tracks:
- **File hashes** (SHA256) - Detects content changes
- **Modification times** - Detects file updates
- **Last sync timestamp** - Stored in `.drive_sync_state.json`

Only new or modified files are downloaded and ingested, making subsequent syncs fast.

### File Support

Supported file types:
- `.txt` - Plain text
- `.md`, `.markdown` - Markdown
- `.pdf` - PDF documents
- `.docx`, `.doc` - Word documents (basic support)

### Tier Mapping

| Google Drive Folder | RAG Tier | Retrieval Weight | TTL |
|---------------------|----------|------------------|-----|
| JARVIS-Core/ | `core` | 1.5x (boosted) | Permanent |
| JARVIS-Reference/ | `reference` | 1.0x (normal) | Permanent |
| JARVIS-Ephemeral/ | `ephemeral` | 0.7x (deprioritized) | 30 days |

### Automatic Cleanup

Ephemeral documents automatically expire after 30 days (configurable in code). Use the cleanup script:

```bash
python scripts/cleanup_expired_memory.py
```

## Troubleshooting

### "Credentials file not found"

- Make sure `credentials.json` is in the project root
- Check the file path with `--credentials` argument

### "Folder not found"

- Verify folder names match exactly: `JARVIS-Core`, `JARVIS-Reference`, `JARVIS-Ephemeral`
- Check folder is at root level (not in a subfolder)
- Ensure folder is not in Trash

### "Token expired"

- Delete `token.json` and re-authenticate
- The script will prompt for re-authentication automatically

### "Permission denied"

- Make sure you granted "View your Google Drive files" permission
- Check OAuth consent screen is configured correctly
- Verify your email is in the test users list (for external apps)

### Sync is slow

- First sync downloads all files (expected)
- Subsequent syncs are incremental (only changed files)
- Large files take longer to download and process

### Files not syncing

- Check file extension is supported (`.txt`, `.md`, `.pdf`, etc.)
- Verify file is not in Trash
- Check sync state file (`.drive_sync_state.json`) for errors

## Security Notes

- **`credentials.json`** - Contains OAuth client ID/secret (not sensitive, but keep private)
- **`token.json`** - Contains access token (keep private, don't commit to git)
- **`.drive_sync_state.json`** - Contains sync metadata (safe to commit)

**Recommended:** Add to `.gitignore`:
```
credentials.json
token.json
```

## Automation (Optional)

### Cron Job

Sync daily at 2 AM:

```bash
crontab -e
```

Add:
```
0 2 * * * cd /home/ramon/ai_projects/mini_jarvis && /home/ramon/ai_projects/mini_jarvis/venv/bin/python scripts/sync_google_drive.py >> /home/ramon/ai_projects/mini_jarvis/logs/drive_sync.log 2>&1
```

### Systemd Service (Advanced)

Create `/etc/systemd/system/jarvis-drive-sync.service`:

```ini
[Unit]
Description=Mini-JARVIS Google Drive Sync
After=network.target

[Service]
Type=oneshot
User=ramon
WorkingDirectory=/home/ramon/ai_projects/mini_jarvis
ExecStart=/home/ramon/ai_projects/mini_jarvis/venv/bin/python scripts/sync_google_drive.py
StandardOutput=append:/home/ramon/ai_projects/mini_jarvis/logs/drive_sync.log
StandardError=append:/home/ramon/ai_projects/mini_jarvis/logs/drive_sync.log

[Install]
WantedBy=multi-user.target
```

Create timer `/etc/systemd/system/jarvis-drive-sync.timer`:

```ini
[Unit]
Description=Run Mini-JARVIS Drive Sync Daily
Requires=jarvis-drive-sync.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable jarvis-drive-sync.timer
sudo systemctl start jarvis-drive-sync.timer
```

## Next Steps

- Set up automated sync (cron or systemd)
- Add more file types (if needed)
- Customize TTL for ephemeral documents
- Integrate with voice commands (future enhancement)

