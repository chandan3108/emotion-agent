"""
User Sync — Discord ↔ Web Account Linking

Maps web user IDs to Discord user IDs so both interfaces share the
same CognitiveCore state in state.db.

Discord stores state as: discord_{discord_user_id}
Web defaults to:         web_{web_user_id}

When linked, the web app transparently uses the Discord key.
"""

import secrets
import string
from datetime import datetime, timezone
from typing import Dict, Any

from .db import SessionLocal
from .models import UserLink, LinkCode

def resolve_core_id(web_user_id: str) -> str:
    """
    Given a web user ID, return the CognitiveCore user_id to use.

    If the web user is linked to a Discord account → `discord_{discord_id}`
    Otherwise → `web_{web_user_id}`

    This ensures that linked users share the same state across both interfaces.
    """
    db = SessionLocal()
    try:
        row = db.query(UserLink).filter(UserLink.web_user_id == web_user_id).first()
        if row:
            return f"discord_{row.discord_id}"
        return f"web_{web_user_id}"
    except Exception:
        return f"web_{web_user_id}"
    finally:
        db.close()


def generate_link_code(discord_id: str) -> str:
    """
    Generate a 6-character alphanumeric link code for a Discord user.
    Called from the Discord bot when user runs !link.

    Returns the code string. Expires implicitly (old codes are overwritten).
    """
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    db = SessionLocal()
    try:
        # Remove any existing unused codes for this Discord user
        db.query(LinkCode).filter(LinkCode.discord_id == discord_id, LinkCode.used == 0).delete()
        new_link = LinkCode(code=code, discord_id=discord_id)
        db.add(new_link)
        db.commit()
        return code
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify_link_code(web_user_id: str, code: str) -> Dict:
    """
    Verify a link code and create the web↔Discord mapping.

    Returns:
        {"success": True, "discord_id": "..."} on success
        {"success": False, "error": "..."} on failure
    """
    code = code.strip().upper()

    db = SessionLocal()
    try:
        row = db.query(LinkCode).filter(LinkCode.code == code, LinkCode.used == 0).first()
        if not row:
            return {"success": False, "error": "Invalid or expired code"}

        discord_id = row.discord_id

        # Check if this Discord account is already linked to another web user
        existing = db.query(UserLink).filter(UserLink.discord_id == discord_id).first()
        if existing:
            return {"success": False, "error": "This Discord account is already linked"}

        # Create the link
        link = UserLink(web_user_id=web_user_id, discord_id=discord_id, linked_at=datetime.now(timezone.utc))
        db.add(link)
        # Mark code as used
        row.used = 1
        db.commit()
        return {"success": True, "discord_id": discord_id}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_link_status(web_user_id: str) -> Dict:
    """Check if a web user is linked to Discord."""
    db = SessionLocal()
    try:
        row = db.query(UserLink).filter(UserLink.web_user_id == web_user_id).first()
        if row:
            linked_at_str = row.linked_at.isoformat() if hasattr(row.linked_at, 'isoformat') else str(row.linked_at)
            return {"linked": True, "discord_id": row.discord_id, "linked_at": linked_at_str}
        return {"linked": False}
    except Exception:
        return {"linked": False}
    finally:
        db.close()


def unlink_user(web_user_id: str) -> bool:
    """Remove a web↔Discord link."""
    db = SessionLocal()
    try:
        row = db.query(UserLink).filter(UserLink.web_user_id == web_user_id).first()
        if row:
            db.delete(row)
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

