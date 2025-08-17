import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from typing import Optional
from .settings import settings

logger = logging.getLogger("events.kafka")

class KafkaBus:
    def __init__(self) -> None:
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer_task: Optional[asyncio.Task] = None
        self._loop = asyncio.get_event_loop()

    async def start_producer(self):
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
            )
            await self._producer.start()
            logger.info("Kafka producer started")

    async def stop_producer(self):
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def send(self, topic: str, key: str, value: dict):
        if self._producer is None:
            await self.start_producer()
        assert self._producer
        md = await self._producer.send_and_wait(topic, value=value, key=key)
        # md: aiokafka.structs.RecordMetadata
        return md.partition, md.offset


    async def _consume_forever(self):
        consumer = AIOKafkaConsumer(
            settings.TOPIC_MOVIE,
            settings.TOPIC_USER,
            settings.TOPIC_PAYMENT,
            bootstrap_servers=settings.KAFKA_BROKERS,
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await consumer.start()
        logger.info(
            "Kafka consumer started; topics: %s, %s, %s",
            settings.TOPIC_MOVIE, settings.TOPIC_USER, settings.TOPIC_PAYMENT,
        )
        try:
            async for msg in consumer:
                logger.info(
                    "Consumed event | topic=%s partition=%s offset=%s key=%s value=%s",
                    msg.topic, msg.partition, msg.offset, msg.key.decode("utf-8") if msg.key else None, msg.value
                )
        finally:
            await consumer.stop()
            logger.info("Kafka consumer stopped")

    async def start_consumer(self):
        if self._consumer_task is None or self._consumer_task.done():
            self._consumer_task = self._loop.create_task(self._consume_forever())

    async def stop_consumer(self):
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            logger.info("Kafka consumer task cancelled")
