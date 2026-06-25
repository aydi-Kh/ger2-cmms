"""
GER2 CMMS — Kafka Consumer (backend side)
Listens for WO commands and audit-log topics to persist data.
"""
import json
import asyncio
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.core.logging import logger
from app.core.database import get_db_context
from app.models.compliance import AuditLog
from datetime import datetime, timezone


async def _consume_audit_log():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_AUDIT_LOG,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"{settings.KAFKA_GROUP_ID}-audit",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()
    logger.info("kafka.consumer.started", topic=settings.KAFKA_TOPIC_AUDIT_LOG)
    try:
        async for msg in consumer:
            data = msg.value
            async with get_db_context() as db:
                log = AuditLog(
                    timestamp_utc=data.get("timestamp_utc", datetime.now(tz=timezone.utc).isoformat()),
                    user_id=data.get("user_id"),
                    agent_id=data.get("agent_id"),
                    action=data.get("action", "unknown"),
                    entity_type=data.get("entity_type", "unknown"),
                    entity_id=data.get("entity_id", ""),
                )
                db.add(log)
    finally:
        await consumer.stop()


async def start_consumers():
    asyncio.create_task(_consume_audit_log())
    logger.info("kafka.consumers.all_started")
