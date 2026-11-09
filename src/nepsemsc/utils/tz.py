"""Asia/Kathmandu helpers (DC4 — UTC+5:45, NOT the familiar UTC+5:30)."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

KTM = "Asia/Kathmandu"
EXPECTED_OFFSET_MINUTES = 345  # 5 h 45 m


def now_ktm() -> datetime:
    return datetime.now(ZoneInfo(KTM))


def verify_offset() -> bool:
    """True iff the Kathmandu offset is exactly +05:45 (DC4 self-check)."""
    off = now_ktm().utcoffset()
    return off is not None and int(off.total_seconds() // 60) == EXPECTED_OFFSET_MINUTES


def utc_iso() -> str:
    """Timestamp string for manifests."""
    return datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
