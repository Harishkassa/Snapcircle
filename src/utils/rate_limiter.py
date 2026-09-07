from src.utils import *

from src.core import settings

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=f"redis://:{settings.REDIS_PASSWORD}@cache:{settings.REDIS_PORT}"
)