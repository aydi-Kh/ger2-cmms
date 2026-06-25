"""Unit tests for the Predictor Agent feature extraction and RUL threshold logic."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents/predictor"))
from predictor_agent import extract_features, compute_shap_approx, FEATURE_NAMES, RUL_CRITICAL_THRESHOLD, RUL_WARNING_THRESHOLD


def _make_readings(n=48, base_value=0.3):
    return [{"value": base_value + i * 0.001, "asset_id": "test-asset"} for i in range(n)]


def test_extract_features_shape():
    readings = _make_readings(48)
    features = extract_features(readings)
    assert features.shape == (1, len(FEATURE_NAMES))


def test_extract_features_dtype():
    features = extract_features(_make_readings())
    assert features.dtype == np.float32


def test_shap_values_sum_to_one():
    features = extract_features(_make_readings())
    shap = compute_shap_approx(features, 74.0)
    assert abs(sum(shap.values()) - 1.0) < 1e-6


def test_shap_keys_match_features():
    features = extract_features(_make_readings())
    shap = compute_shap_approx(features, 74.0)
    assert set(shap.keys()) == set(FEATURE_NAMES)


@pytest.mark.parametrize("rul,expected_action", [
    (10,  "wo_critical"),
    (21,  "wo_critical"),
    (22,  "alert"),
    (60,  "alert"),
    (61,  "none"),
    (100, "none"),
])
def test_rul_thresholds(rul, expected_action):
    if rul <= RUL_CRITICAL_THRESHOLD:
        action = "wo_critical"
    elif rul <= RUL_WARNING_THRESHOLD:
        action = "alert"
    else:
        action = "none"
    assert action == expected_action
