"""Shared fixtures for tg-archive tests."""
import os
import tempfile
from datetime import datetime

import pytest
import pytz

from tgarchive.db import DB, User, Message, Media, Month, Day


@pytest.fixture
def sample_config():
    """Return a sample configuration dict."""
    return {
        "api_id": "123456",
        "api_hash": "test_hash",
        "group": "test_group",
        "download_avatars": True,
        "avatar_size": [64, 64],
        "download_media": False,
        "media_dir": "media",
        "media_mime_types": [],
        "proxy": {"enable": False},
        "fetch_batch_size": 2000,
        "fetch_wait": 5,
        "fetch_limit": 0,
        "publish_rss_feed": True,
        "rss_feed_entries": 100,
        "publish_dir": "site",
        "site_url": "https://example.com",
        "static_dir": "static",
        "telegram_url": "https://t.me/{id}",
        "per_page": 1000,
        "show_sender_fullname": False,
        "timezone": "",
        "site_name": "@{group} (Telegram) archive",
        "site_description": "Public archive of @{group} Telegram messages.",
        "meta_description": "@{group} {date} Telegram message archive.",
        "page_title": "{date} - @{group} Telegram message archive."
    }


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Use a unique temp file path that doesn't exist yet
    db_path = os.path.join(tempfile.gettempdir(), f"test_db_{os.getpid()}.sqlite")

    # Ensure file doesn't exist
    if os.path.exists(db_path):
        os.unlink(db_path)

    db = DB(db_path)
    yield db

    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_user():
    """Return a sample User instance."""
    return User(
        id=123,
        username="testuser",
        first_name="Test",
        last_name="User",
        tags=["bot"],
        avatar="avatar_123.jpg"
    )


@pytest.fixture
def sample_media():
    """Return a sample Media instance."""
    return Media(
        id=456,
        type="photo",
        url="456.jpg",
        title="test_photo.jpg",
        description=None,
        thumb="thumb_456.jpg"
    )


@pytest.fixture
def sample_message(sample_user, sample_media):
    """Return a sample Message instance."""
    return Message(
        id=789,
        type="message",
        date=pytz.utc.localize(datetime(2024, 1, 15, 12, 30, 0)),
        edit_date=None,
        content="Hello, this is a test message!",
        reply_to=None,
        user=sample_user,
        media=sample_media
    )


@pytest.fixture
def sample_month():
    """Return a sample Month instance."""
    return Month(
        date=pytz.utc.localize(datetime(2024, 1, 1)),
        slug="2024-01",
        label="Jan 2024",
        count=100
    )


@pytest.fixture
def sample_day():
    """Return a sample Day instance."""
    return Day(
        date=pytz.utc.localize(datetime(2024, 1, 15)),
        slug="2024-01-15",
        label="15 Jan 2024",
        count=50,
        page=1
    )


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary config file for testing."""
    import yaml

    with tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config, f)
        config_path = f.name

    yield config_path

    os.unlink(config_path)
