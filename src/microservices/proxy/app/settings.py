import os

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    MONOLITH_URL: str = os.getenv("MONOLITH_URL", "http://monolith:8080")
    MOVIES_SERVICE_URL: str = os.getenv("MOVIES_SERVICE_URL", "http://movies-service:8081")
    EVENTS_SERVICE_URL: str = os.getenv("EVENTS_SERVICE_URL", "http://events-service:8082")

    GRADUAL_MIGRATION: bool = os.getenv("GRADUAL_MIGRATION", "true").lower() == "true"
    MOVIES_MIGRATION_PERCENT: int = int(os.getenv("MOVIES_MIGRATION_PERCENT", "0"))

settings = Settings()
