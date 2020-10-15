import redis


class SessionConfig:
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.Redis()
