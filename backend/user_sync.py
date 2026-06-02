"""
User Sync — Discord ↔ Web Account Linking

Maps web user IDs to Discord user IDs so both interfaces share the
same CognitiveCore state in state.db.

Discord stores state as: discord_{discord_user_id}
Web defaults to:         web_{web_user_id}

When linked, the web app transparently uses the Discord key.
"""

import os
import sqlite3
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

# Reuse the same db as StateOrchestrator
_db_dir = os.environ.get("DATABASE_DIR")
if _db_dir:
    _DB_PATH = Path(_db_dir) / "state.db"
else:
    _DB_PATH = Path(__file__).parent.parent / "state.db"


def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_links (
            web_user_id   TEXT PRIMARY KEY,
            discord_id    TEXT NOT NULL UNIQUE,
            linked_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS link_codes (
            code          TEXT PRIMARY KEY,
            discord_id    TEXT NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used          INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def resolve_core_id(web_user_id: str) -> str:
    """
    Given a web user ID, return the CognitiveCore user_id to use.

    If the web user is linked to a Discord account → `discord_{discord_id}`
    Otherwise → `web_{web_user_id}`

    This ensures that linked users share the same state across both interfaces.
    """
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT discord_id FROM user_links WHERE web_user_id = ?",
            (web_user_id,)
        ).fetchone()
        conn.close()

        if row:
            return f"discord_{row[0]}"
        return f"web_{web_user_id}"
    except Exception:
        return f"web_{web_user_id}"


def generate_link_code(discord_id: str) -> str:
    """
    Generate a 6-character alphanumeric link code for a Discord user.
    Called from the Discord bot when user runs !link.

    Returns the code string. Expires implicitly (old codes are overwritten).
    """
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    conn = _get_conn()
    # Remove any existing unused codes for this Discord user
    conn.execute("DELETE FROM link_codes WHERE discord_id = ? AND used = 0", (discord_id,))
    conn.execute(
        "INSERT INTO link_codes (code, discord_id) VALUES (?, ?)",
        (code, discord_id)
    )
    conn.commit()
    conn.close()
    return code


def verify_link_code(web_user_id: str, code: str) -> Dict:
    """
    Verify a link code and create the web↔Discord mapping.

    Returns:
        {"success": True, "discord_id": "..."} on success
        {"success": False, "error": "..."} on failure
    """
    code = code.strip().upper()

    conn = _get_conn()
    row = conn.execute(
        "SELECT discord_id FROM link_codes WHERE code = ? AND used = 0",
        (code,)
    ).fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "Invalid or expired code"}

    discord_id = row[0]

    # Check if this Discord account is already linked to another web user
    existing = conn.execute(
        "SELECT web_user_id FROM user_links WHERE discord_id = ?",
        (discord_id,)
    ).fetchone()

    if existing:
        conn.close()
        return {"success": False, "error": "This Discord account is already linked"}

    # Create the link
    try:
        conn.execute(
            "INSERT OR REPLACE INTO user_links (web_user_id, discord_id, linked_at) VALUES (?, ?, ?)",
            (web_user_id, discord_id, datetime.now(timezone.utc).isoformat())
        )
        # Mark code as used
        conn.execute("UPDATE link_codes SET used = 1 WHERE code = ?", (code,))
        conn.commit()
        conn.close()
        return {"success": True, "discord_id": discord_id}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}


def get_link_status(web_user_id: str) -> Dict:
    """Check if a web user is linked to Discord."""
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT discord_id, linked_at FROM user_links WHERE web_user_id = ?",
            (web_user_id,)
        ).fetchone()
        conn.close()

        if row:
            return {"linked": True, "discord_id": row[0], "linked_at": row[1]}
        return {"linked": False}
    except Exception:
        return {"linked": False}


def unlink_user(web_user_id: str) -> bool:
    """Remove a web↔Discord link."""
    try:
        conn = _get_conn()
        cursor = conn.execute(
            "DELETE FROM user_links WHERE web_user_id = ?",
            (web_user_id,)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception:
        return False
