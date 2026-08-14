from datetime import datetime
import json
from pathlib import Path
import pytest
from sentinel_edge.collaboration import CollaborationConsent, CollaborativeSignal, evaluate_correlation
from sentinel_edge.collaboration.wire import decode_signal_email, CollaborativeInboundValidator

ROOT=Path('fixtures/collaboration')


def _load(path):
    raw=json.loads((ROOT/path).read_text())
    now=datetime.fromisoformat(raw['evaluation_time'].replace('Z','+00:00'))
    return raw, now, [CollaborativeSignal.model_validate(item) for item in raw['signals']]

@pytest.mark.parametrize('path',[p.relative_to(ROOT) for p in (ROOT/'valid').glob('*.json')] + [p.relative_to(ROOT) for p in (ROOT/'clock').glob('*.json')] + [p.relative_to(ROOT) for p in (ROOT/'duplicate').glob('*.json')] + [p.relative_to(ROOT) for p in (ROOT/'replay').glob('*.json')] + [p.relative_to(ROOT) for p in (ROOT/'expired').glob('*.json')] + [p.relative_to(ROOT) for p in (ROOT/'domains').glob('*.json')])
def test_spec_correlation_fixtures(path):
    raw, now, signals=_load(path)
    decision=evaluate_correlation(signals,now=now,transport_trust='fixture_qualified')
    expected=raw['expected']
    assert decision.selected_action==expected['selected_action']
    if 'independent_peer_count' in expected:
        assert decision.independent_peer_count==expected['independent_peer_count']
    if 'blocking_reason' in expected:
        assert expected['blocking_reason'] in decision.blocking_reasons
    assert decision.selected_action != expected.get('must_not_action')


def test_consent_fixtures_are_valid_and_research_is_separate():
    off=CollaborationConsent.model_validate_json((ROOT/'consent/research-disabled.json').read_text())
    on=CollaborationConsent.model_validate_json((ROOT/'consent/research-enabled.json').read_text())
    assert off.sharing_enabled and not off.research_enabled
    assert on.sharing_enabled and on.research_enabled


def test_raw_eml_fixture_matrix():
    valid=decode_signal_email((ROOT/'gmail/valid-email.eml').read_bytes())
    assert valid.signal_id=='signal-gmail-valid-001'
    with pytest.raises(ValueError,match='EMAIL_TOO_LARGE'):
        decode_signal_email((ROOT/'gmail/oversized-email.eml').read_bytes())
    with pytest.raises(ValueError,match='MIME_UNSUPPORTED'):
        decode_signal_email((ROOT/'gmail/missing-json-part.eml').read_bytes())
    with pytest.raises(ValueError,match='MULTIPLE_SIGNAL_PARTS'):
        decode_signal_email((ROOT/'gmail/multiple-json-parts.eml').read_bytes())
    for name in ('invalid-json.eml','invalid-schema.eml'):
        with pytest.raises(ValueError,match='SCHEMA_INVALID'):
            decode_signal_email((ROOT/f'gmail/{name}').read_bytes())


def test_expired_email_fixture_is_rejected_semantically():
    signal=decode_signal_email((ROOT/'gmail/expired-signal.eml').read_bytes())
    decision=CollaborativeInboundValidator().validate(signal=signal,received_at=datetime.fromisoformat('2026-08-13T12:00:00+00:00'),transport_trust='email_unverified')
    assert not decision.accepted and decision.reason_code=='SIGNAL_EXPIRED'


def test_capability_record_is_h1_default_off_and_truthful():
    import yaml
    payload=yaml.safe_load(Path('provenance/collaboration/capability.yaml').read_text())
    assert payload['capability_id']=='CAP-COLLAB-001'
    assert payload['profile']=='H1' and payload['slice']=='S8'
    assert payload['default_enabled'] is False
    assert payload['state']=='implemented'
    assert payload['trust_limitations']['trusted_real_multi_node_confirmation'] is False


def test_inbound_reason_code_vocabulary_contains_spec_codes():
    from sentinel_edge.collaboration.wire import REASON_CODES
    required={
        'SCHEMA_INVALID','SCHEMA_VERSION_UNSUPPORTED','PAYLOAD_TOO_LARGE','EMAIL_TOO_LARGE',
        'MIME_UNSUPPORTED','MULTIPLE_SIGNAL_PARTS','SIGNAL_EXPIRED','SIGNAL_DUPLICATE',
        'TRANSPORT_MESSAGE_DUPLICATE','OBSERVATION_UNSUPPORTED','HAZARD_DOMAIN_MISMATCH',
        'DOMAIN_UNKNOWN','CLOCK_UNSAFE','SOURCE_MODE_REPLAYED','SOURCE_MODE_SIMULATED',
        'PEER_UNTRUSTED','CONSENT_POLICY_UNSUPPORTED','INTERNAL_ERROR',
    }
    assert required <= REASON_CODES
