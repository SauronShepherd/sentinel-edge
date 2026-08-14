"""Opt-in webhook inbound-message authorization contract."""

from pydantic import BaseModel, ConfigDict, model_validator


class InboundMessageDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enrolled_number: str
    sender_number: str
    intentionally_sent: bool
    permitted: bool
    code: str
    media_bytes_available: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> "InboundMessageDecision":
        if not self.enrolled_number.strip() or not self.sender_number.strip():
            raise ValueError("enrolled and sender numbers are required")
        expected = self.intentionally_sent and self.sender_number == self.enrolled_number
        if self.permitted != expected:
            raise ValueError("webhook permission must match enrollment and intent")
        if self.media_bytes_available and not self.permitted:
            raise ValueError("media bytes cannot be available for denied messages")
        return self


def authorize_inbound_message(*, enrolled_number: str, sender_number: str,
                              intentionally_sent: bool, media_bytes_available: bool = False) -> InboundMessageDecision:
    permitted = intentionally_sent and sender_number == enrolled_number
    return InboundMessageDecision(enrolled_number=enrolled_number, sender_number=sender_number,
        intentionally_sent=intentionally_sent, permitted=permitted,
        code="inbound_message_permitted" if permitted else "inbound_message_not_enrolled_or_not_intended",
        media_bytes_available=media_bytes_available if permitted else False)
