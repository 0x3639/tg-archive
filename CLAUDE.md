# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

tg-archive exports Telegram group chats into static websites. It uses the Telethon Telegram API client to sync messages to a local SQLite database, then generates static HTML archives.

**Note:** This project is no longer actively maintained.

## Commands

```bash
# Install
uv pip install tg-archive

# Create new site
tg-archive --new --path=mysite

# Sync messages from Telegram to local SQLite DB
tg-archive --sync

# Build static site from synced data
tg-archive --build

# Sync specific message IDs
tg-archive --sync --id 123 456

# Sync from a specific message ID onwards
tg-archive --sync --from-id 123

# Build with symlinks instead of copying media
tg-archive --build --symlink
```

## Architecture

### Core Modules (tgarchive/)

- **`__init__.py`**: CLI entry point with argument parsing. Handles `--new`, `--sync`, and `--build` commands. Config loading via `get_config()` merges YAML with defaults.

- **`sync.py`**: `Sync` class manages Telegram API connection via Telethon. Fetches messages in batches, handles media/avatar downloads, and inserts into SQLite. Supports "takeout" mode for higher rate limits.

- **`build.py`**: `Build` class generates static HTML from SQLite data. Paginates messages by month, tracks message IDs across pages for reply linking, generates RSS/Atom feeds.

- **`db.py`**: `DB` class wraps SQLite with schema for `messages`, `users`, `media` tables. Uses namedtuples (`User`, `Message`, `Media`, `Month`, `Day`) for data structures. Handles timezone conversion via pytz.

### Data Flow

1. **Sync**: Telegram API → `Sync._get_messages()` → `DB.insert_*()` → `data.sqlite`
2. **Build**: `data.sqlite` → `DB.get_messages()` → Jinja2 template → static HTML files

### Configuration

`config.yaml` controls API credentials, fetch settings, media download options, and site generation parameters. Environment variables `API_ID` and `API_HASH` can override config values.

### Key Files per Site

- `config.yaml`: Site configuration
- `data.sqlite`: Message database
- `session.session`: Telegram auth session (DO NOT SHARE)
- `template.html`: Jinja2 template for pages
- `static/`: CSS/JS assets
- `site/`: Generated output directory
