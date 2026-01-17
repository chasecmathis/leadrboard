import enum
from pydantic import HttpUrl
from typing import Optional
from sqlalchemy.types import String, TypeDecorator


class FollowStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"


class SortDirection(str, enum.Enum):
    DESCENDING = "desc"
    ASCENDING = "asc"


class GameSortBy(str, enum.Enum):
    ID = "id"
    TITLE = "title"
    IGDB_ID = "igdb_id"
    RELEASE_DATE = "release_date"


class HttpUrlType(TypeDecorator):
    impl = String(
        2083
    )  # Use String in the database (2083 is a safe max length for URLs)
    cache_ok = True
    python_type = HttpUrl

    def process_bind_param(self, value: Optional[HttpUrl], dialect) -> Optional[str]:
        """Convert HttpUrl object to a string for the database."""
        if value is not None:
            return str(value)
        return None

    def process_result_value(self, value: Optional[str], dialect) -> Optional[HttpUrl]:
        """Convert string from the database back to an HttpUrl object."""
        if value is not None:
            return HttpUrl(url=value)
        return None
