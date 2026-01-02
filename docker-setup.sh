#!/bin/bash
# Setup script for tg-archive Docker deployment

set -e

DATA_DIR="./data"

echo "=== tg-archive Docker Setup ==="
echo

# Create data directory if it doesn't exist
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory..."
    mkdir -p "$DATA_DIR"
fi

# Check for config.yaml
if [ ! -f "$DATA_DIR/config.yaml" ]; then
    echo "No config.yaml found. Initializing new site..."
    docker compose run --rm tg-archive tg-archive --new --path /tmp/example
    docker compose run --rm tg-archive cp -r /tmp/example/* /data/
    echo
    echo "Created config.yaml in $DATA_DIR"
    echo "Please edit $DATA_DIR/config.yaml with your Telegram API credentials:"
    echo "  - api_id: Your API ID from https://my.telegram.org"
    echo "  - api_hash: Your API hash from https://my.telegram.org"
    echo "  - group: The Telegram group/channel to archive"
    echo
    read -p "Press Enter after editing config.yaml to continue..."
fi

# Build the Docker image
echo "Building Docker image..."
docker compose build

# Run authentication (interactive)
echo
echo "=== Telegram Authentication ==="
echo "You will be prompted to enter your phone number and verification code."
echo "This creates a session file for future runs."
echo
docker compose run --rm tg-auth

echo
echo "=== Setup Complete ==="
echo
echo "Your session is saved. You can now run:"
echo "  docker compose up tg-archive     # Sync and build"
echo "  docker compose run tg-build      # Build only (no sync)"
echo
echo "For Portainer, use the docker-compose.yml file."
