from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ARTIFACT_DIR = Path("artifacts")
MODEL_PATH = ARTIFACT_DIR / "alert_risk_pipeline.joblib"
FEATURES = ["failed_logins", "unique_source_ips", "privileged", "device_new", "off_hours", "geo_velocity"]


def generate_training_data(n: int = 1200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    failed = rng.poisson(4.0, n)
    ips = np.maximum(1, rng.poisson(2.0, n))
    privileged = rng.binomial(1, 0.12, n)
    device_new = rng.binomial(1, 0.18, n)
    off_hours = rng.binomial(1, 0.25, n)
    geo_velocity = rng.binomial(1, 0.09, n)
    logit = -4.3 + failed * 0.38 + ips * 0.35 + privileged * 1.3 + device_new * 1.0 + off_hours * 0.75 + geo_velocity * 2.1
    probability = 1 / (1 + np.exp(-logit))
    label = rng.binomial(1, probability)
    return pd.DataFrame({
        "failed_logins": failed,
        "unique_source_ips": ips,
        "privileged": privileged,
        "device_new": device_new,
        "off_hours": off_hours,
        "geo_velocity": geo_velocity,
        "malicious": label,
    })


def train_model() -> dict:
    df = generate_training_data()
    x = df[FEATURES]
    y = df["malicious"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y)
    preprocessor = ColumnTransformer([("numeric", StandardScaler(), FEATURES)])
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)),
    ])
    pipeline.fit(x_train, y_train)
    pred = pipeline.predict(x_test)
    prob = pipeline.predict_proba(x_test)[:, 1]
    ARTIFACT_DIR.mkdir(exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    return {
        "rows": len(df),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "f1": round(float(f1_score(y_test, pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, prob)), 4),
        "artifact": str(MODEL_PATH),
        "dataset": "synthetic demonstration data",
    }


def predict(features: dict) -> dict:
    if not MODEL_PATH.exists():
        train_model()
    model = joblib.load(MODEL_PATH)
    frame = pd.DataFrame([{key: features[key] for key in FEATURES}])
    probability = float(model.predict_proba(frame)[0, 1])
    if probability >= 0.75:
        severity = "critical"
        action = "Immediately contain the account, preserve evidence, and escalate to incident response."
    elif probability >= 0.5:
        severity = "high"
        action = "Temporarily restrict access and begin analyst validation."
    elif probability >= 0.25:
        severity = "medium"
        action = "Collect additional identity, device, and network evidence."
    else:
        severity = "low"
        action = "Monitor and retain the event for correlation."
    factors = []
    labels = {
        "failed_logins": "high failed-login volume",
        "unique_source_ips": "multiple source IPs",
        "privileged": "privileged account activity",
        "device_new": "new device",
        "off_hours": "off-hours access",
        "geo_velocity": "impossible-travel pattern",
    }
    thresholds = {"failed_logins": 5, "unique_source_ips": 3, "privileged": 1, "device_new": 1, "off_hours": 1, "geo_velocity": 1}
    for key, threshold in thresholds.items():
        if features[key] >= threshold:
            factors.append(labels[key])
    return {
        "malicious_probability": round(probability, 4),
        "severity": severity,
        "contributing_factors": factors or ["no dominant high-risk factor"],
        "recommended_action": action,
    }
