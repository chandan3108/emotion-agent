"""
User Sync — Discord ↔ Web Account Linking

Maps web user IDs to Discord user IDs so both interfaces share the
same CognitiveCore state in state.db.

Discord stores state as: discord_{discord_user_id}
Web defaults to:         web_{web_user_id}

When linked, the web app transparently uses the Discord key.
"""

from datetime import datetime, timezone
from typing import Dict

from .db import SessionLocal
from .models import UserLink

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

