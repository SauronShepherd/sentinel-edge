# Sentinel Edge — UIX Specification

**Document type:** Product UI / UX design system and screen specification
**Product:** Sentinel Edge
**Reference:** 10 generated desktop application mockups in this conversation
**Status:** Recommended design baseline
**Primary UIX direction:** Clean Product Workspace + Object-Centric Workspace + Split-View Productivity
**Target:** Enterprise edge-security, infrastructure monitoring, incident response, and operations teams

> **Important implementation note:** The mockups are generated images, not screenshots of a coded application. Therefore the typography, spacing, colors, and CSS below are a **reconstructed implementation specification** intended to reproduce the visual language consistently. The CSS is not literal source code extracted from the images.

---

## 1. Product Experience Principles

Sentinel Edge should feel like a high-confidence operations console rather than a generic dashboard. The interface is dense enough for expert users, but the structure must make the next action obvious.

### 1.1 Core UX principles

1. **Operational clarity first.** Critical system health, security state, and required actions should be visible without hunting.
2. **Object-centric navigation.** Sites, devices, incidents, policies, reports, and workflows are first-class objects with dedicated detail states.
3. **Split-view productivity.** Lists and source context should remain visible while the user inspects or acts on a selected object.
4. **Progressive disclosure.** Keep secondary configuration in drawers, inspectors, tabs, and contextual panels rather than showing every option at once.
5. **Risk is visually prioritized.** Red and amber are reserved for meaningful risk or failure states. Blue communicates action/navigation; green communicates healthy/completed.
6. **AI supports decisions, not navigation.** AI insights and investigation tools should explain, correlate, and recommend, while deterministic controls remain conventional UI.
7. **Consistency over novelty.** Tables, filters, tabs, drawers, cards, buttons, status pills, charts, and selection patterns should behave identically across modules.
8. **Fast scanning.** Use compact typography, predictable alignment, status color, short labels, and consistent card anatomy.

---

## 2. Information Architecture

### 2.1 Global navigation

Primary left navigation, in recommended order:

- Overview
- Sites
- Devices
- Sensors
- Cameras
- Incidents
- AI Investigation
- Alerts
- Dashboards
- Reports
- Policies
- Automation
- Integrations
- Administration

The generated screens use a persistent left sidebar and a global top bar. The active module is indicated by a pale blue background with blue icon/text.

### 2.2 Global top bar

The top bar is persistent across all modules and contains:

- Sentinel Edge brand area
- Sidebar collapse / expand control
- Global search / command field
- Keyboard shortcut hint (`⌘ K`)
- Notifications
- Help
- User avatar and online status

Recommended behaviors:

- Global search should search sites, devices, incidents, alerts, reports, policies, and commands.
- `⌘ K` / `Ctrl K` should open a command palette.
- Search results should be grouped by object type.
- Global actions such as “Add Site”, “Add Device”, or “Create Report” remain page-local rather than inside the top bar.

---

## 3. Application Shell

### 3.1 Desktop layout

Reference desktop structure:

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Brand / Collapse      Global search / command       Help  User      │
├───────────────┬─────────────────────────────────────────────────────┤
│               │                                                     │
│ Primary       │ Page header / tabs / filters                       │
│ navigation    │                                                     │
│               │ Main workspace                      Context panel   │
│               │                                                     │
│               │                                                     │
├───────────────┴─────────────────────────────────────────────────────┤
```

Recommended baseline dimensions:

| Element | Baseline |
|---|---:|
| Top bar height | 68 px |
| Left sidebar | 244 px |
| Context / inspector panel | 324 px |
| Main page horizontal padding | 20 px |
| Main page vertical padding | 20 px |
| Standard panel gap | 16 px |
| Base spacing grid | 4 px |

### 3.2 Context panel behavior

The right-side context panel is one of the most important patterns in the design.

Use it for:

- Selected site details
- Selected device details
- Incident ownership / SLA / response playbook
- AI recommended actions
- Policy editing
- Report scheduling
- Firmware rollout details
- Workflow step configuration

Desktop: persistent or sticky.
Tablet: can move below primary content.
Mobile: present as full-height drawer/sheet.

---

## 4. Visual Design System

## 4.1 Typography

The mockups use a neutral, modern grotesk/sans-serif style. The closest recommended implementation is **Inter**.

```css
font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
             "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
```

### Recommended type scale

| Role | Size | Weight | Line height |
|---|---:|---:|---:|
| Page title | 24 px | 700 | 1.2 |
| Section title | 16–20 px | 650–700 | 1.25 |
| Card title | 14 px | 600–650 | 1.3 |
| Body | 14 px | 400–500 | 1.45 |
| UI label | 12 px | 600 | 1.3 |
| Table / metadata | 11–12 px | 500–600 | 1.35 |
| KPI value | 30–36 px | 700 | 1.0 |
| Badge / status | 11 px | 650 | 1.0 |

### Typography rules

- Use sentence case for labels and titles.
- Avoid all-caps headings except very small category labels.
- Use tabular numerals for metrics where possible.
- Use bold weight selectively for titles, KPIs, row names, and actionable state.
- Muted metadata uses `#667085` or lighter.

---

## 4.2 Color tokens

Recommended reconstructed palette:

| Token | Hex | Use |
|---|---|---|
| App background | `#F7F9FC` | Page canvas |
| Surface | `#FFFFFF` | Cards, panels, drawers |
| Selected surface | `#EEF5FF` | Selected nav/table/list row |
| Primary text | `#172033` | Main copy |
| Strong text | `#101828` | Headings/KPIs |
| Muted text | `#667085` | Metadata |
| Subtle text | `#98A2B3` | Secondary hints |
| Border | `#E4E7EC` | Cards, inputs |
| Border strong | `#D0D5DD` | Controls |
| Primary blue | `#1769FF` | Actions, active tabs, links |
| Primary hover | `#0F5AE5` | Hover |
| Primary soft | `#EAF2FF` | Active nav / selected states |
| Success | `#12A66A` | Healthy / online / passed |
| Success soft | `#EAF8F1` | Success pills |
| Warning | `#F59E0B` | Degraded / medium |
| Warning soft | `#FFF7E6` | Warning pills |
| Danger | `#E5484D` | Critical / failed |
| Danger soft | `#FFF0F0` | Critical pills |
| Purple | `#7C5CFF` | AI / Copilot / automation accent |
| Purple soft | `#F1EFFF` | AI pills/cards |

### Semantic color policy

- **Blue**: navigation, selection, primary action, informational links.
- **Green**: healthy, online, complete, compliant, approved.
- **Amber/orange**: degraded, warning, medium impact, pending.
- **Red**: critical, failed, high risk, urgent SLA.
- **Gray**: offline/unknown/disabled where risk is not necessarily active.
- **Purple**: AI and automation intelligence only, used sparingly.

Never encode state using color alone. Pair color with label, icon, or text.

---

## 4.3 Shape and elevation

- Cards: 10–12 px radius.
- Buttons/inputs: 8 px radius.
- Pills: fully rounded.
- Default card shadow: extremely subtle.
- Strong shadows reserved for floating drawers, menus, command palette, and mobile sheets.
- Most hierarchy should come from borders, spacing, and typography rather than shadows.

---

## 4.4 Spacing

Use a 4 px base system.

| Token | Value |
|---|---:|
| XS | 4 px |
| SM | 8 px |
| MD | 12 px |
| Base | 16 px |
| LG | 20 px |
| XL | 24 px |
| 2XL | 32 px |
| 3XL | 40 px |

Common patterns:

- Card internal padding: 16 px.
- Major page section gap: 16–24 px.
- Label-to-field gap: 6–8 px.
- Button gap: 8 px.
- Row padding: 8–12 px.
- Tabs: ~20 px horizontal gap.

---

## 5. Core Components

### 5.1 Buttons

Types:

- Primary: solid blue
- Secondary: white with neutral border
- Destructive: white/red outline or solid red only for irreversible confirmation
- Ghost: no border
- Split button: primary + caret
- Icon button: 32–36 px square

Button hierarchy:

1. One primary action per surface where possible.
2. Secondary actions adjacent.
3. Dangerous actions visually separated from routine actions.

### 5.2 Status pills

Use compact semantic pills:

- Online / Active / Approved / Compliant → green
- Degraded / Warning / Medium / Pending → amber
- Critical / High / Failed / Non-compliant → red
- Low / Maintenance / Informational → blue
- Offline / Unknown / Draft → gray
- Beta / Copilot → purple or blue-purple

### 5.3 Cards

Standard card anatomy:

```text
Title                     Optional action / info
Supporting metric or content
Secondary metadata
Optional footer link
```

Avoid deep card nesting. One nested layer is acceptable in inspector panels.

### 5.4 Tables

Tables are central to Sentinel Edge.

Rules:

- Sticky header for long lists.
- 52–58 px row height.
- First column typically object name with secondary metadata underneath.
- Use status pills in dedicated columns.
- Support sorting, filtering, row selection, and overflow action menu.
- Selected row gets pale blue background.
- Bulk action bar appears after selection.
- Keep numbers aligned consistently.
- Use pagination or virtualized scrolling for large datasets.

### 5.5 Filters

Page-level filter bars should appear directly above the data surface.

Standard order:

1. Search
2. Primary scope selector
3. Object/type filters
4. Status/risk filters
5. Advanced filters
6. Reset

Use persistent filter chips only when a filter is actively applied.

### 5.6 Tabs

Tabs are used inside object details or major content modes.

- Active tab = blue text + 2 px blue underline.
- Tabs never use filled pill styling in this visual system.
- Keep 3–6 tabs visible; overflow more if needed.

### 5.7 Charts

Chart styling:

- White card background.
- Light gray grid.
- Minimal axes.
- Compact legends.
- Use semantic colors consistently.
- Tooltips should show exact values and timestamp.
- Hover / keyboard focus should highlight a single series.
- Never rely only on hue; use marker shape or labels where practical.

### 5.8 Donut / health gauges

Used for:

- Security score
- Compliance
- Connection health
- Uptime
- Rollout success
- AI confidence

Do not use a donut for values that require fine comparison. Use it for a single bounded health score.

---

# 6. Screen Specifications

## Screen 1 — Overview

**Purpose:** Give operators a high-level summary of the entire edge environment and direct them to risks requiring attention.

### Sections

#### A. Page header
- Title: `Overview`
- Subtitle: real-time summary statement
- Time range selector
- `Add Widget` secondary action

#### B. KPI row
Recommended cards:
- Security Posture Score
- Active Incidents
- Connected Sites
- Online Devices

Each card includes:
- label
- large primary value
- small comparison / state
- optional severity breakdown
- deep-link action

#### C. Threat detections chart
Large stacked area chart:
- Critical
- High
- Medium
- Low
- Time range on x-axis
- Count on y-axis
- Chart mode selector

#### D. Performance health cards
Compact metrics:
- Bandwidth health
- Latency p95
- Ring gauge
- Trend sparkline
- Yesterday / previous-period comparison

#### E. Site status table
Columns:
- Site
- Status
- Security score
- Devices
- Bandwidth
- Latency
- Incidents

#### F. Recent Alerts rail
Prioritized by severity and recency.

Each alert:
- severity icon
- title
- site/device
- relative timestamp
- severity badge

#### G. AI Insights
Small recommendations rather than a full chat:
- increased site risk
- firmware recommendations
- bandwidth optimization
- deep links to analysis/action

### UX rules
- Critical incidents must be visible above the fold.
- AI insights must not displace operational alerts.
- Clicking a site row opens its site detail.
- KPI cards should behave as navigational summaries.

---

## Screen 2 — Sites

**Purpose:** Monitor geographic distribution and site health while keeping selected-site context visible.

### Sections

#### A. Header
- Title: `Sites`
- Region selector
- Filters
- `Add Site`

#### B. Site KPIs
- Total Sites
- Online
- Degraded
- Offline

#### C. Regional site list
Left panel:
- site search
- grouped regions
- each site row shows site name and status
- selected site highlighted

#### D. Map
Main map:
- geographic site markers
- online/degraded/offline/unknown colors
- zoom controls
- label toggle
- legend
- selected site label

#### E. Selected Site context panel
Selected object: `Seattle Gateway`

Tabs:
- Overview
- Devices
- Sensors
- Cameras
- Incidents

Overview blocks:
- Connectivity health
- Weather risk
- Devices / cameras / sensors counts
- Bandwidth utilization
- Performance / latency
- Recent alerts

#### F. All Sites table
Columns:
- Site
- Region
- Status
- Security Score
- Devices
- Bandwidth
- Incidents

### UX rules
- Selecting a row or map marker synchronizes the other.
- Closing the inspector returns to full map/table width.
- On smaller screens, map and list may switch via segmented control rather than remain side-by-side.

---

## Screen 3 — Devices

**Purpose:** Inventory, filter, inspect, and manage all edge devices.

### Sections

#### A. Header
- Title: `Devices`
- Export
- `Add Device`

#### B. Filter bar
- Site
- Device Type
- Status
- Firmware Version
- Risk Level
- Advanced filters

#### C. Bulk action toolbar
Initially inactive until selection:
- Update Firmware
- Restart
- Edit Tags
- More

#### D. Device table
Columns:
- Checkbox
- Device Name
- Site
- Type
- Status
- Firmware
- CPU
- Memory
- Last Check-in
- Risk Score
- Actions

#### E. Device detail inspector
Selected object: `GW-SEA-01`

Tabs:
- Overview
- Health
- Config
- History

Overview:
- hardware thumbnail
- type/site/model/serial
- tags
- connection health
- uptime
- open ports
- recent events
- recommended actions

### UX rules
- Device risk should combine score + text label.
- Recommended actions need explicit impact and category.
- Potentially disruptive bulk actions require confirmation.

---

## Screen 4 — Incident Details

**Purpose:** Triage, investigate, coordinate, and resolve a security incident without losing event context.

### Layout
Three-column split view:
1. Incident list
2. Incident workspace
3. Incident context inspector

### Sections

#### A. Incident list
- search
- sort
- list of recent incidents
- severity badges
- timestamps
- selected row

#### B. Incident header
- Incident ID
- Title
- Site
- Detection timestamp
- First seen
- Severity
- Threat / MITRE-like tags
- Previous / next controls

#### C. Summary
Short, action-oriented description:
- what happened
- asset
- destination / source
- confidence
- recommended immediate containment

#### D. Timeline
Events such as:
- Alert triggered
- Behavior analysis
- Destination flagged
- Incident created

#### E. Incident severity card
- 0–100 score
- severity
- impact
- confidence
- deep-link to full risk analysis

#### F. Affected assets
Table:
- Asset
- Type
- Impact
- Status

#### G. Evidence
Evidence objects:
- PCAP
- DNS logs
- Firewall session logs
- Threat intel match

#### H. Response Actions
High visibility actions:
- Contain Device
- Isolate Site
- Create Ticket
- Resolve Incident

#### I. Right context panel
- Assignee
- Status
- SLA timers
- Response playbook
- AI Recommendations

### UX rules
- Risky containment actions should require confirmation and show expected blast radius.
- SLA countdown should change urgency styling as deadlines approach.
- Evidence should open without navigating away from the incident.
- Playbook status should remain visible during triage.

---

## Screen 5 — AI Investigation

**Purpose:** Provide guided AI-assisted reasoning over correlated signals while keeping evidence, entities, and deterministic actions visible.

### Sections

#### A. Header
- Title: `AI Investigation`
- Beta/Copilot badge
- Case selector
- Severity
- Favorite / overflow controls

#### B. Investigation conversation
Left panel:
- user prompts
- AI responses
- sources count
- feedback buttons
- follow-up input
- explicit reliability disclaimer

Recommended prompt starters:
- Summarize what happened
- Which systems were accessed?
- Show the likely attack path
- What evidence supports this?
- What action minimizes blast radius?

#### C. Case summary
- First Seen
- Last Activity
- Duration
- Status
- Assigned To

#### D. Attack Path
Visual sequence:
- compromised credential
- VPN gateway
- WAF / control boundary
- file server
- exfiltration destination

Include:
- phase legend
- layout selector
- export
- zoom / expand

#### E. Suspicious Users
- User
- Risk Score
- Behavior

#### F. Suspicious Devices
- Device
- Risk Score
- Activity

#### G. Correlated Alerts
Compact list with time and severity.

#### H. Root Cause Findings
Evidence-backed bullets, each independently reviewable.

#### I. Right AI context panel
- Confidence Score
- Suggested Next Actions
- Impacted Sites
- Export / Share

### UX rules
- Every AI finding should link to supporting evidence.
- AI confidence must be visible and explainable.
- Deterministic actions require user confirmation.
- Avoid “magic” state changes caused by chat text alone.

---

## Screen 6 — Policies

**Purpose:** Create, inspect, simulate, approve, and roll out security/compliance policies.

### Sections

#### A. Header
- Title: `Policies`
- Import Policy
- Create Policy

#### B. KPI row
- Active Policies
- Policy Violations
- Compliance Score
- Pending Approvals

#### C. Policy category tabs
- Network
- Access
- Firmware
- Data
- Safety

#### D. Filter row
- Search
- Status
- Scope
- Owner
- Filters

#### E. Policy table
Columns:
- Policy
- Status
- Scope
- Last Updated
- Owner
- Violations
- Compliance Impact

#### F. Policy inspector
Selected: `Remote Access Hardening`

Tabs:
- Details
- Rules
- Exceptions
- Rollout

Details:
- description
- active state

Rules:
- MFA requirement
- source IP restriction
- session timeout
- concurrent sessions
- insecure protocol block

Exceptions:
- named objects / windows
- per-exception overflow actions

Rollout:
- Sites
- Devices
- Device Groups
- Exclusions

Footer actions:
- Save Draft
- Simulate Impact
- Publish

### UX rules
- `Simulate Impact` should be encouraged before `Publish`.
- Policy changes should show affected object count.
- Destructive or broad-scope policy changes need elevated confirmation.
- Track author and last updated metadata.

---

## Screen 7 — Reports & Analytics

**Purpose:** Analyze security/operations performance and schedule repeatable reporting.

### Sections

#### A. Header
- Title: `Reports & Analytics`
- Schedule Report
- Export PDF
- Share
- Create Report

#### B. Saved Reports
Left rail:
- Executive Summary
- Security Overview
- Incident Analysis
- Device Health Report
- Compliance Status

#### C. Report Templates
- Executive Summary
- Security Report
- Availability Report
- Compliance Report
- Custom Report

#### D. Report filters
- Date Range
- Site Group
- Severity
- Device Type
- Reset

#### E. Visualizations
- Incident Trends
- Device Uptime
- Site Risk by Region
- Top Recurring Issues

#### F. KPI Summary
Columns:
- Metric
- Current Period
- Previous Period
- Change

#### G. Schedule & Recipients panel
- Enabled
- Frequency
- Day
- Time
- Format
- Recipients
- Optional message
- Save Schedule

### UX rules
- Filters should update all report widgets consistently.
- Export should include active filter context.
- Scheduling should make timezone explicit.
- Reports need persistent saved definitions rather than one-off exports only.

---

## Screen 8 — Deploy New Site

**Purpose:** Provision a site through a guided, low-error workflow.

### Sections

#### A. Breadcrumb / header
- Provisioning
- `Deploy New Site`
- Short supporting description

#### B. Six-step stepper
1. Site Details
2. Network Setup
3. Device Enrollment
4. Security Policies
5. Review
6. Complete

#### C. Site Information form
- Site Name
- Site Code
- Location
- Time Zone
- Site Type
- Environment
- Address

#### D. Bandwidth Profile
- Profile selector
- estimated utilization
- reference link

#### E. Device Templates
- chosen template
- capabilities
- included device settings
- recommended state

#### F. Connectivity Settings
- Primary Connection
- Secondary / Failover
- SD-WAN Overlay
- Cloud Region

#### G. Bottom actions
- Validate Configuration
- Save Draft
- Continue

#### H. Readiness panel
- Readiness score
- status
- readiness details

#### I. Deployment Checklist
Shows progress for all six steps and sub-items.

### UX rules
- Validate on field blur and at explicit Validate action.
- Do not block progress for non-critical warnings; distinguish warning vs error.
- Save draft automatically in addition to explicit Save Draft.
- Final review must summarize all changes and affected infrastructure.

---

## Screen 9 — Firmware & Updates

**Purpose:** Manage fleet firmware compliance and phased update campaigns.

### Sections

#### A. Header
- Title: `Firmware & Updates`
- Date range
- Create Campaign

#### B. Sub-tabs
- Rollout Planner
- Firmware Library
- Update Policies
- History

#### C. KPI row
- Devices Needing Updates
- Critical Patches Available
- Rollout Success Rate
- Scheduled Maintenance

#### D. Rollout Planner
Filters:
- search by site / device family
- campaign
- group by

Table columns:
- Group
- Current Version
- Target Version
- Last Update
- Compliance
- Rollout Stage

#### E. Campaign inspector
Selected: `Q4 Security Patch Rollout`

Tabs:
- Overview
- Phases
- Devices
- Activity

Overview:
- Affected Devices
- Device Families
- Criticality
- Approval Status
- Phases
- Risk Mitigation

Actions:
- Test on Pilot Group
- Schedule Rollout
- Pause Campaign
- View Changelog

### UX rules
- Pilot testing should precede broad rollout.
- Show maintenance windows before scheduling.
- Every rollout needs failure thresholds and automatic rollback policy.
- Progress should be monitorable by phase and site.

---

## Screen 10 — Automation

**Purpose:** Build and operate security/operations workflows visually.

### Layout
Three main regions:
1. Trigger/action library
2. Workflow canvas
3. Step inspector

### Sections

#### A. Header
- Breadcrumb: Automation › Workflows
- Workflow title
- Published / Draft state
- Test Workflow
- Duplicate
- Publish
- Overflow

#### B. Trigger / action library
Tabs:
- Triggers
- Actions

Trigger groups:
- Security
- Manual
- Integrations

Examples:
- Alert triggered
- Incident created
- Device status change
- Policy violation
- Threat intelligence match
- Manual trigger
- Scheduled
- Webhook received
- API event

#### C. Workflow canvas
Recommended node sequence:
1. Alert triggered
2. Isolate device
3. Revoke credentials
4. Create ticket
5. Notify team
6. Verify remediation

Canvas controls:
- zoom
- fit
- grid
- saved state
- mini-map
- add step

#### D. Step inspector
For selected step:
- Description
- Action type
- Configuration
- Timeout
- Retry interval
- Failure behavior
- Advanced options
- Save step

#### E. Operational metrics
- Recent runs
- Success rate
- Failures

### UX rules
- Every workflow change should autosave.
- Draft/published distinction must be explicit.
- Test mode must never affect production by default.
- Nodes should expose validation errors before publish.
- Failure handling must be visible and configurable.

---

# 7. Interaction Patterns

## 7.1 Selection
- Selected list/table row: pale blue background.
- Selected nav item: pale blue background + blue text/icon.
- Selected workflow node: blue outline.
- Selected tab: blue text + bottom rule.

## 7.2 Hover
- Table row: very light gray/blue.
- Cards should not all “lift”; reserve hover elevation for clearly clickable cards.
- Buttons use slight background/border change.

## 7.3 Focus
All interactive elements require a visible 3 px focus ring.

Recommended:

```css
outline: 3px solid rgba(23, 105, 255, 0.22);
outline-offset: 2px;
```

## 7.4 Loading
Use skeletons for:
- KPI cards
- tables
- side panels
- report widgets

Do not blank the whole page when one widget is refreshing.

## 7.5 Empty states
Each object area should provide:
- plain-language description
- why the space is empty
- one primary action
- optional documentation link

## 7.6 Error states
Errors should answer:
1. What failed?
2. What was affected?
3. Is data stale?
4. What can the user do next?

---

# 8. Responsive Strategy

The generated mockups are desktop-first. Recommended breakpoints:

| Width | Behavior |
|---|---|
| ≥ 1180 px | Full sidebar + workspace + inspector |
| 900–1179 px | Reduced sidebar; inspector may move below |
| 640–899 px | Drawer navigation; single-column workspace |
| < 640 px | Mobile, stacked cards, full-screen object sheets |

### Responsive priorities

- Preserve incident response and device status actions before secondary analytics.
- Wide tables become horizontally scrollable or transform into dense list cards.
- Maps may switch to full-width with site list in a separate tab.
- Right inspector becomes a bottom sheet / full-screen drawer.
- Command bar remains accessible.

---

# 9. Accessibility

Minimum requirements:

- WCAG 2.2 AA contrast.
- All controls keyboard accessible.
- Visible focus indicators.
- Status always expressed by text/icon, not color alone.
- Charts include textual summaries and accessible legends.
- Tables use correct headers and scope.
- Live incident / SLA changes use non-disruptive ARIA live regions.
- AI recommendations identify uncertainty and source/evidence.
- Respect `prefers-reduced-motion`.
- Destructive actions require clear confirmation.
- Target size: minimum ~40 px for primary touch interactions on tablet/mobile.

---

# 10. Recommended Design Tokens

```css
:root {
  --font-sans: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
    "Segoe UI", Roboto, Helvetica, Arial, sans-serif;

  --color-bg: #f7f9fc;
  --color-surface: #ffffff;
  --color-surface-selected: #eef5ff;

  --color-text: #172033;
  --color-text-strong: #101828;
  --color-text-muted: #667085;
  --color-text-subtle: #98a2b3;

  --color-border: #e4e7ec;
  --color-border-strong: #d0d5dd;

  --color-primary: #1769ff;
  --color-primary-hover: #0f5ae5;
  --color-primary-soft: #eaf2ff;

  --color-success: #12a66a;
  --color-success-soft: #eaf8f1;
  --color-warning: #f59e0b;
  --color-warning-soft: #fff7e6;
  --color-danger: #e5484d;
  --color-danger-soft: #fff0f0;
  --color-purple: #7c5cff;
  --color-purple-soft: #f1efff;

  --topbar-h: 68px;
  --sidebar-w: 244px;
  --inspector-w: 324px;

  --radius-sm: 8px;
  --radius-lg: 12px;
  --radius-pill: 999px;

  --shadow-card:
    0 1px 2px rgba(16, 24, 40, 0.04),
    0 1px 3px rgba(16, 24, 40, 0.06);
}
```

---

# 11. Reference CSS

The following stylesheet is the recommended reconstructed CSS baseline for implementing the visual language of the generated screens.

```css
/* Sentinel Edge — reconstructed reference CSS
   Derived from the generated UI mockups. This is a design-system implementation
   intended to reproduce the visual language; it is not source CSS extracted from images.
*/

:root {
  /* Typography */
  --font-sans: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;

  /* Core palette */
  --color-bg: #f7f9fc;
  --color-surface: #ffffff;
  --color-surface-subtle: #fbfcfe;
  --color-surface-selected: #eef5ff;

  --color-text: #172033;
  --color-text-strong: #101828;
  --color-text-muted: #667085;
  --color-text-subtle: #98a2b3;

  --color-border: #e4e7ec;
  --color-border-strong: #d0d5dd;

  --color-primary: #1769ff;
  --color-primary-hover: #0f5ae5;
  --color-primary-soft: #eaf2ff;
  --color-primary-strong: #0b4ecf;

  --color-success: #12a66a;
  --color-success-soft: #eaf8f1;

  --color-warning: #f59e0b;
  --color-warning-soft: #fff7e6;

  --color-danger: #e5484d;
  --color-danger-soft: #fff0f0;

  --color-info: #3b82f6;
  --color-info-soft: #eef5ff;

  --color-purple: #7c5cff;
  --color-purple-soft: #f1efff;

  /* Layout */
  --topbar-h: 68px;
  --sidebar-w: 244px;
  --inspector-w: 324px;
  --panel-gap: 16px;
  --page-pad-x: 20px;
  --page-pad-y: 20px;

  /* Radius */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-pill: 999px;

  /* Shadows */
  --shadow-card: 0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.06);
  --shadow-float: 0 8px 24px rgba(16, 24, 40, 0.08);

  /* Spacing: 4px base grid */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  /* Type scale */
  --text-xs: 11px;
  --text-sm: 12px;
  --text-md: 14px;
  --text-lg: 16px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 30px;

  --leading-tight: 1.2;
  --leading-normal: 1.45;
  --leading-relaxed: 1.6;

  /* Motion */
  --ease-standard: cubic-bezier(.2, .8, .2, 1);
  --duration-fast: 120ms;
  --duration-normal: 180ms;
  --duration-slow: 240ms;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
  font-size: var(--text-md);
  line-height: var(--leading-normal);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

button,
input,
select,
textarea {
  font: inherit;
}

button,
[role="button"] {
  cursor: pointer;
}

/* App shell */
.se-app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: var(--sidebar-w) minmax(0, 1fr);
  grid-template-rows: var(--topbar-h) minmax(0, 1fr);
  background: var(--color-bg);
}

.se-topbar {
  grid-column: 1 / -1;
  position: sticky;
  top: 0;
  z-index: 30;
  display: grid;
  grid-template-columns: var(--sidebar-w) minmax(0, 1fr) auto;
  align-items: center;
  min-height: var(--topbar-h);
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(8px);
}

.se-sidebar {
  grid-row: 2;
  position: sticky;
  top: var(--topbar-h);
  height: calc(100vh - var(--topbar-h));
  overflow: auto;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--space-4) var(--space-3);
}

.se-main {
  grid-column: 2;
  grid-row: 2;
  min-width: 0;
  padding: var(--page-pad-y) var(--page-pad-x);
}

/* Page structure */
.se-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.se-page-title {
  margin: 0;
  color: var(--color-text-strong);
  font-size: var(--text-2xl);
  line-height: var(--leading-tight);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.se-page-subtitle {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  font-size: var(--text-md);
}

.se-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

/* Sidebar */
.se-nav {
  display: grid;
  gap: 4px;
}

.se-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 0 12px;
  border-radius: var(--radius-sm);
  color: #344054;
  text-decoration: none;
  font-weight: 500;
  transition: background var(--duration-fast) var(--ease-standard),
              color var(--duration-fast) var(--ease-standard);
}

.se-nav-item:hover {
  background: #f5f8fd;
  color: var(--color-text-strong);
}

.se-nav-item[aria-current="page"],
.se-nav-item.is-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 600;
}

/* Search / command */
.se-command {
  width: min(560px, 52vw);
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-muted);
  box-shadow: inset 0 1px 2px rgba(16, 24, 40, 0.02);
}

/* Buttons */
.se-btn {
  appearance: none;
  border: 1px solid var(--color-border-strong);
  background: var(--color-surface);
  color: #344054;
  border-radius: var(--radius-sm);
  min-height: 36px;
  padding: 0 14px;
  font-weight: 600;
  font-size: var(--text-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.se-btn:hover {
  background: #f8fafc;
  border-color: #c9ced8;
}

.se-btn:active {
  transform: translateY(1px);
}

.se-btn:focus-visible {
  outline: 3px solid rgba(23, 105, 255, 0.22);
  outline-offset: 2px;
}

.se-btn-primary {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 1px 2px rgba(23, 105, 255, 0.22);
}

.se-btn-primary:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.se-btn-danger {
  color: #c93438;
  background: #fff;
  border-color: #f3b6b8;
}

.se-btn-ghost {
  border-color: transparent;
  background: transparent;
}

/* Cards / panels */
.se-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.se-card-body {
  padding: var(--space-4);
}

.se-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4) 0;
}

.se-card-title {
  margin: 0;
  color: var(--color-text-strong);
  font-size: var(--text-md);
  font-weight: 650;
}

.se-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--panel-gap);
}

.se-kpi {
  padding: var(--space-4);
}

.se-kpi-label {
  color: #344054;
  font-size: var(--text-sm);
  font-weight: 600;
}

.se-kpi-value {
  margin-top: 10px;
  color: var(--color-text-strong);
  font-size: 34px;
  line-height: 1;
  letter-spacing: -0.035em;
  font-weight: 700;
}

.se-kpi-meta {
  margin-top: 8px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* Tables */
.se-table-wrap {
  overflow: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.se-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 820px;
}

.se-table th {
  height: 42px;
  padding: 0 12px;
  color: var(--color-text-muted);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-subtle);
}

.se-table td {
  height: 56px;
  padding: 8px 12px;
  border-bottom: 1px solid #edf0f4;
  color: #344054;
  font-size: var(--text-sm);
}

.se-table tbody tr:last-child td {
  border-bottom: 0;
}

.se-table tbody tr:hover {
  background: #fafcff;
}

.se-table tbody tr.is-selected {
  background: var(--color-surface-selected);
}

/* Status pills */
.se-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  line-height: 1;
  font-weight: 650;
  white-space: nowrap;
}

.se-pill-success { color: #087a4b; background: var(--color-success-soft); }
.se-pill-warning { color: #b66a00; background: var(--color-warning-soft); }
.se-pill-danger  { color: #c93438; background: var(--color-danger-soft); }
.se-pill-info    { color: #1456c4; background: var(--color-info-soft); }
.se-pill-neutral { color: #667085; background: #f2f4f7; }
.se-pill-purple  { color: #6244dd; background: var(--color-purple-soft); }

/* Forms */
.se-field {
  display: grid;
  gap: 6px;
}

.se-label {
  color: #344054;
  font-size: var(--text-sm);
  font-weight: 600;
}

.se-input,
.se-select,
.se-textarea {
  width: 100%;
  min-height: 38px;
  padding: 8px 11px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
  transition: border-color var(--duration-fast) var(--ease-standard),
              box-shadow var(--duration-fast) var(--ease-standard);
}

.se-textarea {
  min-height: 92px;
  resize: vertical;
}

.se-input:focus,
.se-select:focus,
.se-textarea:focus {
  border-color: #84adff;
  box-shadow: 0 0 0 3px rgba(23, 105, 255, 0.14);
}

/* Tabs */
.se-tabs {
  display: flex;
  gap: 20px;
  border-bottom: 1px solid var(--color-border);
}

.se-tab {
  position: relative;
  padding: 11px 2px 10px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  text-decoration: none;
}

.se-tab.is-active {
  color: var(--color-primary);
}

.se-tab.is-active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background: var(--color-primary);
}

/* Split-view productivity layout */
.se-split {
  display: grid;
  grid-template-columns: minmax(210px, 280px) minmax(0, 1fr) var(--inspector-w);
  gap: var(--panel-gap);
  align-items: start;
}

.se-inspector {
  position: sticky;
  top: calc(var(--topbar-h) + var(--page-pad-y));
  max-height: calc(100vh - var(--topbar-h) - var(--page-pad-y) * 2);
  overflow: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

/* Two-column workspace with right context */
.se-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) var(--inspector-w);
  gap: var(--panel-gap);
  align-items: start;
}

/* Charts / visualization blocks */
.se-chart {
  min-height: 260px;
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.se-sparkline {
  display: block;
  width: 100%;
  height: 36px;
}

/* Timeline */
.se-timeline {
  position: relative;
  display: grid;
  gap: 16px;
}

.se-timeline::before {
  content: "";
  position: absolute;
  left: 9px;
  top: 8px;
  bottom: 8px;
  width: 1px;
  background: var(--color-border);
}

.se-timeline-item {
  position: relative;
  padding-left: 30px;
}

.se-timeline-dot {
  position: absolute;
  left: 3px;
  top: 4px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 1px var(--color-border-strong);
  background: var(--color-primary);
}

/* Stepper */
.se-stepper {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
  margin: 8px 0 20px;
}

.se-step {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
}

.se-step::before {
  content: "";
  position: absolute;
  top: 13px;
  left: -50%;
  width: 100%;
  height: 1px;
  background: var(--color-border);
  z-index: 0;
}

.se-step:first-child::before {
  display: none;
}

.se-step-index {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: #475467;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
}

.se-step.is-active {
  color: var(--color-primary);
}

.se-step.is-active .se-step-index {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

/* Workflow canvas */
.se-flow-canvas {
  min-height: 620px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background-color: #fff;
  background-image: radial-gradient(#d9dee8 0.7px, transparent 0.7px);
  background-size: 16px 16px;
  overflow: auto;
}

.se-flow-node {
  width: min(360px, 82%);
  margin: 16px auto;
  padding: 12px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: #fff;
  box-shadow: var(--shadow-card);
}

.se-flow-node.is-selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(23, 105, 255, 0.1);
}

/* Empty / loading / error */
.se-empty {
  min-height: 220px;
  display: grid;
  place-items: center;
  text-align: center;
  color: var(--color-text-muted);
}

.se-skeleton {
  border-radius: 6px;
  background: linear-gradient(90deg, #f2f4f7 25%, #fafbfc 50%, #f2f4f7 75%);
  background-size: 200% 100%;
  animation: se-shimmer 1.4s infinite linear;
}

@keyframes se-shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

/* Responsive behavior */
@media (max-width: 1180px) {
  :root {
    --sidebar-w: 208px;
    --inspector-w: 292px;
  }

  .se-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .se-split {
    grid-template-columns: 240px minmax(0, 1fr);
  }

  .se-split > .se-inspector {
    grid-column: 1 / -1;
    position: static;
    max-height: none;
  }
}

@media (max-width: 900px) {
  .se-app {
    grid-template-columns: 1fr;
  }

  .se-topbar {
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  .se-sidebar {
    position: fixed;
    inset: var(--topbar-h) auto 0 0;
    width: min(82vw, 300px);
    z-index: 50;
    transform: translateX(-100%);
    transition: transform var(--duration-slow) var(--ease-standard);
    box-shadow: var(--shadow-float);
  }

  .se-sidebar.is-open {
    transform: translateX(0);
  }

  .se-main {
    grid-column: 1;
  }

  .se-workspace,
  .se-split {
    grid-template-columns: 1fr;
  }

  .se-inspector {
    position: static;
    max-height: none;
  }

  .se-stepper {
    overflow-x: auto;
    grid-template-columns: repeat(6, 130px);
    justify-content: start;
  }
}

@media (max-width: 640px) {
  :root {
    --page-pad-x: 12px;
    --page-pad-y: 12px;
  }

  .se-page-header {
    flex-direction: column;
  }

  .se-actions {
    width: 100%;
  }

  .se-kpi-grid {
    grid-template-columns: 1fr;
  }

  .se-command {
    width: 100%;
  }

  .se-btn {
    min-height: 40px;
  }
}

/* Accessibility helpers */
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}

```

---

# 12. Suggested Front-End Component Inventory

A production implementation should standardize the following components.

### Global
- `AppShell`
- `TopBar`
- `SideNav`
- `CommandPalette`
- `UserMenu`
- `NotificationMenu`

### Navigation
- `Tabs`
- `Breadcrumbs`
- `Pagination`
- `Stepper`

### Data display
- `KpiCard`
- `MetricGauge`
- `Sparkline`
- `StatusPill`
- `DataTable`
- `Timeline`
- `ActivityFeed`
- `EntityList`
- `MapPanel`
- `ChartCard`

### Inputs
- `SearchInput`
- `Select`
- `FilterBar`
- `DateRangePicker`
- `TextField`
- `Textarea`
- `Toggle`
- `Checkbox`
- `TagInput`

### Actions
- `Button`
- `SplitButton`
- `IconButton`
- `BulkActionBar`
- `OverflowMenu`

### Contextual UI
- `InspectorPanel`
- `Drawer`
- `Modal`
- `ConfirmationDialog`
- `Popover`
- `Tooltip`

### Security / operations specific
- `SeverityBadge`
- `RiskScore`
- `SlaTimer`
- `PlaybookProgress`
- `EvidenceCard`
- `AttackPath`
- `PolicyRule`
- `RolloutPhase`
- `WorkflowNode`
- `AiInsight`
- `AiConfidence`

---

# 13. Naming and Content Style

Use clear operational language.

Preferred:
- `Contain Device`
- `Resolve Incident`
- `Simulate Impact`
- `Validate Configuration`
- `Schedule Rollout`
- `View Changelog`

Avoid vague verbs:
- `Proceed`
- `Execute`
- `Do it`
- `Manage`
- `Action`

### Severity naming

Use one controlled vocabulary:

- Critical
- High
- Medium
- Low
- Info

### Operational status naming

Use:
- Online
- Degraded
- Offline
- Maintenance
- Unknown

### Policy states

Use:
- Draft
- Active
- Pending Approval
- Retired

### Workflow states

Use:
- Draft
- Published
- Running
- Succeeded
- Failed
- Paused

---

# 14. Implementation Guidance

### 14.1 Recommended stack behavior

The design maps well to component-driven front ends such as React/Vue/Svelte with a tokenized CSS layer. Keep layout tokens and semantic colors independent from component code.

### 14.2 State ownership

Global state:
- current site group
- current user
- global search
- notifications

Page state:
- filters
- sort
- selected row/object
- time range

Object state:
- open inspector tab
- editable fields
- action confirmation
- loading/error state

### 14.3 URL design

Important application state should be deep-linkable.

Examples:

```text
/overview
/sites
/sites/seattle-gateway
/devices/gw-sea-01
/incidents/INC-2025-05-19-0893
/investigations/seattle-gateway-credential-abuse
/policies/remote-access-hardening
/reports/executive-summary
/provisioning/new-site
/updates/campaigns/q4-security-patch-rollout
/automation/workflows/contain-compromised-gateway
```

---

# 15. Final UIX Recommendation

The strongest design direction for Sentinel Edge is the one already visible across the generated screens:

**Clean Product Workspace + Object-Centric Detail + Split-View Productivity.**

The system should preserve a stable shell while allowing the central work mode to change by task:

- **Overview:** dashboard
- **Sites:** list + map + site inspector
- **Devices:** table + device inspector
- **Incidents:** list + investigation workspace + response inspector
- **AI Investigation:** conversation + evidence workspace + recommendation inspector
- **Policies:** table + editor
- **Reports:** report library + analytics + schedule panel
- **Provisioning:** guided form + readiness checklist
- **Firmware:** rollout planner + campaign inspector
- **Automation:** library + canvas + step inspector

That consistency is the key UX advantage: operators learn the shell once, then reuse the same selection, inspection, filtering, and action patterns throughout the product.
