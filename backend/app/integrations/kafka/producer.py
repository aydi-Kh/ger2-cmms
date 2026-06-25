"""
GER2 CMMS — Kafka Async Producer
Fire-and-forget event publishing to Kafka topics.
"""
import json
from datetime import datetime, timezone
from typing import Any
from aiokafka import AIOKafkaProducer
from app.core.config import settings
from app.core.logging import logger

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            acks="all",
            enable_idempotence=True,
            max_batch_size=65536,
            linger_ms=5,
        )
        await _producer.start()
    return _producer


async def publish_event(topic: str, payload: dict[str, Any]) -> None:
    payload.setdefault("timestamp_utc", datetime.now(tz=timezone.utc).isoformat())
    payload.setdefault("source", "ger2-cmms-backend")
    try:
        producer = await get_producer()
        await producer.send_and_wait(topic, payload)
        logger.debug("kafka.event.published", topic=topic, event=payload.get("event"))
    except Exception as exc:
        logger.error("kafka.publish.failed", topic=topic, error=str(exc))
