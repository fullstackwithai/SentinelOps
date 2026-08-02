from collections import Counter, defaultdict
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.models import SecurityEvent


def failed_login_spikes(db: Session) -> dict:
    rows = db.query(SecurityEvent).filter(SecurityEvent.outcome == "failure").all()
    by_user = Counter(row.user for row in rows)
    by_ip = Counter(row.source_ip for row in rows)
    return {
        "failed_events": len(rows),
        "top_users": by_user.most_common(5),
        "top_source_ips": by_ip.most_common(5),
    }


def suspicious_events(db: Session, limit: int = 20) -> list[dict]:
    rows = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.risk_label == 1)
        .order_by(SecurityEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "user": row.user,
            "source_ip": row.source_ip,
            "event_type": row.event_type,
            "country": row.country,
            "privileged": bool(row.privileged),
            "device_new": bool(row.device_new),
        }
        for row in rows
    ]


def build_timeline(db: Session, user: str | None = None, limit: int = 50) -> list[dict]:
    query = db.query(SecurityEvent)
    if user:
        query = query.filter(SecurityEvent.user == user)
    rows = query.order_by(SecurityEvent.timestamp.asc()).limit(limit).all()
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "user": row.user,
            "source_ip": row.source_ip,
            "event_type": row.event_type,
            "outcome": row.outcome,
            "country": row.country,
        }
        for row in rows
    ]


def investigation_summary(db: Session) -> dict:
    rows = db.query(SecurityEvent).all()
    high_risk = [r for r in rows if r.risk_label == 1]
    privileged = [r for r in high_risk if r.privileged]
    countries = Counter(r.country for r in high_risk)
    return {
        "total_events": len(rows),
        "high_risk_events": len(high_risk),
        "high_risk_privileged_events": len(privileged),
        "top_high_risk_countries": countries.most_common(5),
    }
