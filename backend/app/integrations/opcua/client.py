"""
GER2 CMMS — OPC-UA Client
Connects to medical equipment OPC-UA servers (IEC 62541).
Reads sensor data and publishes to Kafka for AI agent consumption.
"""
import asyncio
from typing import Optional, Callable
from opcua import Client as OPCClient, ua
from app.core.config import settings
from app.core.logging import logger
from app.integrations.kafka.producer import publish_event


class OPCUAReader:
    """
    Polls OPC-UA nodes at configured interval and publishes readings to Kafka.
    Security: Basic256Sha256 / SignAndEncrypt per IEC 62541-2.
    """

    def __init__(self, server_url: str, asset_id: str, node_ids: list[str]):
        self.server_url = server_url
        self.asset_id = asset_id
        self.node_ids = node_ids
        self._client: Optional[OPCClient] = None
        self._running = False

    async def connect(self):
        self._client = OPCClient(self.server_url)
        self._client.set_security_string(
            f"Basic256Sha256,{settings.OPCUA_SECURITY_MODE},"
            "certificates/ger2_cmms_cert.der,"
            "certificates/ger2_cmms_key.pem"
        )
        await asyncio.get_event_loop().run_in_executor(None, self._client.connect)
        logger.info("opcua.connected", server=self.server_url, asset_id=self.asset_id)

    async def disconnect(self):
        if self._client:
            await asyncio.get_event_loop().run_in_executor(None, self._client.disconnect)
            logger.info("opcua.disconnected", asset_id=self.asset_id)

    async def read_node(self, node_id: str) -> dict:
        node = self._client.get_node(node_id)
        value = await asyncio.get_event_loop().run_in_executor(None, node.get_value)
        data_value = await asyncio.get_event_loop().run_in_executor(None, node.get_data_value)
        return {
            "node_id": node_id,
            "value": value,
            "source_timestamp": str(data_value.SourceTimestamp),
            "status_code": str(data_value.StatusCode),
        }

    async def poll_loop(self, interval: int = settings.OPCUA_POLL_INTERVAL_SECONDS):
        self._running = True
        while self._running:
            for node_id in self.node_ids:
                try:
                    reading = await self.read_node(node_id)
                    await publish_event(settings.KAFKA_TOPIC_SENSOR_RAW, {
                        "event": "sensor.reading",
                        "asset_id": self.asset_id,
                        "node_id": node_id,
                        "value": reading["value"],
                        "source_timestamp": reading["source_timestamp"],
                        "quality": reading["status_code"],
                    })
                except Exception as exc:
                    logger.warning("opcua.read.failed", node_id=node_id, error=str(exc))
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
