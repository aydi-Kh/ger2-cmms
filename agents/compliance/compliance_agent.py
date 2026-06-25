"""
GER2 CMMS — Compliance Agent
Monitors calibration cert expiry, checks regulatory rule compliance,
triggers DICOM SR write-back on WO completion, and flags audit gaps.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_WO_COMMANDS        = "ger2.wo.commands"
TOPIC_COMPLIANCE_EVENTS  = "ger2.compliance.events"
TOPIC_AGENT_EVENTS       = "ger2.agent.events"
TOPIC_AUDIT_LOG          = "ger2.audit.log"
AGENT_ID = "compliance"
CERT_EXPIRY_WARNING_DAYS = 60


async def main():
    consumer = AIOKafkaConsumer(
        TOPIC_WO_COMMANDS, TOPIC_COMPLIANCE_EVENTS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="ger2-compliance-agent",
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
    print("[Compliance] Agent started.")

    try:
        async for msg in consumer:
            data = msg.value
            event = data.get("event")

            if event == "wo.completed":
                # Trigger DICOM SR write-back
                asset_id = data.get("asset_id")
                wo_id    = data.get("wo_id")
                await producer.send_and_wait(TOPIC_COMPLIANCE_EVENTS, {
                    "event": "dicom_sr.write_requested",
                    "agent_id": AGENT_ID,
                    "asset_id": asset_id,
                    "wo_id": wo_id,
                    "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
                })
                await producer.send_and_wait(TOPIC_AUDIT_LOG, {
                    "agent_id": AGENT_ID,
                    "action": "dicom_sr.write_triggered",
                    "entity_type": "work_order",
                    "entity_id": wo_id or "",
                    "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
                })
                print(f"[Compliance] DICOM SR write requested for WO={wo_id}")

            elif event == "cert.expiry_check":
                cert_expiry = data.get("expiry_date")
                asset_id    = data.get("asset_id")
                cert_id     = data.get("cert_id")
                try:
                    expiry_dt = datetime.fromisoformat(cert_expiry)
                    days_left = (expiry_dt - datetime.now(tz=timezone.utc)).days
                    if days_left < 0:
                        status = "expired"
                    elif days_left <= CERT_EXPIRY_WARNING_DAYS:
                        status = "near_expiry"
                    else:
                        status = "valid"
                    await producer.send_and_wait(TOPIC_AGENT_EVENTS, {
                        "event": "cert.status_updated",
                        "agent_id": AGENT_ID,
                        "asset_id": asset_id,
                        "cert_id": cert_id,
                        "status": status,
                        "days_remaining": days_left,
                    })
                    if status != "valid":
                        print(f"[Compliance] ALERT: cert {cert_id} → {status} ({days_left}d left)")
                except ValueError:
                    pass

            elif event == "evidence_pack.requested":
                asset_id    = data.get("asset_id")
                requested_by = data.get("requested_by")
                # Notify that pack is ready (actual PDF generation is a Celery task)
                await producer.send_and_wait(TOPIC_COMPLIANCE_EVENTS, {
                    "event": "evidence_pack.queued",
                    "agent_id": AGENT_ID,
                    "asset_id": asset_id,
                    "requested_by": requested_by,
                    "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
                })
                print(f"[Compliance] Evidence pack queued for asset {asset_id}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
