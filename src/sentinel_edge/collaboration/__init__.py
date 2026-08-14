"""Opt-in H1 collaborative detection contracts; no transport is started here."""

from .models import (
    CorrelationDomain,
    CollaborationConsent,
    CollaborativeSignal,
    CollaborativeSignalEnvelope,
    CorrelationDecisionRecord,
)
from .factory import CollaborativeSignalFactory, MATERIAL_STATES, create_signal
from .policy import (
    CorrelationDecision,
    CollaborationPolicy,
    HazardCorrelationPolicy,
    correlate,
    evaluate_correlation,
    load_policy,
    validate_signal,
)
from .demo import run_demo
from .wire import CollaborativeInboundValidator, ValidationDecision, decode_signal_email, encode_email
from .smtp import QueuedEmail, SmtpEmailCollaborativeSignalPublisher, SmtpQueueConfig
from .gmail import GmailCollaborativeSignalConnector, PollResult
from .config import validate_collaboration_config
from .privacy import CollaborationPrivacyTransformer, coarsen_domain, pseudonymous_node_id
from .fixture import FixtureCollaborativeSignalPublisher, FixturePublishResult
from .repository import CollaborationRepository, SqliteCollaborationRepository
from .service import CollaborativeCorrelationService, CollaborativeIncidentWriter
from .metrics import CollaborationMetrics

__all__ = [
    "CorrelationDomain",
    "CollaborationConsent",
    "CollaborativeSignal",
    "CollaborativeSignalEnvelope",
    "CorrelationDecisionRecord",
    "CorrelationDecision",
    "CollaborationPolicy",
    "HazardCorrelationPolicy",
    "CollaborativeSignalFactory",
    "CollaborationPrivacyTransformer",
    "MATERIAL_STATES",
    "create_signal",
    "correlate",
    "evaluate_correlation",
    "load_policy",
    "validate_signal",
    "run_demo",
    "CollaborativeInboundValidator",
    "ValidationDecision",
    "decode_signal_email",
    "encode_email",
    "QueuedEmail",
    "SmtpEmailCollaborativeSignalPublisher",
    "SmtpQueueConfig",
    "GmailCollaborativeSignalConnector",
    "PollResult",
    "validate_collaboration_config",
    "coarsen_domain",
    "pseudonymous_node_id",
    "FixtureCollaborativeSignalPublisher",
    "FixturePublishResult",
    "CollaborationRepository",
    "SqliteCollaborationRepository",
    "CollaborativeCorrelationService",
    "CollaborativeIncidentWriter",
    "CollaborationMetrics",
]
