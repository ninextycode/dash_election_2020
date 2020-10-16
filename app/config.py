import redis
import os


class SessionConfig:
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.Redis(
        os.environ.get("REDIS_HOST", "localhost"),
        os.environ.get("REDIS_PORT", 6379)
    )
