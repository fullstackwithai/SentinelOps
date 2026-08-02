from tests.conftest import client


def test_health_and_stats():
    assert client.get('/api/health').json()['status'] == 'ok'
    stats = client.get('/api/stats').json()
    assert stats['events'] >= 16
    assert stats['high_risk_events'] >= 1


def test_agent_failed_login_trace():
    result = client.post('/api/chat', json={'session_id':'abc123','message':'Show failed login spikes'}).json()
    assert result['traces'][0]['tool'] == 'security_analytics'
    assert result['traces'][0]['evidence']['failed_events'] > 0


def test_playbook_retrieval():
    result = client.post('/api/chat', json={'session_id':'abc124','message':'Which playbook applies to credential compromise?'}).json()
    assert result['traces'][0]['tool'] == 'playbook_retrieval'
    assert result['traces'][0]['evidence']['matches']


def test_ml_train_and_predict():
    train = client.post('/api/ml/train').json()
    assert train['roc_auc'] > 0.75
    payload={'failed_logins':12,'unique_source_ips':6,'privileged':1,'device_new':1,'off_hours':1,'geo_velocity':1}
    pred = client.post('/api/ml/predict', json=payload).json()
    assert pred['malicious_probability'] > 0.5
    assert pred['severity'] in {'high','critical'}


def test_upload_validation():
    bad = client.post('/api/playbooks', files={'file':('bad.exe',b'x','application/octet-stream')})
    assert bad.status_code == 415
    good = client.post('/api/playbooks', files={'file':('new.md',b'# New\nContain affected identities.','text/markdown')})
    assert good.status_code == 200
