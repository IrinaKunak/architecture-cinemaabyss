import os
from pydantic import BaseModel

class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", "8082"))
    KAFKA_BROKERS: str = os.getenv("KAFKA_BROKERS", "kafka:9092")

    TOPIC_MOVIE: str = os.getenv("TOPIC_MOVIE", "movie-events")
    TOPIC_USER: str = os.getenv("TOPIC_USER", "user-events")
    TOPIC_PAYMENT: str = os.getenv("TOPIC_PAYMENT", "payment-events")

settings = Settings()