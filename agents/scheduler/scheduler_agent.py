"""
GER2 CMMS — Scheduler Agent
Listens for WO auto-create events, assigns technicians using constraint satisfaction,
syncs maintenance windows with HL7 FHIR R4 Schedule/Slot resources.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import httpx

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_WO_COMMANDS  = "ger2.wo.commands"
TOPIC_AGENT_EVENTS = "ger2.agent.events"
FHIR_URL = "http://fhir:8080/fhir"
AGENT_ID = "scheduler"

# Simple technician pool (in production, loaded from DB)
TECHNICIAN_POOL = [
    {"id": "tech-001", "name": "Rami Mansouri",   "speciality": ["MRI", "CT"],    "center": "center-a"},
    {"id": "tech-002", "name": "Sami Bejaoui",    "speciality": ["CT", "X-Ray"],  "center": "center-a"},
    {"id": "tech-003", "name": "Hichem Trabelsi", "speciality": ["MRI"],          "center": "center-b"},
    {"id": "tech-004", "name": "Anis Khelil",     "speciality": ["General"],      "center": "center-c"},
]


def assign_technician(asset_id: str, center_id: str) -> dict:
    """Simple constraint satisfaction: match technician by center and asset type."""
    category_hint = asset_id.split("-")[1].upper() if "-" in asset_id else "General"
    candidates = [
        t for t in TECHNICIAN_POOL
        if t["center"] == center_id or any(category_hint in s for s in t["speciality"])
    ]
    return candidates[0] if candidates else TECHNICIAN_POOL[0]


async def create_fhir_slot(asset_id: str, start_dt: datetime, duration_hours: float = 4.0) -> str:
    """Create a FHIR R4 Schedule + Slot resource for the maintenance window."""
    end_dt = start_dt + timedelta(hours=duration_hours)
    slot_resource = {
        "resourceType": "Slot",
        "status": "busy-tentative",
        "serviceType": [{"text": "Biomedical Equipment Maintenance"}],
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "comment": f"Scheduled maintenance — {asset_id}",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(f"{FHIR_URL}/Slot", json=slot_resource,
                                     headers={"Content-Type": "application/fhir+json"})
            resp.raise_for_status()
            return resp.json().get("id", "unknown")
        except Exception as exc:
            print(f"[Scheduler] FHIR Slot creation failed: {exc}")
            return "fhir-unavailable"


async def main():
    consumer = AIOKafkaConsumer(
        TOPIC_WO_COMMANDS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="ger2-scheduler-agent",
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
    print("[Scheduler] Agent started.")

    try:
        async for msg in consumer:
            data = msg.value
            if data.get("event") != "wo.auto_create":
                continue
            asset_id  = data.get("asset_id")
            center_id = data.get("center_id", "center-a")

            # Assign technician
            tech = assign_technician(asset_id, center_id)
            # Schedule 4 hours from now
            start_dt = datetime.now(tz=timezone.utc) + timedelta(hours=1)
            fhir_slot_id = await create_fhir_slot(asset_id, start_dt)

            await producer.send_and_wait(TOPIC_AGENT_EVENTS, {
                "event": "wo.scheduled",
                "agent_id": AGENT_ID,
                "asset_id": asset_id,
                "assigned_technician_id": tech["id"],
                "assigned_technician_name": tech["name"],
                "scheduled_start": start_dt.isoformat(),
                "fhir_slot_id": fhir_slot_id,
                "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            })
            print(f"[Scheduler] WO scheduled for {asset_id} → {tech['name']} at {start_dt}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
