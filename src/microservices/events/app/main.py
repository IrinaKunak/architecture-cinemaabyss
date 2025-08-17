import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .settings import settings
from .schemas import MovieEvent, UserEvent, PaymentEvent, Event, EventResponse
from .kafka_bus import KafkaBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("events.app")

app = FastAPI(title="Cinema Abyss Events Service")

bus = KafkaBus()

@app.on_event("startup")
async def startup_event():
    await bus.start_producer()
    await bus.start_consumer()
    logger.info("Events service started on port %s, brokers=%s", settings.PORT, settings.KAFKA_BROKERS)

@app.on_event("shutdown")
async def shutdown_event():
    await bus.stop_consumer()
    await bus.stop_producer()
    logger.info("Events service shutting down")

@app.get("/api/events/health")
async def health():
    return {"status": True}

def _wrap_event(evt_type: str, payload: dict) -> Event:
    now = datetime.now(timezone.utc)
    event_id = f"{evt_type}-{int(now.timestamp()*1000)}"
    return Event(id=event_id, type=evt_type, timestamp=now, payload=payload)

def _to_response(evt: Event, partition: int, offset: int) -> EventResponse:
    return EventResponse(status="success", partition=partition, offset=offset, event=evt)

@app.post("/api/events/movie", response_model=EventResponse, status_code=201)
async def create_movie_event(body: MovieEvent):
    evt = _wrap_event("movie", body.model_dump())
    key = f"movie:{body.movie_id}"
    partition, offset = await bus.send(settings.TOPIC_MOVIE, key=key, value=evt.model_dump())
    logger.info("Produced movie event key=%s partition=%s offset=%s", key, partition, offset)
    return _to_response(evt, partition, offset)

@app.post("/api/events/user", response_model=EventResponse, status_code=201)
async def create_user_event(body: UserEvent):
    evt = _wrap_event("user", body.model_dump())
    key = f"user:{body.user_id}"
    partition, offset = await bus.send(settings.TOPIC_USER, key=key, value=evt.model_dump())
    logger.info("Produced user event key=%s partition=%s offset=%s", key, partition, offset)
    return _to_response(evt, partition, offset)

@app.post("/api/events/payment", response_model=EventResponse, status_code=201)
async def create_payment_event(body: PaymentEvent):
    evt = _wrap_event("payment", body.model_dump())
    key = f"payment:{body.payment_id}"
    partition, offset = await bus.send(settings.TOPIC_PAYMENT, key=key, value=evt.model_dump())
    logger.info("Produced payment event key=%s partition=%s offset=%s", key, partition, offset)
    return _to_response(evt, partition, offset)
