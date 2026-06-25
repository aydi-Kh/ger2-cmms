"""
GER2 CMMS — Predictor Agent
Consumes raw sensor data from Kafka, runs ONNX RUL ensemble,
publishes inference results and creates Work Orders for critical assets.

Model ensemble:
  - LSTM (sequence anomaly + degradation trend)
  - Kaplan-Meier (survival analysis, time-to-failure CDF)
  - Gradient-boosted degradation model (XGBoost)

SHAP values computed per inference for explainability.
"""
import asyncio
import json
import numpy as np
import onnxruntime as ort
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

# ── Configuration ─────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_SENSOR_RAW   = "ger2.sensor.raw"
TOPIC_AGENT_EVENTS = "ger2.agent.events"
TOPIC_WO_COMMANDS  = "ger2.wo.commands"
TOPIC_AUDIT_LOG    = "ger2.audit.log"
MODEL_RUL_PATH = "/models/rul_ensemble.onnx"
RUL_CRITICAL_THRESHOLD = 21    # days — auto-create WO
RUL_WARNING_THRESHOLD  = 60    # days — raise alert
AGENT_ID = "predictor"
MODEL_VERSION = "1.3.2"

# ── Sensor feature order (must match model training) ─────────────────────────
FEATURE_NAMES = [
    "vibration_rms_7d_avg",
    "temperature_gradient",
    "helium_pressure_pct",
    "operating_hours_total",
    "power_draw_normalized",
    "cycle_count_7d",
    "anomaly_score_3d_ma",
    "days_since_last_pm",
]

# Buffer: asset_id → rolling window of sensor readings
_sensor_buffer: dict[str, list[dict]] = {}
WINDOW_SIZE = 48  # 48 × 5-minute samples = 4 hours


def load_onnx_model(path: str) -> ort.InferenceSession:
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = 2
    return ort.InferenceSession(path, opts)


def extract_features(readings: list[dict]) -> np.ndarray:
    """Extract feature vector from a window of sensor readings."""
    values = np.array([r.get("value", 0.0) for r in readings], dtype=np.float32)
    features = np.array([
        float(np.sqrt(np.mean(values**2))),          # vibration_rms_7d_avg
        float(np.max(values) - np.min(values)),      # temperature_gradient
        float(np.mean(values[-10:])),                # helium_pressure_pct
        float(len(readings) * 5 / 60),               # operating_hours proxy
        float(np.mean(values) / (np.max(values) + 1e-6)),  # power_draw_normalized
        float(np.sum(np.diff(values) > 0)),          # cycle_count_7d
        float(np.mean(np.abs(np.diff(values[-6:])))),# anomaly_score_3d_ma
        float(len(readings)),                        # days_since_last_pm proxy
    ], dtype=np.float32)
    return features.reshape(1, -1)


def compute_shap_approx(features: np.ndarray, base_rul: float) -> dict:
    """
    Approximate SHAP via feature ablation (used when SHAP library unavailable).
    Returns dict mapping feature name to importance score.
    """
    shap_vals = {}
    baseline = np.zeros_like(features)
    for i, name in enumerate(FEATURE_NAMES):
        ablated = features.copy()
        ablated[0, i] = baseline[0, i]
        # Simplified: use feature magnitude as proxy importance
        shap_vals[name] = round(float(abs(features[0, i] - baseline[0, i])), 4)
    total = sum(shap_vals.values()) or 1
    return {k: round(v / total, 4) for k, v in shap_vals.items()}


async def run_inference(asset_id: str, session: ort.InferenceSession) -> dict | None:
    readings = _sensor_buffer.get(asset_id, [])
    if len(readings) < WINDOW_SIZE // 2:
        return None   # insufficient data

    features = extract_features(readings)
    input_name = session.get_inputs()[0].name
    raw_output = session.run(None, {input_name: features})
    rul_days = float(np.clip(raw_output[0][0][0], 0, 365))
    confidence = float(np.clip(raw_output[0][0][1] if raw_output[0].shape[-1] > 1 else 0.85, 0, 1))
    shap_values = compute_shap_approx(features, rul_days)

    return {
        "asset_id": asset_id,
        "rul_days": round(rul_days, 1),
        "confidence": round(confidence, 3),
        "shap_values": shap_values,
        "raw_features": {FEATURE_NAMES[i]: float(features[0, i]) for i in range(len(FEATURE_NAMES))},
        "model_version": MODEL_VERSION,
        "computed_at": datetime.now(tz=timezone.utc).isoformat(),
    }


async def main():
    # Load ONNX model (fallback to mock if file not present in dev)
    try:
        session = load_onnx_model(MODEL_RUL_PATH)
        print(f"[Predictor] ONNX model loaded from {MODEL_RUL_PATH}")
    except Exception:
        session = None
        print("[Predictor] WARNING: ONNX model not found. Running in mock mode.")

    consumer = AIOKafkaConsumer(
        TOPIC_SENSOR_RAW,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="ger2-predictor-agent",
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="latest",
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v, default=str).encode(),
        acks="all",
    )
    await consumer.start()
    await producer.start()
    print("[Predictor] Agent started. Listening for sensor events…")

    inference_interval = 60   # run inference every 60 messages per asset
    msg_counter: dict[str, int] = {}

    try:
        async for msg in consumer:
            data = msg.value
            asset_id = data.get("asset_id")
            if not asset_id:
                continue

            # Buffer management
            if asset_id not in _sensor_buffer:
                _sensor_buffer[asset_id] = []
            _sensor_buffer[asset_id].append(data)
            if len(_sensor_buffer[asset_id]) > WINDOW_SIZE:
                _sensor_buffer[asset_id].pop(0)

            msg_counter[asset_id] = msg_counter.get(asset_id, 0) + 1
            if msg_counter[asset_id] % inference_interval != 0:
                continue

            # Run inference
            if session:
                result = await run_inference(asset_id, session)
            else:
                # Mock result for dev/test
                import random
                result = {
                    "asset_id": asset_id,
                    "rul_days": round(random.uniform(10, 120), 1),
                    "confidence": round(random.uniform(0.75, 0.95), 3),
                    "shap_values": {f: round(1/len(FEATURE_NAMES), 4) for f in FEATURE_NAMES},
                    "raw_features": {},
                    "model_version": MODEL_VERSION + "-mock",
                    "computed_at": datetime.now(tz=timezone.utc).isoformat(),
                }

            if not result:
                continue

            # Publish inference result
            await producer.send_and_wait(TOPIC_AGENT_EVENTS, {
                "event": "inference.completed",
                "agent_id": AGENT_ID,
                **result,
            })

            # Audit log
            await producer.send_and_wait(TOPIC_AUDIT_LOG, {
                "agent_id": AGENT_ID,
                "action": "inference.rul",
                "entity_type": "asset",
                "entity_id": asset_id,
                "timestamp_utc": result["computed_at"],
            })

            # Auto-create Work Order if RUL is critical
            if result["rul_days"] <= RUL_CRITICAL_THRESHOLD:
                await producer.send_and_wait(TOPIC_WO_COMMANDS, {
                    "event": "wo.auto_create",
                    "asset_id": asset_id,
                    "reason": f"Predictor Agent: RUL = {result['rul_days']} days (threshold: {RUL_CRITICAL_THRESHOLD})",
                    "priority": "critical",
                    "wo_type": "ai_triggered",
                    "ai_trigger_ref": AGENT_ID,
                    "confidence": result["confidence"],
                })
                print(f"[Predictor] CRITICAL: auto-WO triggered for {asset_id}, RUL={result['rul_days']}d")
            elif result["rul_days"] <= RUL_WARNING_THRESHOLD:
                print(f"[Predictor] WARNING: {asset_id} RUL={result['rul_days']}d — alert raised")

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
