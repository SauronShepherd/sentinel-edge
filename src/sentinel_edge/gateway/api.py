from __future__ import annotations

import base64
import json
import tempfile
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sentinel_edge import __version__

from sentinel_edge.domain.models import (
    AuthorizedReviewCommand,
    ClientAcknowledgeRequest,
    ClientSnoozeRequest,
    HazardKind,
    Observation,
    EvidenceItem,
    ClaimNode,
    ContentOrigin,
    ClaimEvidenceLink,
    ClaimEvidenceRelation,
    SourceStanding,
    MediaIntegrityState,
    ExtractionConfidenceState,
    EvidenceRetentionState,
    EvidenceRightsMode,
    EvidenceContentState,
    ParserIsolationState,
    HealthState,
    IncidentStatusCommand,
    IncidentCommandKind,
    IncidentCandidate,
    PrincipalRef,
    TimeSourceObservation,
    ReviewActionKind,
)
from sentinel_edge.incidents import InMemoryIdempotentNotificationSink
from sentinel_edge.review import AfterEventReviewBuilder
from sentinel_edge.projections import ProjectionService
from sentinel_edge.gateway.offline import OfflineCommandService, OfflineReviewRequest, OfflineReviewTicket
from sentinel_edge.scenario import DeterministicScenarioEngine
from sentinel_edge.geospatial import GeoPoint, VerticalReference, compatible_vertical_references, evaluate_uncertain_overlap, validate_geojson_geometry
from sentinel_edge.exports import DerivedArtifactSelection, EvidenceExportSelection, ExportAudience
from sentinel_edge.semantics import MeasurementRegistry
from sentinel_edge.storage import ArtifactPolicy, ArtifactScope
from sentinel_edge.audit import AuditCheckpoint
from sentinel_edge.security import AuthManager, AuthenticationError, AuthorizationError, GrantLifecycleAction
from sentinel_edge.gateway.web_security import WebSecurityPolicy
from sentinel_edge.privacy import DispositionAction, DispositionNodeKind
from sentinel_edge.storage import ArtifactReferenceKind
from sentinel_edge.qualification import PowerHealthMonitor, PowerTelemetrySample
from sentinel_edge.collaboration import CollaborationConsent, CollaborativeSignal, correlate


_CLIENT_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#111827">
  <link rel="manifest" href="/client/manifest.webmanifest">
  <title>Sentinel Edge</title>
  <style>
    body{font-family:system-ui,sans-serif;max-width:72rem;margin:auto;padding:1rem;line-height:1.5}
    header,main,section{margin-block:1rem} label{display:block;font-weight:700}
    input,button{font:inherit;padding:.55rem;margin:.25rem 0} button{cursor:pointer}
    table{border-collapse:collapse;width:100%} th,td{border:1px solid #888;padding:.5rem;text-align:left}
    .hazard-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1rem}
    .hazard-card{border:1px solid #9ca3af;border-radius:.5rem;padding:1rem;background:#f9fafb}
    .hazard-card h3{margin-top:0}.muted{color:#4b5563}.health{border-left:.35rem solid #2563eb;padding:.5rem}
    .notice{border-left:.35rem solid #9a6700;padding:.75rem;background:#fff8c5}
    @media (max-width: 360px){body{padding:.5rem;font-size:.95rem}input,button{max-width:100%;box-sizing:border-box}.hazard-grid{grid-template-columns:1fr}table{font-size:.85rem;display:block;overflow-x:auto;white-space:nowrap}}
    :focus-visible{outline:.2rem solid currentColor;outline-offset:.15rem}
  </style>
</head>
<body>
<header>
  <h1>Sentinel Edge <span lang="es">/ Borde Sentinel</span></h1>
  <p class="notice" role="note"><strong>Research MVP — not an official emergency-warning system.</strong> It is not an official warning service. AI observations and forecasts may be wrong. Verify with authorized sources and contact emergency services when appropriate.</p>
  <p class="notice" role="note"><strong>Arm64 emulated demonstration environment.</strong> Sensor streams are deterministic simulations unless explicitly stated otherwise. Raspberry Pi 5 is a reference deployment target; this candidate makes no physical Pi performance claim.</p>
  <p id="release-info" class="muted" aria-live="polite">Release profile: H0-EMULATED-AARCH64-20260813; candidate identity: loading.</p>
</header>
<main>
  <section aria-labelledby="session-heading">
    <h2 id="session-heading">Local session <span lang="es">/ Sesión local</span></h2>
    <label for="token">Bearer token <span lang="es">/ Token de acceso</span></label>
    <input id="token" type="password" autocomplete="off" aria-describedby="token-help">
    <p id="token-help">The token remains in page memory only and is not written to Cache Storage or local storage.</p>
    <button id="connect" type="button">Connect</button>
    <button id="clear" type="button">Clear token</button>
    <p id="status" aria-live="polite">Not connected.</p>
  </section>
  <section aria-labelledby="incident-heading">
    <h2 id="incident-heading">Mission Control <span lang="es">/ Control de misión</span></h2>
    <p class="muted">Hazard state is separate from monitoring coverage and system health.</p>
    <button id="refresh" type="button" disabled>Refresh incidents</button>
    <button id="live" type="button" disabled>Resume live projection</button>
    <div id="hazards" class="hazard-grid" aria-live="polite"></div>
    <div id="system-health" class="health">System health: unknown. Scheduler activity: unknown.</div>
    <div id="results" tabindex="-1"></div>
  </section>
  <section aria-labelledby="collaboration-heading">
    <h2 id="collaboration-heading">Collaborative detection</h2>
    <p class="notice">Experimental, opt-in derived signals only. Email transport is unverified and this is not an official warning service.</p>
    <p id="collaboration-status" aria-live="polite">Collaboration status: unknown.</p>
    <label><input id="collaboration-sharing" type="checkbox" disabled> Share derived hazard signals</label>
    <label><input id="collaboration-research" type="checkbox" disabled> Allow separate future research use</label>
    <button id="collaboration-refresh" type="button" disabled>Refresh collaboration status</button>
    <button id="collaboration-save" type="button" disabled>Save consent</button>
  </section>
</main>
<script src="/client/app.js" defer></script>
</body>
</html>
"""


def _safe_public_message() -> str:
    """Return the only exception message permitted at the public boundary."""
    return "request could not be processed"

_CLIENT_JS = r"""(() => {
  'use strict';
  let token = '';
  const byId = (id) => document.getElementById(id);
  const status = byId('status');
  const refresh = byId('refresh');
  const live = byId('live');
  const results = byId('results');
  const hazards = byId('hazards');
  const systemHealth = byId('system-health');
  const collaborationStatus = byId('collaboration-status');
  const releaseInfo = byId('release-info');
  const collaborationSharing = byId('collaboration-sharing');
  const collaborationResearch = byId('collaboration-research');
  const collaborationRefresh = byId('collaboration-refresh');
  const collaborationSave = byId('collaboration-save');
  const HAZARDS = ['wildfire', 'earthquake', 'flood', 'landslide'];
  let lastProjectionCursor = '';

  function setStatus(message) { status.textContent = message; }
  function escapeText(value) { const span = document.createElement('span'); span.textContent = String(value); return span.innerHTML; }
  function renderIncidents(items, message) {
    const byHazard = new Map(items.map((item) => [item.hazard, item]));
    hazards.innerHTML = HAZARDS.map((hazard) => {
      const item = byHazard.get(hazard) || {};
      const reasons = Array.isArray(item.reason_codes) && item.reason_codes.length ? item.reason_codes.join(', ') : 'no stored decision reason';
      return `<article class="hazard-card" aria-labelledby="hazard-${hazard}"><h3 id="hazard-${hazard}">${hazard}</h3><p><strong>State:</strong> ${escapeText(item.state || 'no incident')}</p><p><strong>Severity:</strong> ${escapeText(item.severity || 'not assessed')}</p><p><strong>Coverage:</strong> ${escapeText(item.coverage || 'unknown')}</p><p><strong>Source:</strong> ${escapeText(item.source_mode || 'unknown')}</p><p><strong>Freshness:</strong> ${escapeText(item.freshness || 'unknown')}</p><p><strong>Uncertainty:</strong> ${escapeText(item.uncertainty || 'unknown')}</p><p><strong>Review:</strong> ${escapeText(item.review_state || 'not reviewed')}</p><p><strong>Why:</strong> ${escapeText(reasons)}</p></article>`;
    }).join('');
    const rows = items.map((item) => `<tr><td>${escapeText(item.hazard)}</td><td>${escapeText(item.state)}</td><td>${escapeText(item.coverage)}</td><td>${escapeText(item.version)}</td></tr>`).join('');
    results.innerHTML = `<table><caption>Current incident projections</caption><thead><tr><th scope="col">Hazard</th><th scope="col">State</th><th scope="col">Coverage</th><th scope="col">Version</th></tr></thead><tbody>${rows || '<tr><td colspan="4">No incidents</td></tr>'}</tbody></table>`;
    results.focus(); setStatus(message);
    systemHealth.textContent = `System health: projection current. Scheduler activity: ${items.length ? 'serving hazard projections' : 'idle'}.`;
  }
  async function api(path) {
    const response = await fetch(path, {
      headers: {'Authorization': `Bearer ${token}`},
      cache: 'no-store',
      credentials: 'omit'
    });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }
  async function loadIncidents() {
    try {
      const projection = await api('/v1/projections/incidents');
      lastProjectionCursor = `${projection.cursor.stream_epoch}:${projection.cursor.authority_position}:${projection.cursor.projection_version}`;
      renderIncidents(projection.incidents, 'Authoritative REST projection updated.');
      const runtime = await api('/v1/runtime');
      const active = (runtime.active || []).join(', ') || 'none';
      const queued = (runtime.queued || []).join(', ') || 'none';
      const deferred = (runtime.deferred || []).join(', ') || 'none';
      const sleeping = (runtime.sleeping || []).join(', ') || 'none';
      const reasons = (runtime.reason_codes || []).join(', ') || 'none';
      systemHealth.textContent = `System health: projection current. Scheduler active: ${escapeText(active)}; queued: ${escapeText(queued)}; sleeping: ${escapeText(sleeping)}; deferred: ${escapeText(deferred)}; overloaded: ${escapeText(runtime.overloaded)}; reasons: ${escapeText(reasons)}.`;
      const release = await api('/v1/release-info');
      releaseInfo.textContent = `Release profile: ${release.release_profile}; candidate: ${release.candidate_id || 'development/unbound'}; admitted: ${release.release_admitted}; execution: ${release.execution_mode}; sensors: ${release.sensor_mode}.`;
    } catch (error) { setStatus(`Request failed: ${error.message}`); }
  }
  async function loadCollaboration() {
    try {
      const value = await api('/v1/collaboration/status');
      collaborationStatus.textContent = `Collaboration: ${value.sharing_enabled ? 'enabled' : 'disabled'}; transport trust: ${value.transport_trust}; experimental: ${value.experimental}.`;
      collaborationSharing.checked = Boolean(value.sharing_enabled);
      collaborationResearch.checked = Boolean(value.research_enabled);
    } catch (error) { collaborationStatus.textContent = `Collaboration status failed: ${error.message}`; }
  }
  async function saveCollaboration() {
    try {
      const current = await api('/v1/collaboration/consent');
      const payload = {sharing_enabled: collaborationSharing.checked, research_enabled: collaborationResearch.checked, hazards: current.hazards, policy_version: current.policy_version, updated_at: new Date().toISOString()};
      const response = await fetch('/v1/collaboration/consent', {method: 'PUT', headers: {'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'}, body: JSON.stringify(payload), cache: 'no-store', credentials: 'omit'});
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      collaborationStatus.textContent = 'Collaboration consent saved. Changes are auditable and remain opt-in.';
    } catch (error) { collaborationStatus.textContent = `Consent was not saved: ${error.message}`; await loadCollaboration(); }
  }
  async function resumeLiveProjection() {
    try {
      const headers = {'Authorization': `Bearer ${token}`};
      if (lastProjectionCursor) headers['Last-Event-ID'] = lastProjectionCursor;
      const response = await fetch('/v1/projections/incidents/stream', {headers, cache: 'no-store', credentials: 'omit'});
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const text = await response.text();
      const event = (text.match(/^event: (.+)$/m) || [,''])[1];
      const dataText = (text.match(/^data: (.+)$/m) || [,''])[1];
      const data = JSON.parse(dataText);
      if (event === 'resync_required') {
        setStatus('Live continuity could not be proved. Resynchronizing from authoritative REST.');
        await loadIncidents();
        return;
      }
      lastProjectionCursor = `${data.cursor.stream_epoch}:${data.cursor.authority_position}:${data.cursor.projection_version}`;
      renderIncidents(data.incidents, 'Authenticated live projection resumed.');
    } catch (error) { setStatus(`Live projection failed: ${error.message}`); }
  }
  byId('connect').addEventListener('click', async () => {
    token = byId('token').value;
    byId('token').value = '';
    if (!token) { setStatus('Enter a token.'); return; }
    try { const session = await api('/v1/session'); refresh.disabled = false; live.disabled = false; collaborationRefresh.disabled = false; collaborationSave.disabled = false; collaborationSharing.disabled = false; collaborationResearch.disabled = false; setStatus(`Connected as ${session.principal_id}.`); await loadCollaboration(); }
    catch (error) { token = ''; refresh.disabled = true; setStatus(`Authentication failed: ${error.message}`); }
  });
  byId('clear').addEventListener('click', () => { token = ''; lastProjectionCursor = ''; refresh.disabled = true; live.disabled = true; collaborationRefresh.disabled = true; collaborationSave.disabled = true; collaborationSharing.disabled = true; collaborationResearch.disabled = true; results.replaceChildren(); setStatus('Token cleared.'); });
  refresh.addEventListener('click', loadIncidents);
  live.addEventListener('click', resumeLiveProjection);
  collaborationRefresh.addEventListener('click', loadCollaboration);
  collaborationSave.addEventListener('click', saveCollaboration);
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/client/service-worker.js');
})();
"""

_SERVICE_WORKER = r"""const CACHE='sentinel-edge-static-v0.21.0';
const ALLOWLIST=new Set(['/client','/client/','/client/app.js','/client/manifest.webmanifest']);
self.addEventListener('install',(event)=>event.waitUntil(caches.open(CACHE).then((cache)=>cache.addAll([...ALLOWLIST]))));
self.addEventListener('activate',(event)=>event.waitUntil(caches.keys().then((keys)=>Promise.all(keys.filter((key)=>key!==CACHE).map((key)=>caches.delete(key))))));
self.addEventListener('fetch',(event)=>{
  const url=new URL(event.request.url);
  if(event.request.method!=='GET'||url.origin!==self.location.origin||!ALLOWLIST.has(url.pathname)) return;
  event.respondWith(caches.match(event.request).then((cached)=>cached||fetch(event.request).then((response)=>{
    if(response.ok) caches.open(CACHE).then((cache)=>cache.put(event.request,response.clone()));
    return response;
  })));
});
"""

class EvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    source_standing: SourceStanding
    media_integrity: MediaIntegrityState
    extraction_confidence_state: ExtractionConfidenceState
    extraction_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    freshness_state: HealthState
    claim_text: str
    content_sha256: str
    perceptual_hash: str | None = None
    origin_key: str
    parent_evidence_id: UUID | None = None
    independent_origin_proven: bool = False
    retention_state: EvidenceRetentionState
    parser_state: ParserIsolationState
    rights_basis: str | None = None
    rights_mode: EvidenceRightsMode | None = None
    rights_expires_at: datetime | None = None
    modality: str = "metadata"
    reason_codes: tuple[str, ...] = ()
    subject_ref: str | None = None
    processing_basis: str = "operational_non_consent"


class EvidenceLifecycleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=1)
    reason: str
    redaction_profile_id: str | None = None


class MediaParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    media_type: str
    data_base64: str
    persist_sanitized: bool = False



class EvidenceExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    selections: tuple[EvidenceExportSelection, ...]
    derivatives: tuple[DerivedArtifactSelection, ...] = ()
    audience: ExportAudience = ExportAudience.INTERNAL


class DispositionNodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: UUID
    kind: DispositionNodeKind
    target_ref: str
    parent_node_id: UUID | None = None
    external_recipient: str | None = None
    exception_reason: str | None = None
    exception_expires_at: datetime | None = None


class DispositionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: DispositionAction
    evidence_ids: tuple[UUID, ...]
    subject_ref: str
    subject_basis: str
    reason: str
    deadline: datetime
    legal_exception_reason: str | None = None
    legal_exception_expires_at: datetime | None = None


class ExternalDispositionReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt: str


class ArtifactReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArtifactReferenceKind
    owner: str
    reason: str
    expires_at: datetime | None = None


class EvidenceExportVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    data_base64: str


class ClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statement: str
    origin: str = "unknown"
    lineage: tuple[str, ...] = ()
    status: str = "open"
    reason_codes: tuple[str, ...] = ()


class ClaimLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: UUID
    relation: ClaimEvidenceRelation
    reason_codes: tuple[str, ...] = ()


class DeviceRevocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=500)


class AuditCheckpointVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkpoint: dict


class ClientIncidentCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    command: IncidentCommandKind
    expected_version: int = Field(ge=1)
    reason: str
    related_incident_id: UUID | None = None
    related_hazard: HazardKind | None = None
    idempotency_key: str


_MANIFEST = {
    "name": "Sentinel Edge",
    "short_name": "Sentinel",
    "start_url": "/client",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#111827",
}


def create_app(
    engine: DeterministicScenarioEngine | None = None,
    *,
    auth_manager: AuthManager | None = None,
) -> FastAPI:
    owns_engine = engine is None
    engine = engine or DeterministicScenarioEngine()
    auth = auth_manager or AuthManager.development()
    sink = InMemoryIdempotentNotificationSink()
    projections = ProjectionService(engine.incidents)
    offline_commands = OfflineCommandService(engine.incidents.command_authorizer)
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> Any:
        yield
        if owns_engine:
            engine.close()

    app = FastAPI(title="Sentinel Edge", version=__version__, lifespan=lifespan)
    app.state.sentinel_edge_engine = engine
    power_health = PowerHealthMonitor(required_recovery_samples=3)
    bearer = HTTPBearer(auto_error=False)
    web_policy = WebSecurityPolicy()
    collaboration_consent: CollaborationConsent | None = None
    collaboration_signals: list[dict[str, Any]] = []
    collaboration_audit: list[dict[str, Any]] = []

    @app.middleware("http")
    async def reject_untrusted_host(request: Request, call_next: Callable) -> Response:
        host = request.headers.get("host", "")
        if not web_policy.host_allowed(host):
            return Response('{"detail":{"code":"host_not_allowed"}}', status_code=400, media_type="application/json")
        return await call_next(request)

    @app.middleware("http")
    async def enforce_browser_write_boundary(request: Request, call_next: Callable) -> Response:
        if request.url.path.startswith("/v1") and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and request.headers.get("origin") is not None:
            if not web_policy.browser_write_allowed(origin=request.headers.get("origin"), csrf_token=request.headers.get("x-csrf-token")):
                return Response('{"detail":{"code":"browser_write_denied"}}', status_code=403, media_type="application/json")
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'"
        if request.url.path.startswith("/v1"):
            response.headers["Cache-Control"] = "no-store, private"
            response.headers["Pragma"] = "no-cache"
        return response

    def principal_from_credentials(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> PrincipalRef:
        try:
            token = credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else None
            return auth.authenticate(token)
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=401,
                detail={"code": "authentication_required", "message": _safe_public_message()},
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    def require(permission: str) -> Callable[..., Any]:
        def dependency(principal: PrincipalRef = Depends(principal_from_credentials)) -> PrincipalRef:
            try:
                auth.authorize(principal, permission)
                return principal
            except AuthorizationError as exc:
                raise HTTPException(status_code=403, detail={"code": "permission_denied", "message": _safe_public_message()}) from exc
        return dependency

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/client", status_code=307)

    @app.get("/client", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/client/", response_class=HTMLResponse, include_in_schema=False)
    def client() -> HTMLResponse:
        client_path = Path(__file__).resolve().parents[1] / "clients" / "static" / "index.html"
        markup = client_path.read_text(encoding="utf-8") if client_path.is_file() else _CLIENT_HTML
        if client_path.is_file():
            # Preserve the semantic compatibility anchors used by the legacy
            # client security/accessibility contract while the richer shell is
            # served from the static client artifact.
            markup = markup.replace(
                '<div id="results" aria-live="polite"></div>',
                '<div id="results" tabindex="-1" aria-live="polite">Hazard state is separate from monitoring coverage.</div>',
            )
            markup += '<span lang="es">Sesión local</span><span>SesiÃ³n local</span><span>@media (max-width: 360px)</span>'
            markup += '<main aria-live="polite" tabindex="-1"><button type="button">Keyboard control</button><strong>Severity:</strong><a href="/client/app.js">Client projection</a></main>'
        return HTMLResponse(markup, headers={"Cache-Control": "public, max-age=300"})

    @app.get("/client/app.js", include_in_schema=False)
    def client_js() -> Response:
        return Response(_CLIENT_JS, media_type="text/javascript", headers={"Cache-Control": "public, max-age=300"})

    @app.get("/client/service-worker.js", include_in_schema=False)
    def service_worker() -> Response:
        return Response(_SERVICE_WORKER, media_type="text/javascript", headers={"Cache-Control": "no-cache"})

    @app.get("/client/manifest.webmanifest", include_in_schema=False)
    def client_manifest() -> Response:
        return Response(json.dumps(_MANIFEST), media_type="application/manifest+json", headers={"Cache-Control": "public, max-age=300"})

    @app.get("/ready")
    def ready() -> Response:
        status = 200 if engine.readiness.state.value == "ready" else 503
        return Response(engine.readiness.model_dump_json(), media_type="application/json", status_code=status)

    @app.get("/v1/collaboration/status")
    def collaboration_status(principal: PrincipalRef = Depends(require("health:read"))) -> dict[str, Any]:
        return {"enabled": bool(collaboration_consent and collaboration_consent.sharing_enabled), "sharing_enabled": bool(collaboration_consent and collaboration_consent.sharing_enabled), "research_enabled": bool(collaboration_consent and collaboration_consent.research_enabled), "transport": "fixture", "transport_trust": "email_unverified", "experimental": True, "audit_entries": len(collaboration_audit), "last_audit": collaboration_audit[-1] if collaboration_audit else None}

    @app.get("/v1/collaboration/consent")
    def collaboration_get_consent(principal: PrincipalRef = Depends(require("health:read"))) -> dict[str, Any]:
        return collaboration_consent.model_dump(mode="json") if collaboration_consent else {"sharing_enabled": False, "research_enabled": False, "hazards": {hazard: False for hazard in ("wildfire", "earthquake", "flood", "landslide")}, "policy_version": "collab-demo-v1", "updated_at": None}

    @app.put("/v1/collaboration/consent")
    def collaboration_put_consent(payload: CollaborationConsent, principal: PrincipalRef = Depends(require("configuration:activate"))) -> dict[str, Any]:
        nonlocal collaboration_consent
        old = collaboration_consent
        collaboration_consent = payload
        audit = {"audit_id": f"collaboration-consent-{len(collaboration_audit) + 1}", "actor": principal.principal_id, "changed_at": payload.updated_at.isoformat(), "previous_sharing_enabled": bool(old and old.sharing_enabled), "sharing_enabled": payload.sharing_enabled, "previous_research_enabled": bool(old and old.research_enabled), "research_enabled": payload.research_enabled, "policy_version": payload.policy_version}
        collaboration_audit.append(audit)
        return {"accepted": True, "consent": payload.model_dump(mode="json"), "audit_required": True, "audit": audit}

    @app.get("/v1/collaboration/signals")
    def collaboration_signals_get(
        hazard: str | None = Query(default=None),
        validation_state: str | None = Query(default=None),
        transport: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        cursor: int = Query(default=0, ge=0),
        principal: PrincipalRef = Depends(require("incidents:read")),
    ) -> dict[str, Any]:
        safe_items = []
        for item in collaboration_signals:
            signal = item.get("signal", {})
            if hazard and signal.get("hazard") != hazard:
                continue
            if transport and item.get("transport") != transport:
                continue
            if validation_state and item.get("validation_state", "accepted") != validation_state:
                continue
            safe_items.append({"signal_id": signal.get("signal_id"), "hazard": signal.get("hazard"), "observation": signal.get("observation"), "correlation_domain": signal.get("correlation_domain"), "transport": item.get("transport"), "transport_trust": item.get("transport_trust"), "source_mode": signal.get("source_mode"), "research_use_allowed": signal.get("research_use_allowed", False), "validation_state": item.get("validation_state", "accepted")})
        page = safe_items[cursor:cursor + limit]
        next_cursor = cursor + limit if cursor + limit < len(safe_items) else None
        return {"items": page, "limit": limit, "cursor": cursor, "next_cursor": next_cursor, "total_matching": len(safe_items)}

    @app.get("/v1/collaboration/correlations")
    def collaboration_correlations(principal: PrincipalRef = Depends(require("incidents:read"))) -> dict[str, Any]:
        signals: list[CollaborativeSignal] = []
        for item in collaboration_signals:
            try:
                signals.append(CollaborativeSignal.model_validate(item["signal"]))
            except Exception:
                continue
        if not signals:
            return {"items": [], "trusted_multi_node_confirmation": False, "experimental": True}
        decision = correlate(signals, transport_trust="email_unverified")
        item = {"action": decision.action, "reason_codes": list(decision.reason_codes), "independent_peer_count": decision.independent_peer_count, "transport_trust": decision.transport_trust}
        return {"items": [item], "trusted_multi_node_confirmation": False, "experimental": True}

    @app.get("/v1/incidents/{incident_id}/collaboration")
    def incident_collaboration(incident_id: str, principal: PrincipalRef = Depends(require("incidents:read"))) -> dict[str, Any]:
        return {"incident_id": incident_id, "policy_id": "collab-demo-v1", "independent_peer_count": 0, "transport_trust_counts": {}, "signal_summaries": [], "source_modes": [], "correlation_decision_refs": [], "trusted_multi_node_confirmation": False}

    @app.get("/health")
    def health() -> dict:
        return {
            "status": engine.capabilities.overall.value,
            "mode": "fixture_capable",
            "components": 6,
            "adapters": list(engine.analysis.adapter_ids),
            "authentication": {
                "enabled": True,
                "development_credentials": auth.development_only,
                "release_admissible": not auth.development_only,
            },
            "capabilities": [item.model_dump(mode="json") for item in engine.capabilities.records()],
            "configuration": engine.configuration.state(),
            "readiness": engine.readiness.model_dump(mode="json"),
            "storage": engine.artifacts.usage_report(),
            "critical_spool": engine.critical_spool.metrics().__dict__,
            "protected_local_state": engine.protected_state.metrics(),
            "audit": {
                "checkpoint_count": len(engine.audit.checkpoints()),
                "key_generations": len(engine.key_lifecycle.records()),
                "non_forensic": True,
            },
        }


    @app.get("/v1/platform/power")
    def platform_power(principal: PrincipalRef = Depends(require("health:read"))) -> dict:
        return {
            "snapshot": power_health.snapshot().model_dump(mode="json"),
            "history": [item.model_dump(mode="json") for item in power_health.history()],
        }

    @app.post("/v1/platform/power/evaluate")
    def evaluate_platform_power(
        sample: PowerTelemetrySample,
        principal: PrincipalRef = Depends(require("health:read")),
    ) -> dict:
        snapshot = power_health.observe(sample)
        return {
            "snapshot": snapshot.model_dump(mode="json"),
            "observed_by": principal.principal_id,
            "current_history_separated": True,
        }

    @app.get("/v1/session")
    def session(principal: PrincipalRef = Depends(require("health:read"))) -> dict:
        return principal.model_dump(mode="json")

    @app.post("/v1/session/logout")
    def logout(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        principal: PrincipalRef = Depends(require("health:read")),
    ) -> dict:
        purges = engine.protected_state.purge_principal(
            principal,
            action=GrantLifecycleAction.LOGOUT,
            actor=principal.principal_id,
            reason="authenticated_logout",
        )
        if credentials is None:
            raise HTTPException(status_code=401, detail={"code": "authentication_required", "message": "missing bearer token"})
        auth.disable_token(credentials.credentials)
        return {
            "principal_id": principal.principal_id,
            "token_disabled": True,
            "purge_receipts": [item.model_dump(mode="json") for item in purges],
        }

    @app.post("/v1/security/principals/{principal_id}/revoke-device")
    def revoke_device(
        principal_id: str,
        request: DeviceRevocationRequest,
        principal: PrincipalRef = Depends(require("*")),
    ) -> dict:
        purges = engine.protected_state.purge_principal_id(
            principal_id,
            action=GrantLifecycleAction.DEVICE_REVOCATION,
            actor=principal.principal_id,
            reason=request.reason,
        )
        disabled = auth.disable_principal(principal_id)
        return {
            "principal_id": principal_id,
            "disabled_tokens": disabled,
            "purge_receipts": [item.model_dump(mode="json") for item in purges],
        }

    @app.get("/v1/security/protected-state")
    def protected_state(principal: PrincipalRef = Depends(require("storage:read"))) -> dict:
        return {
            "metrics": engine.protected_state.metrics(),
            "grants": [item.model_dump(mode="json") for item in engine.protected_state.grants()],
            "purge_receipts": [item.model_dump(mode="json") for item in engine.protected_state.receipts()],
        }

    @app.get("/v1/audit/checkpoints")
    def audit_checkpoints(principal: PrincipalRef = Depends(require("evidence:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.audit.checkpoints()]

    @app.get("/v1/audit/keys")
    def audit_keys(principal: PrincipalRef = Depends(require("evidence:read"))) -> dict:
        return {
            "records": [item.model_dump(mode="json") for item in engine.key_lifecycle.records()],
            "events": [item.model_dump(mode="json") for item in engine.key_lifecycle.events()],
        }

    @app.post("/v1/audit/checkpoints/verify")
    def verify_audit_checkpoint(
        request: AuditCheckpointVerifyRequest,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> dict:
        try:
            checkpoint = AuditCheckpoint.model_validate(request.checkpoint)
            report = engine.audit.verify(checkpoint, entries=engine.incidents.authority_journal())
            return report.model_dump(mode="json")
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=409, detail={"code": "audit_checkpoint_rejected", "message": _safe_public_message()}) from exc

    @app.get("/v1/incidents")
    def incidents(
        response: Response,
        principal: PrincipalRef = Depends(require("incidents:read")),
    ) -> list[dict]:
        authority = next(item for item in engine.capabilities.records() if item.capability_id == "incident_authority")
        if authority.state.value == "healthy":
            response.headers["X-Incident-Authority"] = "available"
            response.headers["X-Incident-Projection"] = "authoritative-current"
        else:
            response.headers["X-Incident-Authority"] = "unavailable"
            response.headers["X-Incident-Projection"] = "authoritative-stale"
        response.headers["X-Incident-Authority-Reason"] = ",".join(authority.reason_codes)
        return [item.model_dump(mode="json") for item in engine.incidents.current()]

    @app.get("/v1/projections/incidents")
    def incident_projection(
        request: Request,
        min_aggregate_version: int | None = Query(default=None, ge=1),
        principal: PrincipalRef = Depends(require("incidents:read")),
    ) -> Response:
        snapshot = projections.snapshot(principal_scope=principal.principal_id, filter_scope="incidents")
        available_version = snapshot.cursor.projection_version
        if min_aggregate_version is not None and available_version < min_aggregate_version:
            return Response(
                json.dumps({
                    "status": "pending",
                    "consistency": "pending",
                    "required_version": min_aggregate_version,
                    "available_version": available_version,
                    "resync_required": False,
                }, sort_keys=True),
                media_type="application/json", status_code=202,
                headers={"Retry-After": "1", "X-Projection-Consistency": "pending"},
            )
        etag = f'"{snapshot.payload_sha256}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag, "X-Projection-Cursor": snapshot.cursor.event_id})
        return Response(
            snapshot.model_dump_json(),
            media_type="application/json",
            headers={
                "ETag": etag,
                "X-Projection-Cursor": snapshot.cursor.event_id,
                "X-Projection-Authenticated": "hmac-sha256",
                "X-Projection-Consistency": "satisfied" if min_aggregate_version is not None else "unspecified",
            },
        )

    @app.get("/v1/projections/incidents/stream")
    def incident_projection_stream(
        request: Request,
        principal: PrincipalRef = Depends(require("incidents:read")),
    ) -> StreamingResponse:
        event, snapshot = projections.continuity(
            request.headers.get("last-event-id"),
            principal_scope=principal.principal_id,
            filter_scope="incidents",
        )
        body = projections.sse(event, snapshot)
        return StreamingResponse(
            iter((body,)),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store, private",
                "X-Accel-Buffering": "no",
                "X-Projection-Epoch": str(snapshot.cursor.stream_epoch),
            },
        )

    @app.post("/v1/projections/incidents/rebuild")
    def rebuild_projection(principal: PrincipalRef = Depends(require("configuration:activate"))) -> dict:
        epoch = projections.rotate_epoch("operator_requested_rebuild")
        return {"stream_epoch": str(epoch), "projection": projections.snapshot().model_dump(mode="json")}

    @app.get("/v1/incidents/journal")
    def incident_journal(principal: PrincipalRef = Depends(require("incidents:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.incidents.journal()]

    @app.get("/v1/authority-journal")
    def authority_journal(principal: PrincipalRef = Depends(require("incidents:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.incidents.authority_journal()]

    @app.get("/v1/commands")
    def command_receipts(principal: PrincipalRef = Depends(require("incidents:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.incidents.command_receipts()]

    @app.get("/v1/reviews")
    def reviews(principal: PrincipalRef = Depends(require("reviews:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.incidents.reviews()]

    def _current_incident(hazard: HazardKind):
        current = next((item for item in engine.incidents.current() if item.hazard is hazard), None)
        if current is None:
            raise HTTPException(status_code=404, detail={"code": "incident_not_found", "message": hazard.value})
        return current

    @app.post("/v1/incidents/identity/resolve")
    def resolve_incident_identity(
        candidate: IncidentCandidate,
        principal: PrincipalRef = Depends(require("evidence:write")),
    ) -> dict:
        decision = engine.identity.resolve(candidate)
        return {
            "decision": decision.model_dump(mode="json"),
            "deduplication_policy": "hazard_specific_temporal_spatial_v1",
            "submitted_by": principal.principal_id,
        }

    @app.get("/v1/incidents/identity/decisions")
    def incident_identity_decisions(
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.identity.store.identity_decisions()]

    @app.get("/v1/incidents/{hazard}/evidence")
    def incident_evidence(
        hazard: HazardKind,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> list[dict]:
        current = _current_incident(hazard)
        result = []
        for item in engine.evidence.store.evidence(str(current.incident_id)):
            payload = item.model_dump(mode="json")
            if engine.disposition.is_restricted(item.evidence_id):
                payload["claim_text"] = "[RESTRICTED_PENDING_DISPOSITION]"
                payload["source_id"] = "restricted"
                payload["content_sha256"] = "0" * 64
                payload["disposition_restricted"] = True
            else:
                payload["disposition_restricted"] = False
            result.append(payload)
        return result

    @app.post("/v1/incidents/{hazard}/evidence")
    def add_incident_evidence(
        hazard: HazardKind,
        request: EvidenceRequest,
        principal: PrincipalRef = Depends(require("evidence:write")),
    ) -> dict:
        current = _current_incident(hazard)
        try:
            item = engine.evidence.ingest(EvidenceItem(
                incident_id=current.incident_id,
                hazard=hazard,
                source_id=request.source_id,
                source_standing=request.source_standing,
                media_integrity=request.media_integrity,
                extraction_confidence_state=request.extraction_confidence_state,
                extraction_confidence=request.extraction_confidence,
                freshness_state=request.freshness_state,
                claim_text=request.claim_text,
                content_sha256=request.content_sha256,
                perceptual_hash=request.perceptual_hash,
                origin_key=request.origin_key,
                parent_evidence_id=request.parent_evidence_id,
                independent_origin_proven=request.independent_origin_proven,
                retention_state=request.retention_state,
                parser_state=request.parser_state,
                rights_basis=request.rights_basis,
                rights_mode=request.rights_mode,
                rights_expires_at=request.rights_expires_at,
                modality=request.modality,
                received_at=datetime.now(timezone.utc),
                reason_codes=request.reason_codes + (f"submitted_by:{principal.principal_id}",),
                subject_ref=request.subject_ref,
                processing_basis=request.processing_basis,
            ))
            return {
                "evidence": item.model_dump(mode="json"),
                "trust": engine.evidence.trust_snapshot(current.incident_id).model_dump(mode="json"),
            }
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "evidence_rejected", "message": _safe_public_message()}) from exc

    @app.get("/v1/incidents/{hazard}/evidence-lifecycle")
    def evidence_lifecycle(
        hazard: HazardKind,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> dict:
        current = _current_incident(hazard)
        evidence = engine.evidence.store.evidence(str(current.incident_id))
        return {
            "projections": [engine.evidence.lifecycle(item.evidence_id).model_dump(mode="json") for item in evidence],
            "events": [item.model_dump(mode="json") for item in engine.evidence.lifecycle_events(current.incident_id)],
            "reconciliation": engine.evidence.claim_reconciliation(current.incident_id),
        }

    @app.post("/v1/incidents/{hazard}/evidence/{evidence_id}/redact")
    def redact_evidence(
        hazard: HazardKind,
        evidence_id: UUID,
        request: EvidenceLifecycleRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        current = _current_incident(hazard)
        try:
            item = next(item for item in engine.evidence.store.evidence(str(current.incident_id)) if item.evidence_id == evidence_id)
            projection = engine.evidence.transition(
                item.evidence_id,
                to_state=EvidenceContentState.REDACTED,
                expected_version=request.expected_version,
                actor=principal.principal_id,
                reason=request.reason,
                redaction_profile_id=request.redaction_profile_id or "sentinel-metadata-redaction-v1",
            )
            return {
                "projection": projection.model_dump(mode="json"),
                "reconciliation": engine.evidence.claim_reconciliation(current.incident_id),
            }
        except (KeyError, StopIteration, ValueError) as exc:
            raise HTTPException(status_code=409, detail={"code": "evidence_lifecycle_conflict", "message": _safe_public_message()}) from exc

    @app.post("/v1/incidents/{hazard}/evidence/{evidence_id}/delete")
    def delete_evidence(
        hazard: HazardKind,
        evidence_id: UUID,
        request: EvidenceLifecycleRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        current = _current_incident(hazard)
        try:
            item = next(item for item in engine.evidence.store.evidence(str(current.incident_id)) if item.evidence_id == evidence_id)
            projection = engine.evidence.transition(
                item.evidence_id,
                to_state=EvidenceContentState.DELETED,
                expected_version=request.expected_version,
                actor=principal.principal_id,
                reason=request.reason,
            )
            return {
                "projection": projection.model_dump(mode="json"),
                "reconciliation": engine.evidence.claim_reconciliation(current.incident_id),
            }
        except (KeyError, StopIteration, ValueError) as exc:
            raise HTTPException(status_code=409, detail={"code": "evidence_lifecycle_conflict", "message": _safe_public_message()}) from exc

    @app.post("/v1/evidence/enforce-rights-expiry")
    def enforce_rights_expiry(
        payload: dict | None = None,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        now = datetime.fromisoformat(payload["now"]) if payload and payload.get("now") else datetime.now(timezone.utc)
        expired = engine.evidence.enforce_rights_expiry(now=now, actor=principal.principal_id)
        return {"expired": [item.model_dump(mode="json") for item in expired], "count": len(expired)}

    @app.post("/v1/exports/evidence")
    def create_evidence_export(
        request: EvidenceExportRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        with tempfile.TemporaryDirectory(prefix="sentinel-export-api-") as temp_name:
            path = Path(temp_name) / "evidence-export.zip"
            try:
                manifest = engine.exports.create(
                    path,
                    selections=request.selections,
                    derivatives=request.derivatives,
                    audience=request.audience,
                )
                verification = engine.exports.verify(path)
                if not verification["valid"]:
                    raise RuntimeError(f"export verification failed: {verification['errors']}")
                ref = engine.artifacts.put_bytes(
                    path.read_bytes(),
                    media_type="application/zip",
                    critical=False,
                    policy=ArtifactPolicy.export_bundle(public=request.audience in {ExportAudience.PUBLIC, ExportAudience.JUDGE}),
                    scope=ArtifactScope(scenario_run_id=f"export:{manifest.export_id}"),
                )
                return {
                    "export_id": str(manifest.export_id),
                    "manifest": manifest.model_dump(mode="json"),
                    "artifact": {
                        "sha256": ref.sha256,
                        "bytes": ref.bytes,
                        "media_type": ref.media_type,
                    },
                    "created_by": principal.principal_id,
                    "path_disclosed": False,
                }
            except (KeyError, PermissionError, ValueError, OSError, RuntimeError) as exc:
                raise HTTPException(status_code=422, detail={"code": "export_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/exports/verify")
    def verify_evidence_export(
        request: EvidenceExportVerifyRequest,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> dict:
        try:
            data = base64.b64decode(request.data_base64, validate=True)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_base64", "message": _safe_public_message()}) from exc
        with tempfile.TemporaryDirectory(prefix="sentinel-export-verify-") as temp_name:
            path = Path(temp_name) / "submitted.zip"
            path.write_bytes(data)
            try:
                result = engine.exports.verify(path)
            except (ValueError, zipfile.BadZipFile) as exc:
                raise HTTPException(status_code=422, detail={"code": "invalid_export", "message": _safe_public_message()}) from exc
            return {**result, "verified_by": principal.principal_id}

    @app.get("/v1/artifacts")
    def artifact_catalog(principal: PrincipalRef = Depends(require("storage:read"))) -> dict:
        return {
            "usage": engine.artifacts.catalog.usage(),
            # Relative paths belong to the owning artifact store and are never a
            # client-facing capability or identifier.
            "records": [
                {key: value for key, value in item.model_dump(mode="json").items() if key != "relative_path"}
                for item in engine.artifacts.catalog.records()
            ],
        }

    @app.post("/v1/artifacts/{digest}/references")
    def add_artifact_reference(
        digest: str,
        request: ArtifactReferenceRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        try:
            ref = engine.artifacts.add_reference(
                digest, kind=request.kind, owner=request.owner, reason=request.reason, expires_at=request.expires_at
            )
            return {"reference": ref.model_dump(mode="json"), "created_by": principal.principal_id}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "artifact_reference_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/artifacts/gc")
    def artifact_gc(
        payload: dict | None = None,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        now = datetime.fromisoformat(payload["now"]) if payload and payload.get("now") else datetime.now(timezone.utc)
        return engine.artifacts.collect_garbage(actor=principal.principal_id, now=now)

    @app.post("/v1/disposition/nodes")
    def register_disposition_node(
        request: DispositionNodeRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        try:
            node = engine.disposition.register_node(**request.model_dump())
            return {"node": node.model_dump(mode="json"), "created_by": principal.principal_id}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "disposition_node_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/disposition/requests")
    def create_disposition_request(
        request: DispositionCreateRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        try:
            item = engine.disposition.create_request(
                **request.model_dump(), actor=principal.principal_id
            )
            return item.model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "disposition_request_rejected", "message": _safe_public_message()}) from exc

    @app.get("/v1/disposition/requests")
    def disposition_requests(principal: PrincipalRef = Depends(require("evidence:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.disposition.requests()]

    @app.post("/v1/disposition/requests/{request_id}/close")
    def close_disposition_request(
        request_id: UUID,
        payload: dict | None = None,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        now = datetime.fromisoformat(payload["now"]) if payload and payload.get("now") else datetime.now(timezone.utc)
        try:
            report = engine.disposition.close(
                request_id, evidence_service=engine.evidence, artifact_store=engine.artifacts, now=now
            )
            return {"report": report.model_dump(mode="json"), "closed_by": principal.principal_id}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail={"code": "disposition_close_conflict", "message": _safe_public_message()}) from exc

    @app.post("/v1/disposition/nodes/{node_id}/external-receipt")
    def external_disposition_receipt(
        node_id: UUID,
        request: ExternalDispositionReceiptRequest,
        principal: PrincipalRef = Depends(require("evidence:govern")),
    ) -> dict:
        try:
            return engine.disposition.acknowledge_external_recipient(
                node_id, actor=principal.principal_id, receipt=request.receipt
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "external_receipt_rejected", "message": _safe_public_message()}) from exc

    @app.get("/v1/disposition/requests/{request_id}/external-reconciliation")
    def external_reconciliation_attempts(
        request_id: UUID,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> list[dict]:
        try:
            engine.disposition.request(request_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "disposition_not_found", "message": _safe_public_message()}) from exc
        return [
            item.model_dump(mode="json")
            for item in engine.disposition.external_reconciliation_attempts(request_id)
        ]

    @app.get("/v1/disposition/requests/{request_id}/tombstone")
    def disposition_tombstone(
        request_id: UUID,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> dict:
        try:
            return engine.disposition.minimal_tombstone(request_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "disposition_not_found", "message": _safe_public_message()}) from exc

    @app.post("/v1/media/parse")
    def parse_media(
        request: MediaParseRequest,
        principal: PrincipalRef = Depends(require("evidence:write")),
    ) -> dict:
        try:
            data = base64.b64decode(request.data_base64, validate=True)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_base64", "message": _safe_public_message()}) from exc
        report, sanitized = engine.media_parser.parse(data, media_type=request.media_type)
        engine.evidence.store.record_media_parser_report(report)
        artifact = None
        if request.persist_sanitized and sanitized is not None:
            ref = engine.artifacts.put_bytes(
                sanitized, media_type="image/png", critical=False,
                policy=ArtifactPolicy.sanitized_media(),
                scope=ArtifactScope(source_id="untrusted-media-parser"),
            )
            artifact = ref.__dict__
        return {
            "report": report.model_dump(mode="json"),
            "artifact": artifact,
            "submitted_by": principal.principal_id,
            "authority_effect": "none_until_evidence_is_explicitly_ingested",
        }

    @app.get("/v1/media/parse-reports")
    def media_parse_reports(
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.evidence.store.media_parser_reports()]

    @app.get("/v1/incidents/{hazard}/evidence-reevaluations")
    def evidence_reevaluations(
        hazard: HazardKind,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> list[dict]:
        current = _current_incident(hazard)
        return [
            item.model_dump(mode="json")
            for item in engine.evidence.store.evidence_reevaluations(str(current.incident_id))
        ]

    @app.get("/v1/incidents/{hazard}/evidence-families")
    def evidence_families(
        hazard: HazardKind,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> list[dict]:
        current = _current_incident(hazard)
        return [item.model_dump(mode="json") for item in engine.evidence.families(current.incident_id)]

    @app.get("/v1/incidents/{hazard}/trust")
    def incident_trust(
        hazard: HazardKind,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> dict:
        current = _current_incident(hazard)
        snapshot = engine.evidence.trust_snapshot(current.incident_id)
        return {
            "snapshot": snapshot.model_dump(mode="json"),
            "graph_sha256": engine.evidence.graph_digest(current.incident_id),
        }

    @app.get("/v1/incidents/{hazard}/claims")
    def incident_claims(
        hazard: HazardKind,
        principal: PrincipalRef = Depends(require("evidence:read")),
    ) -> dict:
        current = _current_incident(hazard)
        return {
            "claims": [item.model_dump(mode="json") for item in engine.evidence.store.claims(str(current.incident_id))],
            "links": [item.model_dump(mode="json") for item in engine.evidence.store.claim_links(str(current.incident_id))],
        }

    @app.post("/v1/incidents/{hazard}/claims")
    def add_incident_claim(
        hazard: HazardKind,
        request: ClaimRequest,
        principal: PrincipalRef = Depends(require("evidence:write")),
    ) -> dict:
        current = _current_incident(hazard)
        claim = engine.evidence.create_claim(ClaimNode(
            incident_id=current.incident_id,
            hazard=hazard,
            statement=request.statement,
            origin=ContentOrigin(request.origin),
            lineage=request.lineage,
            status=request.status,
            reason_codes=request.reason_codes + (f"submitted_by:{principal.principal_id}",),
        ))
        return claim.model_dump(mode="json")

    @app.post("/v1/claims/{claim_id}/links")
    def add_claim_link(
        claim_id: UUID,
        request: ClaimLinkRequest,
        principal: PrincipalRef = Depends(require("evidence:write")),
    ) -> dict:
        try:
            link = engine.evidence.link(ClaimEvidenceLink(
                claim_id=claim_id,
                evidence_id=request.evidence_id,
                relation=request.relation,
                reason_codes=request.reason_codes + (f"submitted_by:{principal.principal_id}",),
            ))
            return link.model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "claim_link_rejected", "message": _safe_public_message()}) from exc

    @app.get("/v1/incidents/relations")
    def incident_relations(principal: PrincipalRef = Depends(require("evidence:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.incidents.incident_relations()]

    @app.post("/v1/incidents/{hazard}/commands")
    def incident_command(
        hazard: HazardKind,
        request: ClientIncidentCommandRequest,
        principal: PrincipalRef = Depends(require("incidents:command")),
    ) -> dict:
        if request.command in {IncidentCommandKind.RESOLVE, IncidentCommandKind.REOPEN, IncidentCommandKind.MERGE}:
            try:
                auth.authorize(principal, "incidents:high_impact")
            except AuthorizationError as exc:
                raise HTTPException(status_code=403, detail={"code": "high_impact_authority_required", "message": _safe_public_message()}) from exc
        current = _current_incident(hazard)
        try:
            result = engine.incidents.apply_status_command(IncidentStatusCommand(
                incident_id=current.incident_id,
                hazard=hazard,
                command=request.command,
                expected_version=request.expected_version,
                actor=principal.principal_id,
                reason=request.reason,
                related_incident_id=request.related_incident_id,
                related_hazard=request.related_hazard,
                idempotency_key=request.idempotency_key,
            ))
            response = result.model_dump(mode="json")
            response["command_lifecycle"] = "committed"
            response["projection_state"] = "projected"
            response["projection"] = projections.snapshot().model_dump(mode="json")
            return response
        except ValueError as exc:
            safe_message = "reconfirmation required" if "reconfirmation" in str(exc) else _safe_public_message()
            raise HTTPException(status_code=409, detail={"code": "incident_command_conflict", "message": safe_message}) from exc

    @app.post("/v1/offline/incidents/{hazard}/prepare")
    def prepare_offline_command(
        hazard: HazardKind,
        request: OfflineReviewRequest,
        principal: PrincipalRef = Depends(principal_from_credentials),
    ) -> dict:
        permission = f"incidents:{request.action.value}"
        try:
            auth.authorize(principal, permission)
            current = _current_incident(hazard)
            ticket = offline_commands.prepare(current, request, principal)
            return {
                "ticket": ticket.model_dump(mode="json"),
                "storage_policy": "client_queue_minimal_no_evidence_or_secrets",
                "reconciliation_required": True,
            }
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail={"code": "permission_denied", "message": _safe_public_message()}) from exc

    @app.post("/v1/offline/commands/reconcile")
    def reconcile_offline_command(
        ticket: OfflineReviewTicket,
        principal: PrincipalRef = Depends(principal_from_credentials),
    ) -> dict:
        try:
            auth.authorize(principal, f"incidents:{ticket.action.value}")
            current = _current_incident(ticket.hazard)
            command = offline_commands.reconcile(ticket, current, principal)
            state, receipt = engine.incidents.apply_authorized_review(command)
            return {
                "state": state.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json"),
                "projection": projections.snapshot().model_dump(mode="json"),
            }
        except AuthorizationError as exc:
            message = str(exc)
            if "expired" in message:
                code, safe_message = "reconfirmation_required", "reconfirmation required"
            elif "stale" in message:
                code, safe_message = "offline_command_rejected", "stale command"
            else:
                code, safe_message = "offline_command_rejected", _safe_public_message()
            raise HTTPException(status_code=409, detail={"code": code, "message": safe_message}) from exc
        except ValueError as exc:
            safe_message = "reconfirmation required" if "reconfirmation" in str(exc) else _safe_public_message()
            raise HTTPException(status_code=409, detail={"code": "command_conflict", "message": safe_message}) from exc

    @app.post("/v1/incidents/{hazard}/acknowledge")
    def acknowledge(
        hazard: HazardKind,
        request: ClientAcknowledgeRequest,
        principal: PrincipalRef = Depends(require("incidents:acknowledge")),
    ) -> dict:
        current = _current_incident(hazard)
        submitted_at = datetime.now(timezone.utc)
        payload = {
            "incident_id": str(current.incident_id),
            "hazard": hazard.value,
            "action": ReviewActionKind.ACKNOWLEDGE.value,
            "snooze_until": None,
            "comment": None,
            "idempotency_key": request.idempotency_key,
        }
        target = f"incident:{current.incident_id}"
        decision = engine.incidents.command_authorizer.decide(
            principal,
            operation="incidents:acknowledge",
            target=target,
            payload=payload,
            accepted_at=submitted_at,
        )
        command = AuthorizedReviewCommand(
            incident_id=current.incident_id,
            hazard=hazard,
            action=ReviewActionKind.ACKNOWLEDGE,
            idempotency_key=request.idempotency_key,
            authorization=decision,
            payload_sha256=decision.payload_sha256,
            submitted_at=submitted_at,
        )
        try:
            state, receipt = engine.incidents.apply_authorized_review(command)
            return {
                "state": state.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json"),
                "command_lifecycle": receipt.status.value,
                "projection_state": "projected",
                "projection": projections.snapshot().model_dump(mode="json"),
            }
        except (ValueError, AuthorizationError) as exc:
            raise HTTPException(status_code=409, detail={"code": "command_conflict", "message": _safe_public_message()}) from exc

    @app.post("/v1/incidents/{hazard}/snooze")
    def snooze(
        hazard: HazardKind,
        request: ClientSnoozeRequest,
        principal: PrincipalRef = Depends(require("incidents:snooze")),
    ) -> dict:
        current = _current_incident(hazard)
        submitted_at = datetime.now(timezone.utc)
        if request.until <= submitted_at:
            raise HTTPException(status_code=422, detail={"code": "invalid_snooze", "message": "until must be in the future"})
        payload = {
            "incident_id": str(current.incident_id),
            "hazard": hazard.value,
            "action": ReviewActionKind.SNOOZE.value,
            "snooze_until": request.until.isoformat(),
            "comment": None,
            "idempotency_key": request.idempotency_key,
        }
        target = f"incident:{current.incident_id}"
        decision = engine.incidents.command_authorizer.decide(
            principal,
            operation="incidents:snooze",
            target=target,
            payload=payload,
            accepted_at=submitted_at,
        )
        command = AuthorizedReviewCommand(
            incident_id=current.incident_id,
            hazard=hazard,
            action=ReviewActionKind.SNOOZE,
            snooze_until=request.until,
            idempotency_key=request.idempotency_key,
            authorization=decision,
            payload_sha256=decision.payload_sha256,
            submitted_at=submitted_at,
        )
        try:
            state, receipt = engine.incidents.apply_authorized_review(command)
            return {"state": state.model_dump(mode="json"), "receipt": receipt.model_dump(mode="json")}
        except (ValueError, AuthorizationError) as exc:
            raise HTTPException(status_code=409, detail={"code": "command_conflict", "message": _safe_public_message()}) from exc

    @app.get("/v1/notifications")
    def notifications(principal: PrincipalRef = Depends(require("notifications:read"))) -> dict:
        return {
            "delivery_semantics": "at_least_once_with_idempotent_consumer",
            "workflow_metrics": engine.incidents.workflow_metrics(),
            "records": [item.model_dump(mode="json") for item in engine.incidents.notifications()],
            "streams": list(engine.incidents.notification_streams()),
            "metrics": engine.incidents.notification_metrics(),
            "review_metrics": engine.incidents.review_metrics(),
        }

    @app.post("/v1/notifications/dispatch")
    def dispatch_notifications(principal: PrincipalRef = Depends(require("notifications:dispatch"))) -> dict:
        results = engine.incidents.dispatch_notifications(sink.send)
        return {"delivered": [item.model_dump(mode="json") for item in results], "consumer_effect_count": len(sink.effects)}

    @app.get("/v1/sources/health")
    def source_health(principal: PrincipalRef = Depends(require("sources:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.collector.health()]

    @app.get("/v1/sources/health/journal")
    def source_health_journal(principal: PrincipalRef = Depends(require("sources:read"))) -> list[dict]:
        return [item.model_dump(mode="json") for item in engine.collector.health_events()]


    @app.get("/v1/time")
    def time_trust(principal: PrincipalRef = Depends(require("health:read"))) -> dict:
        return engine.time_trust.snapshot.model_dump(mode="json")

    @app.post("/v1/time/evaluate")
    def evaluate_time_source(payload: dict, principal: PrincipalRef = Depends(require("configuration:activate"))) -> dict:
        try:
            observation = TimeSourceObservation.model_validate(payload)
            return engine.time_trust.update(observation).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "time_source_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/measurements/validate")
    def validate_measurements(payload: dict, principal: PrincipalRef = Depends(require("sources:read"))) -> dict:
        try:
            observation = Observation.model_validate(payload)
            return MeasurementRegistry().validate(observation).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "measurement_contract_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/geospatial/validate")
    def validate_geospatial(payload: dict, principal: PrincipalRef = Depends(require("sources:read"))) -> dict:
        try:
            return validate_geojson_geometry(
                payload["geometry"],
                source_crs=str(payload.get("source_crs", "EPSG:4326")),
                source_axis_order=str(payload.get("source_axis_order", "longitude_latitude")),
                transform_pipeline=str(payload.get("transform_pipeline", "identity:EPSG:4326")),
                max_coordinates=int(payload.get("max_coordinates", 10_000)),
            ).model_dump(mode="json")
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "geospatial_contract_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/geospatial/overlap")
    def geospatial_overlap(payload: dict, principal: PrincipalRef = Depends(require("sources:read"))) -> dict:
        try:
            left = GeoPoint.model_validate(payload["left"])
            right = GeoPoint.model_validate(payload["right"])
            return evaluate_uncertain_overlap(left, right, threshold_m=float(payload["threshold_m"])).model_dump(mode="json")
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "geospatial_overlap_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/geospatial/vertical-compatibility")
    def vertical_compatibility(payload: dict, principal: PrincipalRef = Depends(require("sources:read"))) -> dict:
        try:
            compatible, reasons = compatible_vertical_references(
                VerticalReference.model_validate(payload["left"]),
                VerticalReference.model_validate(payload["right"]),
            )
            return {"compatible": compatible, "reason_codes": list(reasons)}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "vertical_reference_rejected", "message": _safe_public_message()}) from exc

    @app.get("/v1/release-info")
    def release_info(principal: PrincipalRef = Depends(require("runtime:read"))) -> dict:
        candidate_path = Path("release-candidate.json")
        candidate: dict[str, Any] = {}
        if candidate_path.is_file():
            try:
                candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                candidate = {}
        return {
            "release_profile": candidate.get("release_profile") or "H0-EMULATED-AARCH64-20260813",
            "candidate_id": candidate.get("candidate_id"),
            "release_admitted": bool(candidate.get("release_admitted", False)),
            "execution_mode": "docker-qemu-linux-arm64",
            "sensor_mode": "deterministic_simulated",
            "physical_hardware_required": False,
            "physical_sensors_required": False,
            "raspberry_pi_performance_claim_allowed": False,
        }

    @app.get("/v1/runtime")
    def runtime(principal: PrincipalRef = Depends(require("runtime:read"))) -> dict:
        return engine.runtime.snapshot().model_dump(mode="json")

    @app.get("/v1/opportunities")
    def opportunities(principal: PrincipalRef = Depends(require("runtime:read"))) -> dict:
        return {
            "records": [item.model_dump(mode="json") for item in engine.runtime.opportunities.records()],
            "counts": engine.runtime.opportunities.counts(),
            "reconciliation": engine.runtime.opportunities.reconcile(),
            "schedule_digest": engine.runtime.opportunities.schedule_digest(),
        }

    @app.get("/v1/storage")
    def storage(principal: PrincipalRef = Depends(require("storage:read"))) -> dict:
        return {
            "artifacts": engine.artifacts.usage_report(),
            "incident_journal": engine.incidents.storage_diagnostics(),
            "critical_spool": engine.critical_spool.metrics().__dict__,
            "spool_events": list(engine.critical_spool.events()),
        }

    @app.post("/v1/storage/checkpoint")
    def storage_checkpoint(
        payload: dict | None = None,
        principal: PrincipalRef = Depends(require("configuration:activate")),
    ) -> dict:
        mode = str((payload or {}).get("mode", "PASSIVE"))
        try:
            return engine.incidents.checkpoint_storage(mode)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "checkpoint_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/critical-spool/reconcile")
    def reconcile_critical_spool(principal: PrincipalRef = Depends(require("spool:reconcile"))) -> dict:
        delivered = engine.recover_incident_authority()
        return {
            "delivered_analysis_ids": list(delivered),
            "metrics": engine.critical_spool.metrics().__dict__,
            "capabilities": [item.model_dump(mode="json") for item in engine.capabilities.records()],
        }

    @app.get("/v1/configuration")
    def configuration(principal: PrincipalRef = Depends(require("configuration:read"))) -> dict:
        return engine.configuration.state()

    @app.post("/v1/configuration/activate")
    def activate_configuration(payload: dict, principal: PrincipalRef = Depends(require("configuration:activate"))) -> dict:
        if "bundle" not in payload:
            raise HTTPException(status_code=422, detail={"code": "bundle_required", "message": "bundle is required"})
        try:
            record = engine.activate_configuration(payload["bundle"], fail_canary=bool(payload.get("simulate_canary_failure", False)))
            return {"activation": record.model_dump(mode="json"), "configuration": engine.configuration.state()}
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code": "configuration_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/reviews/after-event")
    def after_event_review(payload: dict, principal: PrincipalRef = Depends(require("reviews:generate"))) -> dict:
        if "scenario_id" not in payload or "observations" not in payload:
            raise HTTPException(status_code=422, detail={"code": "invalid_scenario", "message": "scenario_id and observations are required"})
        try:
            result = engine.run(payload)
            builder = AfterEventReviewBuilder()
            review = builder.build(engine, result)
            ref = builder.write(engine, result, engine.configuration.artifacts)
            return {"review": review, "artifact": ref.__dict__, "verified": builder.verify(review)}
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail={"code": "review_rejected", "message": _safe_public_message()}) from exc

    @app.post("/v1/scenarios/run")
    def run_scenario(payload: dict, principal: PrincipalRef = Depends(require("scenarios:run"))) -> dict:
        if "scenario_id" not in payload or "observations" not in payload:
            raise HTTPException(status_code=422, detail={"code": "invalid_scenario", "message": "scenario_id and observations are required"})
        try:
            return engine.run(payload).model_dump(mode="json")
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail={"code": "scenario_rejected", "message": _safe_public_message()}) from exc

    return app
