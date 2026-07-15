# CySA Atlas — Infrastructure Status Report & Roadmap
*Last updated: 2026-07-13 18:10 UTC*

---

## 🗺️ ACTUAL DIRECTORY STRUCTURE (corrected)

> [!IMPORTANT]
> There are **TWO separate directories** on disk. Compose files live in `/opt/cysa/` (the active runtime). `/opt/CySA-config/` is the **Git config repo** (source of truth).

```
/opt/
├── cysa/                        ← RUNTIME (live docker-compose working dirs)
│   ├── proxy/nginx.conf         ← Nginx reverse proxy config (active)
│   ├── thehive/
│   │   ├── cassandra/           ← Cassandra data volume (bind mount)
│   │   └── minio/               ← MinIO data volume (bind mount)
│   └── wazuh-docker/single-node/
│       └── config/
│           └── wazuh_indexer_ssl_certs/   ← TLS certs (all present)
│
├── CySA-config/                 ← GIT REPO (github: Youness-Tr/CySA-config)
│   ├── AGENT_CONTEXT.md
│   ├── proxy/nginx.conf
│   ├── thehive/                 ← cassandra + minio data (ALSO BIND MOUNTED here)
│   └── wazuh-docker/single-node/config/wazuh_indexer_ssl_certs/
│
└── cysa-config/                 ← LEGACY/DUPLICATE of CySA-config (same structure)
```

> [!WARNING]
> The actual `docker-compose.yml` files are **not found anywhere on disk** — they were run from `/opt/cysa/*/` but those files may have been deleted or never committed. All containers are running from Docker's internal state. This is a config-as-code debt to fix.

---

## ✅ WHAT IS WORKING (Verified)

| Service | Container | Status | Port | Notes |
|---|---|---|---|---|
| **Wazuh Manager** | `single-node-wazuh.manager-1` | ✅ Up 2h | :55000 | API responding, JWT auth works |
| **Wazuh Indexer** | `single-node-wazuh.indexer-1` | ✅ Up 2h, GREEN | :9200 | 194 alerts indexed, 35 shards |
| **Shuffle Backend** | `shuffle-backend` | ✅ Up 2h | :3001→5001 | Health check 200 OK |
| **Shuffle Frontend** | `shuffle-frontend` | ✅ Up 2h | :3002→80 | HTTP 200 OK |
| **Shuffle Orborus** | `shuffle-orborus` | ✅ Up 2h | — | Workflow executor running |
| **Shuffle Database** | `shuffle-database` | ✅ Up 2h | 9200 (internal) | OpenSearch (no TLS) |
| **Shuffle Workers** | `shuffle-workers.1.*` | ✅ Up 2h | :33333 | Swarm service, 1/1 replica |
| **Shuffle Apps** | email, http, shuffle-tools, shuffle-ai, subflow | ✅ Up | :33334-33338 | Swarm services, 2/2 replicas |
| **TheHive** | `thehive` | ✅ Up 2h | :9003→9000 | Login works! API key: `5icIawuRoHIgT52C87umiCZ8gidV8lZf` |
| **TheHive Cassandra** | `thehive-cassandra` | ✅ Up 2h (healthy) | internal | Healthy |
| **TheHive MinIO** | `thehive-minio` | ✅ Up 2h (healthy) | :9000-9001 | Healthy, bucket exists |
| **Cysa Proxy** | `cysa-proxy` | ✅ Up 2h | :9201→indexer, :55001→API | HTTP proxy stripping TLS |
| **Tenzir** | `tenzir-node` | ✅ Up 2h | :1514, :5160 | Running (unexpected — not in original plan) |
| **Docker Swarm** | — | ✅ Active | — | Single-node manager |

---

## ❌ WHAT IS BROKEN / MISSING

| Issue | Severity | Details |
|---|---|---|
| **Wazuh Dashboard MISSING** | 🔴 HIGH | No `wazuh.dashboard` container running. Port :443 returns HTTP 000. Visual UI is down. |
| **No docker-compose.yml files on disk** | 🔴 HIGH | All compose files for wazuh, shuffle, thehive are gone. Need to recreate & commit to git. |
| **No Wazuh agents enrolled** | 🔴 HIGH | Only agent is `wazuh.manager` itself (000). No real endpoints sending logs. |
| **FIM not configured** | 🟡 MEDIUM | `<syscheck>` block is empty in ossec.conf. 0 FIM alerts. |
| **Vulnerability scanning empty** | 🟡 MEDIUM | `<vulnerability-detection>` block empty. 0 CVEs. |
| **Wazuh Dashboard certs missing** | 🟡 MEDIUM | `wazuh.manager.pem` and `wazuh.indexer.pem` in repo but `wazuh.dashboard.pem` missing from `/opt/CySA-config/` |
| **TheHive API key not in env** | 🟡 MEDIUM | API key retrieved (`5icIawuRoHIgT52C87umiCZ8gidV8lZf`) but not in backend .env |
| **No Suricata (NDR)** | 🟢 LOW | Network module will return empty — expected for now |
| **Dead containers** | 🟢 LOW | 5 dead shuffle app containers (old replicas) — cosmetic |
| **Tenzir container** | 🟢 INFO | Running but not planned. Port :1514 conflicts with Wazuh agent port? Check. |
| **cysa-config vs CySA-config** | 🟢 LOW | Two directories (`/opt/cysa-config` and `/opt/CySA-config`) — duplicate/legacy. |

---

## 📊 DATA STATE

| Index | Count | Status |
|---|---|---|
| `wazuh-alerts-4.x-*` | **194 alerts** | ✅ Data flowing (manager self-monitoring) |
| `wazuh-alerts (syscheck/FIM)` | **0** | ❌ FIM not configured |
| `wazuh-states-vulnerabilities-*` | **0** | ❌ Vuln scanner not configured |
| TheHive Cases | — | ✅ DB initialized, no cases yet |
| Shuffle Workflows | 5 workflows | ✅ Loaded |

---

## 🗺️ MASTER ROADMAP — FROM HERE TO FULL VISION

### 🔴 PHASE 0 — Foundation Fixes (Do First — This Week)
*Get infrastructure solid before building on it*

- [ ] **0.1** Recreate & commit all `docker-compose.yml` files to `CySA-config` git repo
  - `wazuh-docker/single-node/docker-compose.yml`
  - `shuffle/docker-compose.yml`
  - `thehive/docker-compose.yml`
  - `proxy/docker-compose.yml`
- [ ] **0.2** Bring up Wazuh Dashboard container (add to compose + restart)
  - Copy `wazuh.dashboard.pem` cert into place
  - Verify HTTPS :443 loads in browser
- [ ] **0.3** Create a `deploy.sh` script for `CySA-config` repo
- [ ] **0.4** Clean up dead containers + consolidate `cysa-config`/`CySA-config` directories
- [ ] **0.5** Verify Tenzir port :1514 doesn't conflict with Wazuh agent port

---

### 🟡 PHASE 1 — SIEM Activation (Week 1-2)
*Get real data flowing into Wazuh*

- [ ] **1.1** Configure `ossec.conf` — enable FIM (syscheck) with real paths
- [ ] **1.2** Configure `ossec.conf` — enable Vulnerability Detection (syscollector + vuln wodle)
- [ ] **1.3** Configure local_rules.xml — add custom detection rules
- [ ] **1.4** Enroll first Wazuh agent (on Azure VM itself or a test endpoint)
- [ ] **1.5** Verify FIM alerts appear in OpenSearch
- [ ] **1.6** Verify CVE data appears in `wazuh-states-vulnerabilities-*`

---

### 🟡 PHASE 2 — SOAR Pipeline (Week 2-3)
*Wire Wazuh → Shuffle → TheHive*

- [x] **2.1** Build Shuffle workflow: Wazuh webhook → alert routing (Wazuh Ingestion Workflow `8468bf60-b789-465f-b98b-06ab757223a8`)
- [x] **2.2** Configure Shuffle → TheHive case creation (using TheHive API key)
- [x] **2.3** Test end-to-end: alert fires → Shuffle routes → TheHive case created (Consolidated in `40642101-1eea-4b86-b1b7-f88404f3b5d5`)
- [x] **2.4** Build SOAR playbook with NestJS `/api/v1/soar/sync` endpoint
- [x] **2.5** Implement interactive active response approval gate with NestJS callback integration

---

### 🟢 PHASE 3 — CySA Atlas Platform (Week 3-4)
*Build the unified frontend + backend*

- [ ] **3.1** Set up NestJS backend `.env` with all Azure service credentials
- [ ] **3.2** Implement `httpsAgent` for Wazuh Indexer + API calls (TLS bypass)
- [ ] **3.3** Test all `/api/v1/*` endpoints against live services
- [ ] **3.4** Set up Next.js frontend → connect to NestJS backend
- [ ] **3.5** Build SOC Dashboard UI (agents, alerts, FIM, vulnerabilities)

---

### 🔵 PHASE 4 — Advanced Modules (Future)
*Threat Intelligence, Hunting, UEBA, Forensics, Sandbox*

- [ ] **4.1** MISP (IOC feeds) — Docker :443
- [ ] **4.2** OpenCTI (ATT&CK mapping) — Docker :8080
- [ ] **4.3** Sigma rules + Jupyter notebooks for threat hunting
- [ ] **4.4** Python ML service for UEBA (anomaly detection)
- [ ] **4.5** Velociraptor for digital forensics
- [ ] **4.6** CAPE Sandbox for malware analysis

---

## 🎯 IMMEDIATE NEXT ACTIONS (Priority Order)

1. **Recreate wazuh-docker docker-compose.yml** including the dashboard service
2. **Bring up Wazuh Dashboard** (add container, use existing TLS certs)
3. **Configure ossec.conf** — enable FIM + vulnerability scanning
4. **Enroll a Wazuh agent** on the Azure VM itself (self-monitoring)
5. **Commit all compose files** to CySA-config git repo

---

## 🔑 CREDENTIALS REFERENCE

> [!NOTE]
> All sensitive passwords, secrets, and keys have been redacted for safe Git tracking. Refer to the local, gitignored `AGENT_CONTEXT.md` file on the Azure VM for the active credentials.

| Service | URL | Username | Password / Key |
|---|---|---|---|
| Wazuh API | `https://<AZURE_VM_PUBLIC_IP>:55000` | `wazuh-wui` | `<REDACTED_WAZUH_API_PASS>` |
| Wazuh Indexer | `https://<AZURE_VM_PUBLIC_IP>:9200` | `admin` | `<REDACTED_WAZUH_INDEXER_PASS>` |
| Wazuh Dashboard | `https://<AZURE_VM_PUBLIC_IP>:443` | ❌ NOT RUNNING | — |
| Wazuh Proxy (HTTP) | `http://<AZURE_VM_PUBLIC_IP>:9201` | — | *(Auth injected by proxy)* |
| TheHive | `http://<AZURE_VM_PUBLIC_IP>:9003` | `admin@thehive.local` | `<REDACTED_THEHIVE_PASS>` |
| TheHive API Key | — | — | `<REDACTED_THEHIVE_API_KEY>` |
| Shuffle Backend | `http://<AZURE_VM_PUBLIC_IP>:3001` | — | *(Login via UI)* |
| Shuffle Frontend | `http://<AZURE_VM_PUBLIC_IP>:3002` | — | *(Login via browser)* |
| MinIO | `http://<AZURE_VM_PUBLIC_IP>:9001` | `admin` | `<REDACTED_MINIO_PASS>` |

*Azure Public IP: **<AZURE_VM_PUBLIC_IP>** | Internal IP: **10.0.0.4***

---

## 🗄️ DATA STORAGE ARCHITECTURE

To ensure high performance and scalability, the data is divided across three dedicated storage layers based on the type of data and who/what accesses it:

### 1. Case Management Layer (TheHive 5)
* **Cassandra (NoSQL Database)**: Stores all Case Management metadata, structural entities, and audit logs:
  * **Alerts**: Ingested log alerts waiting for Tier 1 triage.
  * **Cases**: Incident details, severity, logs of actions, timeline events, and task checklists.
  * **Observables**: Extracted Indicators of Compromise (IOCs) such as attacker IPs, domains, and file hashes.
  * **Tasks & Audit Logs**: Detailed tracking of analyst actions and workflow audits.
* **MinIO (S3 Object Storage)**: Stores raw attachments and binary artifacts:
  * Uploaded malware samples, PCAP captures, system logs, and analyst screenshots.

### 2. SIEM & Log Telemetry Layer (Wazuh Indexer)
* **OpenSearch**: Stores all high-volume telemetry and alerts from the manager and enrolled agents:
  * **`wazuh-alerts-4.x-*` (Security Alerts)**: Log entries that matched a security rule level $\ge 3$.
  * **`wazuh-states-inventory-*-wazuh.manager/agent` (System Inventory)**: State databases collected by `syscollector` (hardware, OS, interfaces, listening ports, running processes, packages).
  * **`wazuh-states-vulnerabilities-*` (Vulnerabilities Database)**: Active CVE scan results matching package inventories.
  * **`wazuh-archives-4.x-*` (Raw Archives)**: (Optional) Raw un-filtered log streams for deep compliance logging.

### 3. SOAR Workflow Layer (Shuffle Database)
* **OpenSearch**: Stores internal automation engine states:
  * Playbook configurations, execution metadata, runtime variables, and webhook trigger registrations.

---

## 💿 MOUNTED VOLUMES REFERENCE

Below is the mapping of host paths and named volumes to their corresponding container directories:

| Service Stack | Local (Host) Mount Path / Volume Name | Container Mount Path | Mount Type & Purpose |
| :--- | :--- | :--- | :--- |
| **Wazuh Manager** | `/opt/cysa/wazuh-docker/single-node/config/wazuh_cluster/wazuh_manager.conf` | `/wazuh-config-mount/etc/ossec.conf` | Read-write file (ossec configuration) |
| | `/opt/cysa/wazuh-docker/single-node/config/wazuh_indexer_ssl_certs/root-ca-manager.pem` | `/etc/ssl/root-ca.pem` | SSL root certificate authority |
| | `/opt/cysa/wazuh-docker/single-node/config/wazuh_indexer_ssl_certs/wazuh.manager.pem` | `/etc/ssl/filebeat.pem` | Manager TLS certificate |
| | `/opt/cysa/wazuh-docker/single-node/config/wazuh_indexer_ssl_certs/wazuh.manager-key.pem` | `/etc/ssl/filebeat.key` | Manager TLS private key |
| | Named Volume: `single-node_wazuh_etc` | `/var/ossec/etc` | Persists manager credentials, keys, rules |
| | Named Volume: `single-node_wazuh_logs` | `/var/ossec/logs` | Persists alerts (`alerts.json`) and system logs |
| | *Other named volumes:* queue, integrations, active_response, api_configuration, agentless, wodles, filebeat_etc, filebeat_var | Corresponding internal paths | Standard system state persistence |
| **Wazuh Indexer** | `/opt/cysa/wazuh-docker/single-node/config/wazuh_indexer/wazuh.indexer.yml` | `/usr/share/wazuh-indexer/config/opensearch.yml` | Indexer database configuration |
| | `/opt/cysa/wazuh-docker/single-node/config/wazuh_indexer/internal_users.yml` | `/usr/share/wazuh-indexer/config/opensearch-security/internal_users.yml` | Custom database user configurations |
| | SSL cert mounts (`root-ca.pem`, `wazuh.indexer.key`, `wazuh.indexer.pem`, `admin.pem`, `admin-key.pem`) | `/usr/share/wazuh-indexer/config/certs/` | Transport layer security certificates |
| | Named Volume: `single-node_wazuh-indexer-data` | `/var/lib/wazuh-indexer` | Persists Elasticsearch/OpenSearch indices |
| **TheHive 5** | `/opt/cysa/thehive/application.conf` | `/etc/thehive/application.conf` | Play framework configuration |
| | `/opt/cysa/thehive/cassandra` | `/var/lib/cassandra` | Persists Cassandra databases |
| | `/opt/cysa/thehive/minio` | `/data` | Persists case files & attachments |
| **Shuffle SOAR** | `/var/run/docker.sock` | `/var/run/docker.sock` | Socket mount (allows Orborus to start Swarm app workers) |
| | Named Volume: `shuffle_shuffle_db` | `/usr/share/opensearch/data` | Persists Shuffle app database |
| | Named Volume: `shuffle_shuffle_apps` | `/shuffle-apps` | Persists hot-loaded playbook apps |
| | Named Volume: `shuffle_shuffle_data` | `/etc/shuffle` | Persists user profiles and credentials |
| **Nginx Proxy** | `/opt/cysa/proxy/nginx.conf` | `/etc/nginx/conf.d/default.conf` | Nginx HTTP proxy routing rules |

