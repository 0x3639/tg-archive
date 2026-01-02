"""Tests for database module and dataclasses."""
from datetime import datetime

import pytest
import pytz

from tgarchive.db import DB, User, Message, Media, Month, Day


class TestUserDataclass:
    """Tests for User dataclass."""

    def test_create_user(self):
        """User should be created with required fields."""
        user = User(id=1, username="testuser")
        assert user.id == 1
        assert user.username == "testuser"

    def test_user_defaults(self):
        """User should have correct default values."""
        user = User(id=1, username="testuser")
        assert user.first_name is None
        assert user.last_name is None
        assert user.tags == ""
        assert user.avatar is None

    def test_user_with_all_fields(self):
        """User should accept all fields."""
        user = User(
            id=1,
            username="testuser",
            first_name="Test",
            last_name="User",
            tags=["bot", "verified"],
            avatar="avatar.jpg"
        )
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.tags == ["bot", "verified"]
        assert user.avatar == "avatar.jpg"

    def test_display_name_with_full_name(self):
        """display_name should return full name when available."""
        user = User(id=1, username="testuser", first_name="Test", last_name="User")
        assert user.display_name() == "Test User"

    def test_display_name_with_first_name_only(self):
        """display_name should return first name when last name missing."""
        user = User(id=1, username="testuser", first_name="Test")
        assert user.display_name() == "Test"

    def test_display_name_falls_back_to_username(self):
        """display_name should return username when no name available."""
        user = User(id=1, username="testuser")
        assert user.display_name() == "testuser"


class TestMediaDataclass:
    """Tests for Media dataclass."""

    def test_create_media(self):
        """Media should be created with required fields."""
        media = Media(id=1, type="photo")
        assert media.id == 1
        assert media.type == "photo"

    def test_media_defaults(self):
        """Media should have correct default values."""
        media = Media(id=1, type="photo")
        assert media.url is None
        assert media.title is None
        assert media.description is None
        assert media.thumb is None

    def test_media_with_all_fields(self):
        """Media should accept all fields."""
        media = Media(
            id=1,
            type="photo",
            url="photo.jpg",
            title="My Photo",
            description="A nice photo",
            thumb="thumb.jpg"
        )
        assert media.url == "photo.jpg"
        assert media.title == "My Photo"
        assert media.description == "A nice photo"
        assert media.thumb == "thumb.jpg"


class TestMessageDataclass:
    """Tests for Message dataclass."""

    def test_create_message(self):
        """Message should be created with required fields."""
        now = datetime.now()
        msg = Message(id=1, type="message", date=now)
        assert msg.id == 1
        assert msg.type == "message"
        assert msg.date == now

    def test_message_defaults(self):
        """Message should have correct default values."""
        msg = Message(id=1, type="message", date=datetime.now())
        assert msg.edit_date is None
        assert msg.content is None
        assert msg.reply_to is None
        assert msg.user is None
        assert msg.media is None

    def test_message_with_nested_objects(self, sample_user, sample_media):
        """Message should accept nested User and Media objects."""
        msg = Message(
            id=1,
            type="message",
            date=datetime.now(),
            user=sample_user,
            media=sample_media
        )
        assert msg.user.username == "testuser"
        assert msg.media.type == "photo"


class TestMonthDataclass:
    """Tests for Month dataclass."""

    def test_create_month(self):
        """Month should be created with all required fields."""
        date = pytz.utc.localize(datetime(2024, 1, 1))
        month = Month(date=date, slug="2024-01", label="Jan 2024", count=100)
        assert month.slug == "2024-01"
        assert month.label == "Jan 2024"
        assert month.count == 100


class TestDayDataclass:
    """Tests for Day dataclass."""

    def test_create_day(self):
        """Day should be created with all required fields."""
        date = pytz.utc.localize(datetime(2024, 1, 15))
        day = Day(date=date, slug="2024-01-15", label="15 Jan 2024", count=50, page=1)
        assert day.slug == "2024-01-15"
        assert day.count == 50
        assert day.page == 1


class TestDBLifecycle:
    """Tests for DB connection lifecycle."""

    def test_db_creates_tables(self, temp_db):
        """DB should create tables on initialization."""
        # Check tables exist by querying them
        cur = temp_db.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "messages" in tables
        assert "users" in tables
        assert "media" in tables

    def test_db_close(self, temp_db):
        """DB close should close the connection."""
        temp_db.close()
        assert temp_db.conn is None

    def test_db_context_manager(self):
        """DB should work as context manager."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name

        try:
            with DB(db_path) as db:
                assert db.conn is not None
            # After context exit, connection should be closed
            assert db.conn is None
        finally:
            os.unlink(db_path)


class TestDBOperations:
    """Tests for DB CRUD operations."""

    def test_insert_and_retrieve_user(self, temp_db, sample_user):
        """User should be inserted and retrievable."""
        temp_db.insert_user(sample_user)
        temp_db.commit()

        cur = temp_db.conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (sample_user.id,))
        row = cur.fetchone()

        assert row is not None
        assert row[0] == sample_user.id
        assert row[1] == sample_user.username

    def test_insert_and_retrieve_media(self, temp_db, sample_media):
        """Media should be inserted and retrievable."""
        temp_db.insert_media(sample_media)
        temp_db.commit()

        cur = temp_db.conn.cursor()
        cur.execute("SELECT * FROM media WHERE id = ?", (sample_media.id,))
        row = cur.fetchone()

        assert row is not None
        assert row[0] == sample_media.id
        assert row[1] == sample_media.type

    def test_insert_and_retrieve_message(self, temp_db, sample_user, sample_media):
        """Message should be inserted and retrievable."""
        temp_db.insert_user(sample_user)
        temp_db.insert_media(sample_media)

        msg = Message(
            id=1,
            type="message",
            date=pytz.utc.localize(datetime(2024, 1, 15, 12, 0, 0)),
            content="Test message",
            user=sample_user,
            media=sample_media
        )
        temp_db.insert_message(msg)
        temp_db.commit()

        cur = temp_db.conn.cursor()
        cur.execute("SELECT * FROM messages WHERE id = ?", (msg.id,))
        row = cur.fetchone()

        assert row is not None
        assert row[0] == msg.id
        assert row[1] == "message"

    def test_get_last_message_id_empty(self, temp_db):
        """get_last_message_id should return (0, None) for empty DB."""
        msg_id, date = temp_db.get_last_message_id()
        assert msg_id == 0
        assert date is None

    def test_get_last_message_id(self, temp_db, sample_user):
        """get_last_message_id should return the last message ID."""
        temp_db.insert_user(sample_user)

        for i in range(1, 4):
            msg = Message(
                id=i,
                type="message",
                date=pytz.utc.localize(datetime(2024, 1, i, 12, 0, 0)),
                content=f"Message {i}",
                user=sample_user
            )
            temp_db.insert_message(msg)

        temp_db.commit()

        msg_id, date = temp_db.get_last_message_id()
        assert msg_id == 3
