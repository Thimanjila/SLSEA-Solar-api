from datetime import datetime, timezone
import hashlib
from email.utils import parsedate_to_datetime
from fastapi import Request, Response

def make_etag(value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()
    return f'"{digest}"'

def apply_cache_headers(response: Response, etag: str, last_modified: datetime):
    response.headers["ETag"] = etag
    response.headers["Last-Modified"] = last_modified.astimezone(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.headers["Content-Type"] = "application/json"

def is_not_modified(request: Request, etag: str, last_modified: datetime) -> bool:
    inm = request.headers.get("If-None-Match")
    if inm and inm.strip() == etag:
        return True
    ims = request.headers.get("If-Modified-Since")
    if ims:
        try:
            since = parsedate_to_datetime(ims).astimezone(timezone.utc)
            return last_modified.astimezone(timezone.utc) <= since
        except (TypeError, ValueError):
            pass
    return False
