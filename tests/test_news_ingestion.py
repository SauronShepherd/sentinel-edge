from datetime import datetime, timezone

import pytest

from sentinel_edge.qualification.news_ingestion import NewsArticleRecord


def test_news_record_preserves_publisher_and_correction_lineage() -> None:
    record = NewsArticleRecord(article_id="a-1", title="Flood update", author="Reporter",
        publisher="Example News", quoted_source="Hydrology Office",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc), updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        correction_note="Corrected river level", canonical_url="https://news.example/article/1", feed_kind="rss")
    assert record.publisher == "Example News"
    assert record.correction_note == "Corrected river level"
    assert str(record.canonical_url).endswith("/1")


def test_news_record_rejects_invalid_update_order() -> None:
    with pytest.raises(ValueError):
        NewsArticleRecord(article_id="a-1", title="x", publisher="p",
            published_at=datetime(2026, 1, 2, tzinfo=timezone.utc), updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            canonical_url="https://news.example/a", feed_kind="atom")
