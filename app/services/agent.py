import re
from sqlalchemy.orm import Session
from app.core.models import InvestigationMessage
from app.services.ml_service import predict, train_model
from app.services.retrieval import search_playbooks
from app.services.security_analytics import build_timeline, failed_login_spikes, investigation_summary, suspicious_events


def _save(db: Session, session_id: str, role: str, content: str) -> None:
    db.add(InvestigationMessage(session_id=session_id, role=role, content=content))
    db.commit()


def _sample_features() -> dict:
    return {"failed_logins": 12, "unique_source_ips": 6, "privileged": 1, "device_new": 1, "off_hours": 1, "geo_velocity": 1}


def run_agent(db: Session, session_id: str, message: str) -> tuple[str, list[dict]]:
    _save(db, session_id, "user", message)
    text = message.lower()
    traces: list[dict] = []

    if "failed" in text and ("login" in text or "authentication" in text):
        result = failed_login_spikes(db)
        traces.append({"tool": "security_analytics", "summary": "Analyzed failed authentication events by user and source IP.", "evidence": result})
        answer = f"I found {result['failed_events']} failed authentication events. The most affected users are {result['top_users'][:3]}, and the leading source IPs are {result['top_source_ips'][:3]}."
    elif "timeline" in text:
        match = re.search(r"user\s+([\w.@-]+)", message, re.I)
        user = match.group(1) if match else None
        result = build_timeline(db, user=user)
        traces.append({"tool": "timeline_builder", "summary": "Built a chronological event timeline.", "evidence": {"user": user, "events": result[:10], "count": len(result)}})
        answer = f"I built a timeline containing {len(result)} events" + (f" for {user}." if user else ".")
    elif "playbook" in text or "contain" in text or "credential" in text:
        results = search_playbooks(db, message)
        traces.append({"tool": "playbook_retrieval", "summary": "Retrieved relevant incident-response guidance.", "evidence": {"matches": results}})
        answer = "The most relevant playbook guidance is: " + (results[0]["excerpt"] if results else "No indexed playbook matched the request.")
    elif "train" in text and "model" in text:
        result = train_model()
        traces.append({"tool": "ml_training", "summary": "Trained and evaluated the alert-risk classifier.", "evidence": result})
        answer = f"The classifier trained on {result['rows']} synthetic rows with ROC-AUC {result['roc_auc']} and F1 {result['f1']}."
    elif "predict" in text or "malicious" in text or "risk" in text:
        result = predict(_sample_features())
        traces.append({"tool": "alert_risk_model", "summary": "Scored a representative suspicious authentication alert.", "evidence": result})
        answer = f"The sample alert has a {result['malicious_probability']:.1%} malicious probability and is classified as {result['severity']}. Recommended action: {result['recommended_action']}"
    elif "suspicious" in text or "high risk" in text:
        result = suspicious_events(db)
        traces.append({"tool": "event_triage", "summary": "Retrieved recent high-risk security events.", "evidence": {"events": result, "count": len(result)}})
        answer = f"I found {len(result)} recent high-risk events. Review the evidence trace for users, IPs, countries, and event types."
    else:
        result = investigation_summary(db)
        traces.append({"tool": "investigation_summary", "summary": "Summarized the current security-event dataset.", "evidence": result})
        answer = f"The workspace contains {result['total_events']} events, including {result['high_risk_events']} high-risk events and {result['high_risk_privileged_events']} high-risk privileged-account events."

    _save(db, session_id, "assistant", answer)
    return answer, traces
