"""Publisher RSS/Atom/API article metadata contract."""

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


class NewsArticleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str
    title: str
    author: str | None = None
    publisher: str
    quoted_source: str | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    correction_note: str | None = None
    canonical_url: AnyHttpUrl
    feed_kind: str

    @model_validator(mode="after")
    def validate_record(self) -> "NewsArticleRecord":
        if any(not value.strip() for value in (self.article_id, self.title, self.publisher, self.feed_kind)):
            raise ValueError("article identity, title, publisher, and feed kind are required")
        for timestamp in (self.published_at, self.updated_at):
            if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ValueError("article timestamps must be timezone-aware")
        if self.updated_at is not None and self.published_at is not None and self.updated_at < self.published_at:
            raise ValueError("updated_at cannot precede published_at")
        return self
