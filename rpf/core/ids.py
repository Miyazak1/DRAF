from __future__ import annotations


def event_id(tick: int, order: int, event_type: str) -> str:
    return f"evt-{tick:04d}-{order:03d}-{event_type}"
