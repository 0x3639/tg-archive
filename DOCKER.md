# Docker Setup for tg-archive

## Quick Start

### 1. Initial Setup (One-time)

```bash
# Run the setup script
./docker-setup.sh
```

This will:
- Create a `data/` directory with config.yaml template
- Prompt you to edit config.yaml with your Telegram API credentials
- Run interactive Telegram authentication
- Save session for future runs

### 2. Manual Setup

If you prefer manual setup:

```bash
# Create data directory
mkdir -p data

# Initialize config
docker compose run --rm tg-archive tg-archive --new --path /tmp/example
docker compose run --rm tg-archive cp -r /tmp/example/* /data/

# Edit data/config.yaml with your credentials
# Then authenticate with Telegram (interactive)
docker compose run --rm --profile auth tg-auth
```

## Running

### Sync and Build (default)
```bash
docker compose up tg-archive
```

### Build Only (no Telegram sync)
```bash
docker compose run --rm --profile build tg-build
```

### Sync Only
```bash
docker compose run --rm tg-archive tg-archive --sync
```

## Portainer Setup

1. In Portainer, go to **Stacks** > **Add stack**

2. Choose **Repository** and enter:
   - Repository URL: Your fork's URL
   - Compose path: `docker-compose.yml`

3. Or use **Web editor** and paste the docker-compose.yml contents

4. Before first run, you need to authenticate with Telegram locally:
   ```bash
   # On your local machine with Docker
   docker compose run --rm --profile auth tg-auth
   ```
   Then copy the `data/` directory (including `session.session`) to your Portainer host.

5. Deploy the stack in Portainer

## Scheduled Runs (Cron)

For automated archiving, add to crontab:

```bash
# Sync and build every 6 hours
0 */6 * * * cd /path/to/tg-archive && docker compose up tg-archive >> /var/log/tg-archive.log 2>&1
```

## Volume Structure

The `data/` directory contains:
```
data/
├── config.yaml      # Configuration file
├── session.session  # Telegram session (keep secure!)
├── data.sqlite      # Message database
├── media/           # Downloaded media files
├── static/          # Static assets
├── site/            # Generated HTML output
└── template.html    # HTML template
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| TZ       | UTC     | Timezone for timestamps |

## Troubleshooting

### "session.session not found" or auth errors
Re-run authentication:
```bash
docker compose run --rm --profile auth tg-auth
```

### Permission issues
Ensure data directory is writable:
```bash
chmod -R 755 data/
```

### Rebuild after code changes
```bash
docker compose build --no-cache
```
