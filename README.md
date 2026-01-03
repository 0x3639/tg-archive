
![favicon](https://user-images.githubusercontent.com/547147/111869334-eb48f100-89a4-11eb-9c0c-bc74cdee197a.png)


**tg-archive** is a tool for exporting Telegram group chats into static websites, preserving chat history like mailing list archives.

**IMPORTANT:** I'm no longer actively maintaining or developing this tool. Can review and merge PRs (as long as they're not massive and are clearly documented).

## Preview
The [@fossunited](https://tg.fossunited.org) Telegram group archive.

![image](https://user-images.githubusercontent.com/547147/111869398-44188980-89a5-11eb-936f-01d98276ba6a.png)


## How it works
tg-archive uses the [Telethon](https://github.com/LonamiWebs/Telethon) Telegram API client to periodically sync messages from a group to a local SQLite database (file), downloading only new messages since the last sync. It then generates a static archive website of messages to be published anywhere.

## Features
- Periodically sync Telegram group messages to a local DB.
- Download user avatars locally.
- Download and embed media (files, documents, photos).
- Renders poll results.
- Use emoji alternatives in place of stickers.
- Single file Jinja HTML template for generating the static site.
- Year / Month / Day indexes with deep linking across pages.
- "In reply to" on replies with links to parent messages across pages.
- RSS / Atom feed of recent messages.

## Install
- Get [Telegram API credentials](https://my.telegram.org/auth?to=apps). Normal user account API and not the Bot API.
  - If this page produces an alert stating only "ERROR", disconnect from any proxy/vpn and try again in a different browser.

- Install with: `uv pip install tg-archive` (tested with Python 3.13.2).

### Usage

1. `tg-archive --new --path=mysite` (creates a new site. `cd` into mysite and edit `config.yaml`).
1. `tg-archive --sync` (syncs data into `data.sqlite`).
  Note: First time connection will prompt for your phone number + a Telegram auth code sent to the app. On successful auth, a `session.session` file is created. DO NOT SHARE this session file publicly as it contains the API autorization for your account.
1. `tg-archive --build` (builds the static site into the `site` directory, which can be published)

### Customization
Edit the generated `template.html` and static assets in the `./static` directory to customize the site.

### Note
- The sync can be stopped (Ctrl+C) any time to be resumed later.
- Setup a cron job to periodically sync messages and re-publish the archive.
- Downloading large media files and long message history from large groups continuously may run into Telegram API's rate limits. Watch the debug output.

## Docker / Portainer Deployment

This project includes Docker support with automatic scheduling via [Ofelia](https://github.com/mcuadros/ofelia).

### Prerequisites
- Docker and Docker Compose installed
- [Telegram API credentials](https://my.telegram.org/auth?to=apps)

### Step 1: Prepare Configuration

1. Clone or download this repository
2. Create a `data` directory and add your `config.yaml`:

```bash
mkdir -p data
tg-archive --new --path=data
```

3. Edit `data/config.yaml` with your Telegram API credentials and group settings

### Step 2: Authenticate with Telegram

First-time setup requires interactive authentication:

```bash
docker-compose --profile auth run --rm tg-auth
```

This will prompt for your phone number and Telegram auth code. Once authenticated, a `session.session` file is created in the `data` directory.

### Step 3: Deploy to Portainer

#### Option A: Using Portainer Stacks (Recommended)

1. In Portainer, go to **Stacks** → **Add stack**
2. Name your stack (e.g., `tg-archive`)
3. Choose **Repository** or **Upload** and provide the `docker-compose.yml`
4. If using Repository:
   - Repository URL: Your git repo URL
   - Compose path: `docker-compose.yml`
5. Click **Deploy the stack**

#### Option B: Using docker-compose directly

```bash
docker-compose up -d
```

### How Scheduling Works

The `docker-compose.yml` includes:

- **ofelia**: A job scheduler that runs inside Docker
- **tg-archive**: The main container that stays running

Ofelia runs two separate jobs:

- **sync**: Runs `tg-archive --sync` every minute
- **build**: Runs `tg-archive --build` once daily at midnight (UTC)

Both jobs have **no-overlap** protection - if a job is still running, the next scheduled run is skipped.

### Viewing Logs

```bash
# View Ofelia scheduler logs (shows when jobs run/skip)
docker logs -f ofelia

# View tg-archive sync/build output
docker logs -f tg-archive
```

### Changing the Schedule

Edit the cron schedules in `docker-compose.yml`:

```yaml
labels:
  # Sync schedule
  ofelia.job-exec.sync.schedule: "* * * * *"      # Every minute
  # ofelia.job-exec.sync.schedule: "*/5 * * * *"  # Every 5 minutes

  # Build schedule
  ofelia.job-exec.build.schedule: "0 0 * * *"     # Daily at midnight
  # ofelia.job-exec.build.schedule: "0 */6 * * *" # Every 6 hours
```

After changing, redeploy the stack in Portainer or run:

```bash
docker-compose up -d
```

### Accessing the Generated Site

The static site is generated in `data/site/`. You can:

- Serve it with any web server (nginx, Apache, etc.)
- Add an nginx container to the docker-compose.yml
- Copy files to your web hosting

Licensed under the MIT license.
