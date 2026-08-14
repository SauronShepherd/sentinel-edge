from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'src/sentinel_edge/clients/static/app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'src/sentinel_edge/clients/static/styles.css').read_text(encoding='utf-8')


def test_uix_reference_screens_are_present():
    # The ten supplied reference-screen families must remain represented in the local client.
    required = [
        "renderOverview", "renderSites", "renderDevices", "renderIncidents",
        "renderInvestigation", "renderPolicies", "renderReports",
        "renderProvisioning", "renderFirmware", "renderAutomation",
    ]
    for symbol in required:
        assert f"function {symbol}" in APP


def test_split_view_and_progressive_disclosure_patterns_are_present():
    for token in [
        'se-inspector', 'se-reports-layout', 'se-investigation-layout',
        'se-automation-layout', 'se-stepper', 'se-flow-canvas', 'se-tabs',
        'se-filterbar', 'se-bulkbar', 'se-response-actions',
    ]:
        assert token in APP or f'.{token}' in CSS


def test_global_command_palette_indexes_core_object_types():
    for group in ['Navigation', 'Sites', 'Devices', 'Incidents', 'Policies', 'Reports', 'Commands']:
        assert group in APP


def test_reference_screens_mark_fixture_only_values_truthfully():
    assert 'UI fixture' in APP
    assert 'not physical fleet uptime' in APP
    assert 'not a claim of deployed incident frequency' in APP
    assert 'not physical Raspberry Pi measurements' in APP or 'not measured Raspberry Pi' in APP
    assert 'no official warning geography' in APP


def test_responsive_reference_screen_layouts_exist():
    assert '@media(max-width:1180px)' in CSS
    assert '@media(max-width:900px)' in CSS
    assert '@media(max-width:640px)' in CSS
    for layout in ['.se-overview-layout', '.se-reports-layout', '.se-investigation-layout', '.se-automation-layout']:
        assert layout in CSS


def test_disruptive_actions_require_explicit_confirmation_and_show_blast_radius():
    assert 'window.confirm' in APP
    assert 'Expected blast radius' in APP
    assert 'id="publish-policy"' in APP
    assert 'Component 4 remains the sole incident-state authority' in APP


def test_reference_screen_interactions_are_not_static_placeholders():
    html = (ROOT / 'src/sentinel_edge/clients/static/index.html').read_text(encoding='utf-8')
    assert 'use-operator-token' in html
    assert 'data-site-tab' in APP
    assert 'data-device-tab' in APP
    assert 'device-filter-site' in APP and 'device-filter-risk' in APP
    assert '/acknowledge' in APP and 'idempotency_key' in APP
    assert 'save-report-schedule' in APP
    assert 'save-provision-draft' in APP and 'data-required="true"' in APP
    assert 'data-firmware-action' in APP
    assert 'automation-save-step' in APP and 'automationPublished' in APP


def test_mutating_incident_action_requires_operator_session_and_component5():
    assert 'sentinel-dev-operator-token' in APP
    assert 'Use the local Operator token' in APP
    assert 'Component 4 performed the authoritative mutation' in APP
