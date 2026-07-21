# CySA Atlas — Project Progress & Pipeline Tracking

This file tracks the active progress, verified integrations, connected modules, and pending roadmap items for the **CySA Atlas SOC** infrastructure.

---

## 📊 Current Integration Status

### 🔗 Connected & Operational Pipelines

| Source Module | Target Module | Data Transmitted | Status | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Wazuh Manager** | **Shuffle Ingestion** | Raw XML/JSON logs (level $\ge 3$) | ✅ Connected | Alert logs appearing in Shuffle trigger webhook |
| **Shuffle Ingestion** | **NestJS Backend** | Relay of raw Wazuh alert data | ✅ Connected | HTTP 200 returned by NestJS `/api/v1/soar/alert` |
| **NestJS Backend** | **Shuffle Playbook** | POST trigger to execute main SOAR pipeline | ⚠️ Pending Code Fix | Attempted trigger returned `HTTP 405` (requires changing `/executions` to `/execute`) |
| **SOAR Playbook** | **freeipapi.com** | Keyless GET Geolocation query for `srcip` | ✅ Connected | Country, City, and ISP successfully retrieved in real-time |
| **SOAR Playbook** | **httpbin.org** | POST query to simulate Threat Intelligence metrics | ✅ Connected | Mock VirusTotal, reputation, and confidence scores returned |
| **SOAR Playbook** | **TheHive 5** | Create Alert with enriched metadata | ✅ Connected | Rich alert generated in TheHive index |
| **SOAR Playbook** | **TheHive 5** | Promote Alert to Case | ✅ Connected | Auto-promoted to Case in TheHive (e.g. Case Number 11) |
| **SOAR Playbook** | **NestJS Approvals** | POST request to register approval action | ✅ Connected | HTTP 201 returned with approval entity details |
| **NestJS approvals** | **Shuffle Callback** | Resume callback with approval/rejection decision | ✅ Connected | Webhook `7f83b19a-d8c3-4e4b-927d-0a887413d9cf` successfully resumes playbook |

---

## 🏗️ Detailed Pipeline Data Flow

The diagram below outlines how logs, enrichments, and human approvals route through the infrastructure:

```
[ Wazuh SIEM ] (Anomalous Log Detected)
      │
      ▼ (ossec.conf Integration)
[ Shuffle Ingestion Hook ] (webhook_b76d3576-f033-47a3-8731-e8ad8aa62942)
      │
      ▼ (Relays payload)
[ NestJS Backend /api/v1/soar/alert ] (Caches IP + Rule ID for 15m)
      │
      ▼ (If same IP + Rule ID occurs 5 times in 5 minutes)
[ Shuffle Playbook Trigger ] (POST /api/v1/workflows/.../execute)
      │
      ├─► [ Geolocation API ] (freeipapi.com queries attacker IP location)
      ├─► [ Threat Intel API ] (httpbin.org mocks VT & Abuse scores)
      │
      ▼ (Combines geo-IP & reputation metrics into Markdown)
[ TheHive 5 Alert ] (Create Alert & Auto-Promote to Case)
      │
      ▼ (Submits callback URL & target info)
[ NestJS approvals ] (Registers PENDING approval & emits WebSocket event)
      │
      ▼ (Analyst clicks "Approve" on Next.js UI)
[ Shuffle Callback Hook ] (webhook_7f83b19a-d8c3-4e4b-927d-0a887413d9cf)
      │
      ▼ (If status == approved)
[ Containment Action ] (Isolate compromised agent / block malicious IP)
```

---

## 🛠️ Infrastructure Health (Azure VM)

| Container Name | Service | Ports | Status | Notes / Config File |
| :--- | :--- | :--- | :--- | :--- |
| `single-node-wazuh.manager-1` | Wazuh Manager | `:1514`, `:1515`, `:55000` | ✅ Up | Config: `wazuh_manager.conf` |
| `single-node-wazuh.indexer-1` | Wazuh Indexer | `:9200` | ✅ Up (Green) | Cluster healthy, SSL fully initialized |
| `cysa-proxy` | Nginx Proxy | `:9201`, `:55001` | ✅ Up | Proxies Wazuh SSL ports as HTTP |
| `shuffle-backend` | Shuffle Backend | `:3001` | ✅ Up | Handles REST execution endpoints |
| `shuffle-frontend` | Shuffle UI | `:3002` | ✅ Up | Host interface for playbooks |
| `thehive` | TheHive 5 | `:9003` | ✅ Up | Case Management, API keys working |
| `thehive-cassandra` | Cassandra DB | *Internal* | ✅ Up (Healthy) | Backend DB for case indexes |
| `thehive-minio` | MinIO Storage | `:9000`, `:9001` | ✅ Up (Healthy) | Stores case attachments & files |
| `tenzir-node` | Tenzir Node | `:5160` | ✅ Up | High-performance log parsing engine |
| `jupyter-workbench` | Jupyter Workbench | `:8888` | ✅ Up (Healthy) | Python notebooks console (token: `cysa-atlas-hunt`) |
| `velociraptor` | Velociraptor Server | `:8889`, `:8001` | ✅ Up | DFIR client manager & VQL query server |

---

## 🗺️ Master Roadmap & Next Actions

### 🟥 Phase 0: Configuration as Code (Current Focus)
*Goal: Recreate compose configurations and maintain repository integrity.*
* [x] **0.1 Recreate Compose Files**: Generate `docker-compose.yml` for Wazuh, Shuffle, and TheHive, saving them to `CySA-config` to replace the lost ones.
* [x] **0.2 Consolidate Directories**: Clean up duplicates and keep `CySA-config` as the single source of truth.

### 🟨 Phase 1: SIEM Configuration & Agent Deployment
*Goal: Get real logs flowing from endpoints into Wazuh.*
* [x] **1.1 Configure Real-Time FIM**: Edit `wazuh_manager.conf` to enable `<directories realtime="yes">` on manager/agent critical paths.
* [x] **1.2 Configure Vulnerability Detection**: Verify database sync times and scan configurations (2,205 vulnerabilities successfully scanned and indexed!).
* [x] **1.3 Deploy Wazuh Agent**: Installed and auto-enrolled Wazuh agent on local workstation (youness-workstation) for real-world telemetry stream.

### 🟩 Phase 2: Unified Frontend Integration & Triage Desk
*Goal: Adapt Next.js panels using Case Context and real SOAR/Case data.*
* [x] **2.1 Resolve NestJS executions trigger URL**: Implemented the `/execute` call in the NestJS controller and client-side helpers.
* [x] **2.2 Case Management TheHive Integration**: Connected NestJS backend proxy endpoints (`GET /api/v1/case/list`, `POST /api/v1/case/create`) and Next.js frontend to list/create real cases from TheHive 5.
* [x] **2.3 SOAR Workflow Visualizer**: Integrated dynamic ReactFlow visualizer reading real-time Shuffle playbooks.
* [x] **2.4 Human-in-the-Loop Approvals Pipeline**: Constrained SOAR approvals console to display pending items *only* after escalation from SIEM/FIM.
* [ ] **2.5 Sandbox upload integration**: Limit `/api/v1/sandbox/status` query details to files matching active Case ID.

### 🟦 Phase 4: Advanced Modules (Threat Hunting & Jupyter)
*Goal: Deploy advanced detection, notebooks, and hunt escalation.*
* [x] **4.1 Deploy Jupyter Workbench**: Spun up `jupyter-workbench` container on port `:8888` (token: `cysa-atlas-hunt`).
* [x] **4.2 Import Sigma Rules**: Created rules repository `/opt/CySA-config/sigma/rules/` with lateral movement, defense evasion, and persistence detections.
* [x] **4.3 Configure NestJS Hunting API**: Implemented `/api/v1/hunting/*` rules list, OpenSearch converter, and Tenzir pipeline search queries.

### 🟪 Phase 5: Digital Forensics & Incident Response (Velociraptor DFIR)
*Goal: Deploy endpoint forensics, query engine, and auto-hunt triggers.*
* [x] **5.1 Deploy Velociraptor Server**: Spun up custom self-initializing `velociraptor` container on ports `8889` (GUI) and `8001` (Agent port).
* [x] **5.2 Write VQL hunting integrations**: Store basic Velociraptor Query Language (VQL) scripts for host artifact collection.
* [x] **5.3 Configure NestJS Forensics API**: Implement endpoints to launch forensic hunts, pull process trees, network state, user accounts, and query results via VQL proxy bridge.

---

## 🧭 Project Status History & Milestones

* **2026-07-21**:
  * Created Python VQL Proxy (`vql_proxy.py`) running as a systemd service (`vql-proxy.service`) on host port `4100`, bridging NestJS backend calls to the running `velociraptor` Docker container via mTLS/API client config.
  * Added live digital forensics endpoints in NestJS backend (`GET /api/v1/forensics/clients`, `/processes`, `/netstat`, `/users`, `POST /hunt`, `POST /escalate-hunt`).
  * Redesigned `DigitalForensics.tsx` into a Tier 3 DFIR console with live agent status, process tree table with memory & root privilege flags, network state matrix with external connection risk badges, system users table, evidence inspector drawer, and an interactive VQL query console with presets.
  * Redesigned Threat Hunting console into a responsive 3-column Single Pane of Glass dashboard.
  * Integrated CISA's official live Known Exploited Vulnerabilities (KEV) JSON feed into the MISP sidebar to track real-world emerging threat TTPs (e.g. CVE-2026-58644).
  * Added an interactive MITRE Tactics coverage widget (blue/purple/rose themed, green color completely removed).
  * Added an inline guide explaining how the Universal Sigma Rule Builder compiles detection parameters to query the raw indices via the Tenzir pipeline.
  * Added a time range query selector (24h/7d/30d/90d) defaulting to "Last 30 Days" to allow immediate retrieval of historical logs.
  * Configured docker-compose volume mounts to pass host-level `/opt/CySA-config` rules directly into `cysa-atlas-backend-1` container in read-only mode.
  * Created Linux-based Sigma rules (`apparmor_denied.yml`, `sudo_root_execution.yml`, `vulnerability_detected.yml`) and verified live index queries directly against Wazuh/OpenSearch indexer (fetched 30 AppArmor logs and 3,181 Vulnerability alerts successfully).
  * Overhauled right panel recommendation console to "AI Recommendations (future Agent)" showcasing Wazuh XML alerts, fast firewall block commands, and Shuffle SOAR Playbook hooks.
* **2026-07-19**:
  * Corrected backend configuration for TheHive, updating `.env` keys (`THEHIVE_API_KEY`) and pointing host queries to internal VM private IP (`10.0.0.4:9003`).
  * Implemented backend routes (`GET /api/v1/case/list` and `POST /api/v1/case/create`) mapping cases and creating entries dynamically on TheHive.
  * Overhauled Case Management dashboard, substituting mock case data with live data fetched directly from TheHive 5.
  * Dynamically mapped cases onto Kanban board columns (`New`, `Triage`, `Investigation`, `Containment`, `Resolved`) and recalculated workload allocations and severity counts.
  * Overhauled SOAR Playbook visualizer to fetch real workflows from Shuffle API, formatting action blocks dynamically for ReactFlow.
  * Implemented detailed Manual Playbook trigger modal in the SOAR UI, supporting target agent selection, IP inputs, and severity indicators.
  * Restricted HIL approvals queue to show items ONLY after the analyst triages and escalates an incident from SIEM/FIM.
* **2026-07-16**:
  * Cloned the `CySA-Atlas` frontend/backend monorepo onto the Azure VM (`/opt/CySA-Atlas`).
  * Built and deployed the platform containers (Next.js frontend, NestJS backend, and PostgreSQL database) directly on the VM.
  * Rebuilt database workflow triggers in Shuffle's OpenSearch instance to route directly to VM port `4000`, completely eliminating Cloudflare tunnels.
  * Replaced mock fleet data with live Wazuh API telemetry on the "Agents" dashboard, including real-time OS/Subnet distributions and dynamic risk scoring.
  * Added a search interface and a functional multi-OS deployment command generator inside the Agents page.
  * Replaced mock EDR threat charts on the "Endpoints Security" dashboard with live parsed categories (SCA rules, authentication, systemd failures) and configured active containment isolation actions.
  * Initialized `wazuh-indexer` security plugin configuration using `securityadmin.sh` with correct admin certificates to restore OpenSearch availability.
  * Configured active Suricata IDS network capturing on VM gateway interface (`eth0`) and mapped `eve.json` log ingestion directly into the Wazuh Manager stack.
  * Connected "Network Security (NDR)" dashboard to live stats, top talkers, and threat flow queries. Implemented persistent local IP block/unblock policies.
  * Integrated "Security Events (SIEM Alerts)" workspace with a NestJS-backed dynamic correlation engine that aggregates raw alerts in 5-minute windows.
  * Connected "Integrity Monitor (FIM)" dashboard to live syscheck queries and implemented persistent analyst approvals and SOAR escalation events.
* **2026-07-15**: 
  * Enrolled and connected local workstation agent (**`youness-workstation`**). Automatically synchronized package inventory (942 packages) and ran vulnerability detection (2,205 CVE findings successfully indexed!).
  * Deployed and started self-initializing **Velociraptor Server** container on ports `:8889` (GUI HTTPS) and `:8001` (Agent communications). Configured automated admin creation.
  * Deployed and started **Jupyter Workbench** container on port `:8888`.
  * Created the **Sigma Rules repository** with rules for PsExec execution, Log Clearing, and Linux Cron persistence.
  * Configured and activated real-time File Integrity Monitoring (FIM) inside Wazuh Manager. Verified instantaneous alert generation (Rule 554) and indexing in OpenSearch upon file additions.
  * Recreated and committed all `docker-compose.yml` configurations for Wazuh, TheHive, Shuffle, and Nginx proxy to both the git repository and active runtime paths.
* **2026-07-14**: Integrated real-time Geolocation (`freeipapi.com`) and simulated Threat Intelligence (`httpbin.org`) into the main playbook. Verified Case creation and details population in TheHive 5 (Case Number 11).
* **2026-07-13**: Resolved HTTP 400 validation issues on NestJS approvals endpoint by routing callbacks through VM public IP. Created local `AGENT_CONTEXT.md` to safely isolate sensitive credentials.
* **2026-07-11**: Restored Wazuh Indexer boot loop caused by invalid Transport SSL cert configuration. Generated security config indexes using `securityadmin.sh`.
* **2026-07-10**: Configured Cassie / Cassandra database cluster bindings for TheHive 5. Established proper indices routing.
* **2026-07-09**: Re-initialized Shuffle SOAR database and backend. Verified API communications.
