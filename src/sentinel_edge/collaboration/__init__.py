"""Opt-in H1 collaborative detection contracts; no transport is started here."""

from .models import CorrelationDomain, CollaborationConsent, CollaborativeSignal
from .factory import create_signal
from .policy import CorrelationDecision, correlate, validate_signal
from .demo import run_demo

__all__ = ["CorrelationDomain", "CollaborationConsent", "CollaborativeSignal", "CorrelationDecision", "create_signal", "correlate", "validate_signal", "run_demo"]
from .wire import CollaborativeInboundValidator, ValidationDecision, decode_signal_email, encode_email
from .smtp import QueuedEmail, SmtpEmailCollaborativeSignalPublisher, SmtpQueueConfig
from .gmail import GmailCollaborativeSignalConnector, PollResult
from .config import validate_collaboration_config
from .privacy import coarsen_domain, pseudonymous_node_id
from .fixture import FixtureCollaborativeSignalPublisher, FixturePublishResult

__all__ = ["CollaborativeInboundValidator", "ValidationDecision", "decode_signal_email", "encode_email", "QueuedEmail", "SmtpEmailCollaborativeSignalPublisher", "SmtpQueueConfig", "GmailCollaborativeSignalConnector", "PollResult", "validate_collaboration_config", "coarsen_domain", "pseudonymous_node_id", "FixtureCollaborativeSignalPublisher", "FixturePublishResult"]
