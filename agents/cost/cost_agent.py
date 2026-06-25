"""
GER2 CMMS — Cost Agent
Accumulates costs on WO events, computes TCO, and forecasts budget overruns.
"""
import asyncio
import json
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_WO_COMMANDS  = "ger2.wo.commands"
TOPIC_COST_EVENTS  = "ger2.cost.events"
TOPIC_AGENT_EVENTS = "ger2.agent.events"
AGENT_ID = "cost"

# Cost rates (TND — Tunisia, configurable in prod)
LABOR_RATE_PER_HOUR = 65.0
BUDGET_OVERRUN_THRESHOLD = 0.15   # 15% over budget triggers alert


async def main():
    consumer = AIOKafkaConsumer(
        TOPIC_WO_COMMANDS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="ger2-cost-agent",
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
    print("[Cost] Agent started.")

    try:
        async for msg in consumer:
            data = msg.value
            event = data.get("event")

            if event == "wo.completed":
                actual_hours = data.get("actual_hours", 0) or 0
                parts_cost   = data.get("parts_cost", 0) or 0
                labor_cost   = round(actual_hours * LABOR_RATE_PER_HOUR, 2)
                total_cost   = round(labor_cost + parts_cost, 2)
                now = datetime.now(tz=timezone.utc)
                await producer.send_and_wait(TOPIC_COST_EVENTS, {
                    "event": "cost.recorded",
                    "agent_id": AGENT_ID,
                    "wo_id":     data.get("wo_id"),
                    "asset_id":  data.get("asset_id"),
                    "center_id": data.get("center_id"),
                    "labor_cost": labor_cost,
                    "parts_cost": parts_cost,
                    "total_cost": total_cost,
                    "period_month": now.strftime("%Y-%m"),
                    "timestamp_utc": now.isoformat(),
                })
                print(f"[Cost] WO {data.get('wo_id')}: labor={labor_cost} + parts={parts_cost} = {total_cost} TND")

            elif event == "wo.created":
                # Reserve budget optimistically
                estimated_hours = data.get("estimated_hours", 4) or 4
                estimated_labor = round(estimated_hours * LABOR_RATE_PER_HOUR, 2)
                await producer.send_and_wait(TOPIC_AGENT_EVENTS, {
                    "event": "budget.reserved",
                    "agent_id": AGENT_ID,
                    "wo_id": data.get("wo_id"),
                    "estimated_cost": estimated_labor,
                    "asset_id": data.get("asset_id"),
                })
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
