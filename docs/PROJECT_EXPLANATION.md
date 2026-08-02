# Project Explanation

**Author: Arsim Shefkiu**

SentinelOps AI is an agentic cybersecurity investigation chatbot designed to help analysts triage authentication alerts, identify suspicious patterns, retrieve incident-response guidance, and produce evidence-backed investigation summaries. The project addresses a common security-operations problem: important evidence is scattered across logs, playbooks, and analytical tools, while analysts need a fast way to correlate it without losing transparency.

The application uses FastAPI, SQLAlchemy, SQLite or PostgreSQL, pandas, scikit-learn, and a browser-based chat interface. Its agent router selects investigation tools for failed-login analysis, high-risk event triage, chronological timeline construction, playbook retrieval, model training, and alert-risk inference. Retrieval uses chunked TF-IDF search over uploaded playbooks, while the machine-learning pipeline classifies alert risk using authentication and identity features.

I designed and implemented the full project, including the backend APIs, database models, synthetic security-event dataset, agent orchestration, retrieval workflow, explainable classifier, frontend dashboard, Docker configuration, automated tests, CI workflow, and technical documentation. I also built visible tool traces into every chatbot answer so that an analyst or reviewer can inspect the evidence used rather than accepting an unsupported response.

A major challenge was making the chatbot feel agentic without hiding deterministic logic behind vague claims. I solved this by separating each capability into a bounded tool and returning structured evidence with every execution. Another challenge was demonstrating machine learning honestly, so the repository clearly labels the training data as synthetic and avoids presenting evaluation metrics as production performance. The resulting project shows how conversational AI, security analytics, retrieval, and machine learning can be integrated into one auditable workflow.
