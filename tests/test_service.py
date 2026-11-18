"""Tests run after train.py inside the Docker 'train' stage.

They check the trained artifacts and the FastAPI endpoints required by the brief.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app

CONFIG = json.loads(Path('config.json').read_text())
METRICS = json.loads(Path('artifacts/metrics.json').read_text())
client = TestClient(app)

REQUIRED_METRIC_FIELDS = ['student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha']


def sample_record(value=0.0):
    return {feature: value for feature in CONFIG['features']}


def test_artifacts_exist():
    assert Path('artifacts/model.joblib').exists()
    assert Path('artifacts/metrics.json').exists()


def test_metrics_file_contents():
    for field in REQUIRED_METRIC_FIELDS:
        assert field in METRICS, f'missing {field}'
    assert METRICS['student_id'] == CONFIG['student_id']
    assert METRICS['training_rows'] >= 100
    assert len(METRICS['model_version']) == 12


def test_accuracy_quality_gate():
    # A model worse than this is not worth deploying.
    assert 0.60 <= METRICS['accuracy'] <= 1.0


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_metrics_endpoint():
    response = client.get('/metrics')
    assert response.status_code == 200
    body = response.json()
    for field in REQUIRED_METRIC_FIELDS:
        assert field in body


def test_predict_endpoint():
    records = [sample_record(-2.0), sample_record(0.0), sample_record(2.0)]
    response = client.post('/predict', json={'records': records})
    assert response.status_code == 200
    body = response.json()
    assert len(body['predictions']) == 3
    assert len(body['probabilities']) == 3
    assert set(body['predictions']) <= {0, 1}
    assert all(0.0 <= p <= 1.0 for p in body['probabilities'])
    # All weights are positive, so higher feature values must raise the probability.
    assert body['probabilities'][0] < body['probabilities'][2]


@pytest.mark.parametrize('records', [[], [sample_record()] * 101])
def test_predict_rejects_bad_batch_size(records):
    response = client.post('/predict', json={'records': records})
    assert response.status_code == 422
