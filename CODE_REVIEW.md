# Code Review: tg-archive

Senior software engineer review identifying security vulnerabilities, code quality issues, and refactoring opportunities.

**Review Date:** 2026-01-01
**Codebase Version:** v1.3.0 (commit bdee32c)

---

## Executive Summary

The codebase is functionally complete with good security hygiene in several areas (no SQL injection, no code execution vulnerabilities, no command injection). However, there are critical issues around mutable class defaults, path validation, and exception handling that should be addressed.

| Severity | Count | Examples |
|----------|-------|----------|
| Critical | 4 | Mutable class defaults, path traversal, bare excepts |
| High | 6 | Session permissions, type hints, deprecated APIs |
| Medium | 5 | Namedtuples, config validation, tight coupling |
| Low | 5 | String formatting, logging levels |

---

## Critical Issues (Fix Immediately)

### 1. Class-Level Mutable Defaults

**Files:** `tgarchive/sync.py:22-23`, `tgarchive/build.py:20-22`

```python
class Sync:
    config = {}  # DANGER: Shared across ALL instances!
    db = None
```

**Problem:** Empty dicts defined at class level are shared between all instances. If one instance modifies `config`, it affects every other instance. This is a classic Python gotcha that causes subtle, hard-to-debug issues.

**Impact:** Data corruption if multiple Sync instances are created.

**Fix:** Remove class-level attributes entirely; initialize only in `__init__`:
```python
class Sync:
    def __init__(self, config, session_file, db):
        self.config = config
        self.db = db
        # ...
```

---

### 2. Path Traversal Vulnerabilities

**Files:** `tgarchive/sync.py:329-342`, `tgarchive/build.py:150-152`, `tgarchive/__init__.py:48-52`

**Problem:** Configuration file paths (`media_dir`, `publish_dir`, `static_dir`) are not validated. An attacker who controls the config file could write files outside intended directories using `../` sequences.

```python
# sync.py:333 - media_dir comes directly from config
shutil.move(fpath, os.path.join(self.config["media_dir"], newname))

# build.py:150-152 - m.media.url from database used in path
media_path = "{}/{}".format(self.config["media_dir"], m.media.url)
```

**Impact:** Arbitrary file write if config is untrusted or database is compromised.

**Fix:** Add path validation function:
```python
import os
from pathlib import Path

def validate_path(path: str, base_dir: str = ".") -> str:
    """Ensure path doesn't escape base directory."""
    if ".." in path:
        raise ValueError(f"Path traversal detected: {path}")

    resolved = Path(base_dir).resolve() / path
    if not str(resolved).startswith(str(Path(base_dir).resolve())):
        raise ValueError(f"Path escapes base directory: {path}")

    return str(resolved)
```

---

### 3. Bare `except:` Clauses

**Files:** `tgarchive/__init__.py:112,148`, `tgarchive/build.py:163`

```python
# __init__.py:112
except:
    raise

# build.py:163
except:
    pass  # Silently swallows ALL exceptions
```

**Problem:** Bare `except:` catches everything including `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`. This makes debugging difficult and can prevent proper program termination.

**Impact:** Hard to debug errors; can prevent Ctrl+C from working.

**Fix:** Use specific exception types:
```python
# __init__.py
except (FileExistsError, OSError) as e:
    raise

# build.py
except (OSError, IOError) as e:
    logging.warning(f"Could not determine MIME type: {e}")
```

---

### 4. Unhandled None from `_fetch_messages()`

**File:** `tgarchive/sync.py:189-203`

```python
def _fetch_messages(self, group, offset_id, ids=None) -> Message:
    try:
        messages = self.client.get_messages(...)
        return messages
    except errors.FloodWaitError as e:
        logging.info(f"flood waited: have to wait {e.seconds} seconds")
        # Returns None implicitly!
```

The caller at line 56 doesn't check for None:
```python
for m in self._get_messages(...):  # Will crash if _fetch_messages returns None
```

**Impact:** Crash when Telegram rate limits the API.

**Fix:** Return empty list on error:
```python
except errors.FloodWaitError as e:
    logging.warning(f"Flood wait: {e.seconds} seconds. Returning empty batch.")
    return []
```

---

## High Priority Issues

### 5. Session File Permissions Not Enforced

**File:** `tgarchive/sync.py:102`

Session files contain Telegram authentication tokens. They are created with the default umask, which is often `0644` (world-readable).

**Impact:** On shared systems, other users could steal Telegram credentials.

**Fix:** After session file creation, restrict permissions:
```python
import os
import stat

session_path = f"{session}.session"
if os.path.exists(session_path):
    os.chmod(session_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
```

---

### 6. Incorrect Type Hints

**Files:** `tgarchive/db.py:87`, `tgarchive/sync.py:144,189,321`

```python
# db.py:87 - Invalid Python syntax
def get_last_message_id(self) -> [int, datetime]:

# sync.py:321 - Also invalid
def _download_media(self, msg) -> [str, str, str]:
```

**Problem:** `[int, datetime]` is a list literal, not a type hint. This is valid Python but doesn't mean what the author intended.

**Fix:** Use proper typing:
```python
from typing import Tuple, Optional, Iterator

def get_last_message_id(self) -> Tuple[int, Optional[datetime]]:
def _download_media(self, msg) -> Tuple[str, str, Optional[str]]:
def _get_messages(self, group, offset_id, ids=None) -> Iterator[Message]:
```

---

### 7. Deprecated `pkg_resources`

**File:** `tgarchive/build.py:5,134`

```python
import pkg_resources
# ...
pkg_resources.get_distribution("tg-archive").version
```

**Problem:** `pkg_resources` from setuptools is deprecated and slow. It's being phased out in favor of `importlib.metadata`.

**Fix:**
```python
from importlib.metadata import version

# Later:
f.generator(f"tg-archive {version('tg-archive')}")
```

---

### 8. Database Connection Never Closed

**File:** `tgarchive/db.py:69-70`

```python
self.conn = sqlite3.Connection(dbfile, ...)
# No close() method or context manager
```

**Impact:** Resource leak; database may not be properly flushed on exit.

**Fix:** Add cleanup methods:
```python
def close(self):
    if self.conn:
        self.conn.close()

def __enter__(self):
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
```

---

### 9. Incorrect `raise()` Syntax

**File:** `tgarchive/sync.py:137`

```python
raise(Exception("could not initiate takeout."))  # Python 2 style
```

**Fix:**
```python
raise Exception("could not initiate takeout.")
```

---

### 10. Using `exit()`/`quit()` Instead of `sys.exit()`

**Files:** `tgarchive/sync.py:402`, `tgarchive/build.py:44`

```python
exit(1)  # sync.py:402
quit()   # build.py:44
```

**Problem:** `exit()` and `quit()` are convenience functions for the interactive interpreter. In production code, use `sys.exit()`.

**Fix:**
```python
import sys
sys.exit(1)
```

---

## Medium Priority (Refactoring)

### 11. Namedtuples Should Be Dataclasses

**File:** `tgarchive/db.py:43-54`

```python
User = namedtuple("User", ["id", "username", "first_name", "last_name", "tags", "avatar"])
Message = namedtuple("Message", ["id", "type", "date", "edit_date", "content", "reply_to", "user", "media"])
Media = namedtuple("Media", ["id", "type", "url", "title", "description", "thumb"])
```

**Problems:**
- No type hints or validation
- No default values
- Cannot add methods
- `tags` is sometimes a list, sometimes a space-separated string (bug!)

**Fix:** Convert to dataclasses:
```python
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    avatar: Optional[str] = None

    def display_name(self) -> str:
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return name or self.username
```

---

### 12. No Configuration Validation

**File:** `tgarchive/__init__.py:48-52`

```python
def get_config(path):
    with open(path, "r") as f:
        config = {**_CONFIG, **yaml.safe_load(f.read())}
    return config
```

**Problems:**
- No validation that required fields exist
- Empty `api_id`/`api_hash` allowed
- Typos in config.yaml silently ignored
- No type checking on values

**Fix:** Add schema validation using dataclasses or Pydantic:
```python
@dataclass
class Config:
    api_id: str
    api_hash: str
    group: str
    # ... with validation in __post_init__
```

---

### 13. Mixed Responsibilities in Sync/Build Classes

The `Sync` class (416 lines) handles:
- Telegram client lifecycle
- Message fetching
- Data extraction and transformation
- Media downloading
- File I/O
- Database writes

The `Build` class (226 lines) handles:
- Template loading
- Page rendering
- RSS generation
- File system operations
- Static site generation

**Recommendation:** Extract into focused classes:
```
Sync:
├── TelegramClientManager (lifecycle)
├── MessageFetcher (API calls)
├── DataExtractor (transformation)
├── MediaDownloader (file I/O)
└── SyncOrchestrator (coordination)

Build:
├── PageRenderer (templates)
├── RSSGenerator (feeds)
├── PublishManager (file system)
└── SiteBuilder (coordination)
```

---

### 14. Telethon Client Lifecycle Issues

**File:** `tgarchive/sync.py:118-142`

```python
takeout_client = client.takeout(finalize=True).__enter__()
# ... manual __exit__ call later
def finish_takeout(self):
    self.client.__exit__(None, None, None)
```

**Problem:** Manually calling `__enter__()` and `__exit__()` bypasses Python's context manager protocol and makes resource cleanup non-obvious.

**Fix:** Create proper context manager wrapper:
```python
class TelegramClientManager:
    def __enter__(self):
        self.client = self._create_client()
        self.client.start()
        if self.use_takeout:
            self._takeout_ctx = self.client.takeout(finalize=True)
            return self._takeout_ctx.__enter__()
        return self.client

    def __exit__(self, *args):
        if self._takeout_ctx:
            self._takeout_ctx.__exit__(*args)
```

---

### 15. Hard-Coded Dependencies (Untestable)

**Files:** `tgarchive/sync.py:25-32`, `tgarchive/__init__.py:141`

```python
# sync.py - side effect in __init__
def __init__(self, config, session_file, db):
    self.client = self.new_client(session_file, config)  # Creates real client!
    if not os.path.exists(self.config["media_dir"]):
        os.mkdir(self.config["media_dir"])  # Real file I/O!
```

**Problem:** Cannot unit test without:
- Valid Telegram credentials
- Real file system
- Real SQLite database

**Fix:** Dependency injection:
```python
def __init__(self, config, db, client, media_dir_manager):
    self.config = config
    self.db = db
    self.client = client  # Injected, can be mocked
    self.media_manager = media_dir_manager
```

---

## Low Priority (Code Quality)

### 16. String Formatting Style

Throughout the codebase, `.format()` is used instead of f-strings:
```python
logging.info("fetching message id={}".format(ids))
```

**Fix:** Use f-strings for readability:
```python
logging.info(f"fetching message id={ids}")
```

---

### 17. Inconsistent Logging Levels

**File:** `tgarchive/sync.py:136`

```python
logging.info("could not initiate takeout.")  # Should be error!
```

**Fix:** Use appropriate levels:
- `info` for normal operations
- `warning` for recoverable issues
- `error` for failures
- `critical` for fatal errors

---

### 18. Missing Stack Traces in Exception Logs

**File:** `tgarchive/sync.py:317-319`

```python
except Exception as e:
    logging.error(f"error downloading media: #{msg.id}: {e}")
```

**Fix:** Use `logging.exception()` to include stack trace:
```python
except Exception:
    logging.exception(f"Error downloading media #{msg.id}")
```

---

### 19. Unbounded Config Values

**File:** `tgarchive/sync.py:86-88`

```python
time.sleep(self.config["fetch_wait"])  # Could be any value!
```

**Impact:** Malicious config could set `fetch_wait` to millions of seconds.

**Fix:** Add bounds:
```python
wait_time = min(max(self.config["fetch_wait"], 1), 3600)  # 1 sec to 1 hour
time.sleep(wait_time)
```

---

### 20. Code Duplication

MIME type detection logic exists in both `sync.py` (lines 299-304) and `build.py` (lines 156-166).

**Fix:** Extract to utility function in shared module.

---

## What's Good (No Changes Needed)

| Category | Status | Details |
|----------|--------|---------|
| SQL Injection | Safe | All queries use parameterized `?` placeholders |
| Code Execution | Safe | Uses `yaml.safe_load()`, no `eval()`/`exec()` |
| Command Injection | Safe | No shell commands constructed from user input |
| Deserialization | Safe | Uses `json.loads/dumps`, not `pickle` |
| XSS | Safe | Jinja2 templates use `autoescape=True` |

---

## Recommended Fix Order

| Priority | Issue | Effort | Files |
|----------|-------|--------|-------|
| 1 | Class-level mutable defaults | 5 min | sync.py, build.py |
| 2 | Bare except clauses | 5 min | __init__.py, build.py |
| 3 | Unhandled None return | 5 min | sync.py |
| 4 | Path validation | 30 min | sync.py, build.py, __init__.py |
| 5 | Session file permissions | 5 min | sync.py |
| 6 | Type hints | 15 min | db.py, sync.py |
| 7 | raise() syntax | 1 min | sync.py |
| 8 | exit() → sys.exit() | 2 min | sync.py, build.py |
| 9 | pkg_resources → importlib | 5 min | build.py |
| 10 | DB connection cleanup | 10 min | db.py |
| 11 | Namedtuples → dataclasses | 30 min | db.py |
| 12 | Configuration validation | 1 hr | __init__.py |
| 13+ | Architectural refactoring | 2-4 hrs | All files |

---

## Files Summary

| File | Lines | Critical | High | Medium | Low |
|------|-------|----------|------|--------|-----|
| `tgarchive/sync.py` | 416 | 2 | 3 | 4 | 3 |
| `tgarchive/build.py` | 226 | 1 | 2 | 2 | 1 |
| `tgarchive/db.py` | 260 | 0 | 2 | 1 | 0 |
| `tgarchive/__init__.py` | 164 | 1 | 0 | 1 | 1 |
