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

---

## 🗺️ Master Roadmap & Next Actions

### 🟥 Phase 0: Configuration as Code (Current Focus)
*Goal: Recreate compose configurations and maintain repository integrity.*
* [x] **0.1 Recreate Compose Files**: Generate `docker-compose.yml` for Wazuh, Shuffle, and TheHive, saving them to `CySA-config` to replace the lost ones.
* [x] **0.2 Consolidate Directories**: Clean up duplicates and keep `CySA-config` as the single source of truth.

### 🟨 Phase 1: SIEM Configuration & Agent Deployment
*Goal: Get real logs flowing from endpoints into Wazuh.*
* [x] **1.1 Configure Real-Time FIM**: Edit `wazuh_manager.conf` to enable `<directories realtime="yes">` on manager/agent critical paths.
* [ ] **1.2 Configure Vulnerability Detection**: Verify database sync times and scan configurations.
* [ ] **1.3 Deploy Wazuh Agent**: Install the Wazuh agent on the Azure VM host (Agent 001) for local self-monitoring test cases.

### 🟩 Phase 2: Unified Frontend Integration
*Goal: Adapt Next.js panels using Case Context.*
* [ ] **2.1 Resolve NestJS executions trigger URL**: Apply the `/execute` fix in the NestJS controller.
* [ ] **2.2 Threat Hunting Logs Integration**: Ensure `/api/v1/network/search` fetches active case observables from TheHive and appends them to Tenzir queries automatically.
* [ ] **2.3 Sandbox upload integration**: Limit `/api/v1/sandbox/status` query details to files matching active Case ID.

---

## 🧭 Project Status History & Milestones

* **2026-07-15**: Configured and activated real-time File Integrity Monitoring (FIM) inside Wazuh Manager. Verified instantaneous alert generation (Rule 554) and indexing in OpenSearch upon file additions. Also recreated and committed all `docker-compose.yml` configurations for Wazuh, TheHive, Shuffle, and Nginx proxy to both the git repository and active runtime paths.
* **2026-07-14**: Integrated real-time Geolocation (`freeipapi.com`) and simulated Threat Intelligence (`httpbin.org`) into the main playbook. Verified Case creation and details population in TheHive 5 (Case Number 11).
* **2026-07-13**: Resolved HTTP 400 validation issues on NestJS approvals endpoint by routing callbacks through VM public IP. Created local `AGENT_CONTEXT.md` to safely isolate sensitive credentials.
* **2026-07-11**: Restored Wazuh Indexer boot loop caused by invalid Transport SSL cert configuration. Generated security config indexes using `securityadmin.sh`.
