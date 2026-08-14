from sentinel_edge.qualification.webhook_ingestion import authorize_inbound_message


def test_enrolled_intentionally_sent_message_is_permitted() -> None:
    result = authorize_inbound_message(enrolled_number="+34123", sender_number="+34123",
        intentionally_sent=True, media_bytes_available=True)
    assert result.permitted is True
    assert result.media_bytes_available is True


def test_unsolicited_or_other_sender_is_denied() -> None:
    for kwargs in (
        {"enrolled_number": "+34123", "sender_number": "+34999", "intentionally_sent": True},
        {"enrolled_number": "+34123", "sender_number": "+34123", "intentionally_sent": False},
    ):
        result = authorize_inbound_message(**kwargs)
        assert result.permitted is False
        assert result.media_bytes_available is False
