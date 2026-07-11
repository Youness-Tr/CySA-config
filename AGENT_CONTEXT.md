# CySA Atlas — Full Infrastructure Context Prompt
*Last verified: 2026-07-11 18:30 UTC — Live diagnostics run on Azure VM*

You are an AI assistant helping build **CySA Atlas**, a full-stack open-source Security Operations Center (SOC) platform. Below is the complete picture of what we are building, the current verified state, the architecture, and all technical details. Use this as your ground truth for every decision.

---

## WHAT WE ARE BUILDING

CySA Atlas is a custom SOC platform consisting of:
- A **SIEM** (Security Information and Event Management) layer — Wazuh
- A **SOAR** (Security Orchestration, Automation and Response) layer — Shuffle
- **Case Management** (incident tracking) — TheHive 5
- A **custom web platform** (Next.js frontend + NestJS backend) that consumes all services via REST APIs and presents a unified SOC dashboard

The platform is designed for a CySA+ (CompTIA Cybersecurity Analyst) training and real-world SOC simulation environment.

---

## INFRASTRUCTURE OVERVIEW

### Cloud: Microsoft Azure VM
- **OS:** Ubuntu 24.04 LTS
- **Architecture:** AMD x86_64
- **RAM:** 16GB (8.7GB used, 6.9GB available)
- **Disk:** 123GB total, 35GB used, 89GB free
- **User:** azureuser
- **Public IP:** 20.91.141.211
- **Internal IP:** 10.0.0.4
- **Docker Mode:** Swarm (single-node manager) + Compose

### Local Machine (Developer)
- Runs the Next.js frontend (:3005) and NestJS backend (:4000)
- Connects to Azure cloud services via public IP
- Uses Docker Compose for local platform stack

---

## ACTUAL DIRECTORY STRUCTURE ON AZURE (VERIFIED)

> **CRITICAL**: Two directories exist. The Git repo is the source of truth.

```
/opt/
├── CySA-config/              ← GIT REPO (github: Youness-Tr/CySA-config) — SOURCE OF TRUTH
│   ├── AGENT_CONTEXT.md      ← This file
│   ├── .gitignore
│   ├── proxy/
│   │   └── nginx.conf        ← Nginx reverse proxy config
│   ├── thehive/
│   │   ├── cassandra/        ← Cassandra data (bind mount — GITIGNORED)
│   │   └── minio/            ← MinIO data (bind mount — GITIGNORED)
│   └── wazuh-docker/
│       └── single-node/
│           └── config/
│               └── wazuh_indexer_ssl_certs/   ← TLS certs (all 9 present)
│
├── cysa/                     ← RUNTIME working dirs (docker-compose projects run here)
│   ├── proxy/nginx.conf      ← copy of above
│   ├── thehive/
│   │   ├── cassandra/        ← same bind mount data
│   │   └── minio/            ← same bind mount data
│   └── wazuh-docker/single-node/config/wazuh_indexer_ssl_certs/
│
└── cysa-config/              ← LEGACY duplicate (same structure, can be removed)
```

> **TODO**: docker-compose.yml files are NOT on disk anywhere. All containers are running
> from Docker's internal state (started previously). Need to recreate and commit them.

---

## SERVICE 1: WAZUH (SIEM) — Full Docker Stack

### Version: 4.14.5
### Compose project: `single-node` — was started from `/opt/cysa/wazuh-docker/single-node/`
### Status: PARTIAL — Manager + Indexer UP, Dashboard MISSING

### Containers (VERIFIED 2026-07-11):
```
single-node-wazuh.manager-1  → wazuh/wazuh-manager:4.14.5   ✅ Up (2h)
single-node-wazuh.indexer-1  → wazuh/wazuh-indexer:4.14.5   ✅ Up (2h), cluster GREEN
wazuh.dashboard              → NOT RUNNING ❌ (needs to be added back)
```

### Ports:
```
:1514  → Wazuh agent log ingestion (TCP/UDP)  ← NOTE: Tenzir also uses :1514, CONFLICT CHECK NEEDED
:1515  → Wazuh agent enrollment/registration
:514   → Syslog (UDP)
:55000 → Wazuh Manager REST API (HTTPS + JWT auth)  ✅ WORKING
:9200  → Wazuh Indexer (OpenSearch, HTTPS + basic auth)  ✅ WORKING
:443   → Wazuh Dashboard (HTTPS) ❌ NOT RESPONDING (container missing)
```

### HTTP Proxy (cysa-proxy container):
```
:9201  → proxies HTTPS :9200 as plain HTTP (strips TLS, injects auth header)
:55001 → proxies HTTPS :55000 as plain HTTP
```
The proxy is an Nginx container using `/opt/cysa/proxy/nginx.conf`

### Credentials:
```
Wazuh API:
  Username: wazuh-wui
  Password: MyS3cr37P450r.*-
  Auth: POST /security/user/authenticate (JWT, expires 15min, cache 14min)

OpenSearch/Indexer:
  Username: admin
  Password: SecretPassword

Dashboard:
  Username: admin (or kibanaserver)
  Password: (TBD — dashboard not running)
```

### TLS Certificates (stored in wazuh_indexer_ssl_certs/):
```
admin-key.pem, admin.pem
root-ca-manager.key, root-ca-manager.pem
root-ca.key, root-ca.pem
wazuh.dashboard-key.pem, wazuh.dashboard.pem    ← dashboard certs EXIST
wazuh.indexer-key.pem, wazuh.indexer.pem
(wazuh.manager.pem MISSING from repo — in volume only)
```

### OpenSearch Indices (VERIFIED):
```
wazuh-alerts-4.x-*                          → 194 alerts total ✅ (self-monitoring only)
wazuh-states-vulnerabilities-wazuh.manager  → 0 docs ❌ (vuln scanner not configured)
wazuh-states-inventory-*/wazuh.manager      → 0 docs (no agents)
```

### Current ossec.conf state (VERIFIED):
```xml
<syscheck>         → EMPTY (FIM NOT configured) ❌
<vulnerability-detection> → EMPTY (vuln scanner NOT configured) ❌
<wodle name="syscollector"> → present but minimal
<wodle name="osquery">      → present but empty
```

### Wazuh Agents (VERIFIED):
```
Agent 000: wazuh.manager (built-in self) — status: active
NO real agents enrolled ❌
```

---

## SERVICE 2: SHUFFLE (SOAR)

### Compose project: `shuffle` — started from `/opt/cysa/shuffle/` (compose file MISSING from disk)
### Status: FULLY WORKING ✅

### Containers (VERIFIED):
```
shuffle-backend   → frikky/shuffle-backend:latest    ✅ Up (2h), :3001→5001
shuffle-frontend  → frikky/shuffle-frontend:latest   ✅ Up (2h), :3002→80
shuffle-orborus   → ghcr.io/shuffle/shuffle-orborus  ✅ Up (2h)
shuffle-database  → opensearchproject/opensearch:2.11.0  ✅ Up (9200 internal)
```

### Docker Swarm Services (Shuffle Apps):
```
shuffle-workers     1/1 replica  :33333  ghcr.io/shuffle/shuffle-worker:latest
shuffle-subflow_1-1-0  2/2 replicas  :33334
shuffle-tools_1-2-0    2/2 replicas  :33335
shuffle-ai_1-1-0       2/2 replicas  :33336
email_1-3-0            2/2 replicas  :33337
http_1-4-0             2/2 replicas  :33338
```

### Credentials:
```
Shuffle UI: http://20.91.141.211:3002 (login via browser, set up first time)
Shuffle Backend: http://20.91.141.211:3001
API Key: retrieve from Shuffle UI profile settings after login
Admin user: admin@cysa.local (verified from logs)
```

### Playbook Status:
- 5 workflows loaded in Shuffle
- Workflow ID: 7faedd29-cc92-4759-809a-6fe150e0631c (from original — verify in UI)
- Shuffle→TheHive case creation: NOT YET BUILT ❌

---

## SERVICE 3: THEHIVE (Case Management)

### Compose project: `thehive` — started from `/opt/cysa/thehive/` (compose file MISSING from disk)
### Status: FULLY WORKING ✅

### Containers (VERIFIED):
```
thehive           → strangebee/thehive:5    ✅ Up (2h), :9003→9000
thehive-cassandra → cassandra:4.1           ✅ Up (2h, healthy)
thehive-minio     → minio/minio             ✅ Up (2h, healthy), :9000-9001
thehive-minio-init → minio/mc              ✅ Exited (0) — bucket created
```

### Credentials (VERIFIED):
```
TheHive login:
  URL: http://20.91.141.211:9003
  Username: admin@thehive.local
  Password: secret
  Login: ✅ VERIFIED working

TheHive API Key: 5icIawuRoHIgT52C87umiCZ8gidV8lZf   ← GENERATED 2026-07-11
  (renew via: POST /api/v0/user/admin@thehive.local/key/renew with basic auth)

MinIO:
  Console: http://20.91.141.211:9001
  Access key: admin
  Secret key: adminadmin
  Bucket: thehive ✅ (created by minio-init)
```

### TheHive application.conf (target: /opt/cysa/thehive/application.conf — currently MISSING):
```hocon
play.http.secret.key="a477be6f719deb7801c2a45f3715f146244d30ea1585a7a91e26822f3f2b905c"
db.janusgraph {
  storage.backend = cql
  storage.hostname = ["thehive-cassandra"]
  storage.cql.keyspace = thehive
  storage.cql.read-consistency-level = ONE
  storage.cql.write-consistency-level = ONE
}
storage {
  provider = s3
  s3 {
    bucket = "thehive"
    endpoint = "http://thehive-minio:9000"
    accessKey = "admin"
    secretKey = "adminadmin"
    region = "us-east-1"
    pathStyleAccess = true
  }
}
```

### TheHive Data State:
```
License: Platinum Trial (15 days from boot)
Cases: 0 (no cases yet)
```

---

## TENZIR (Unplanned — running)

### Status: Running (not in original plan)
```
tenzir-node → tenzir/tenzir:main  ✅ Up (2h)
  Port :1514 → ⚠️ SAME PORT as Wazuh agent ingestion — CHECK FOR CONFLICT
  Port :5160
```
**Action needed**: Determine if Tenzir is intentional and resolve port :1514 conflict.

---

## LOCAL PLATFORM STACK

### Location: CySA-Atlas/ (Git repo — on developer machine)
### Status: NOT YET TESTED against Azure (NestJS .env not filled in)

### Backend .env values needed:
```dotenv
PORT=4000
WAZUH_API_BASE_URL=https://20.91.141.211:55000
WAZUH_API_USERNAME=wazuh-wui
WAZUH_API_PASSWORD=MyS3cr37P450r.*-
WAZUH_INDEXER_BASE_URL=https://20.91.141.211:9200
WAZUH_INDEXER_USERNAME=admin
WAZUH_INDEXER_PASSWORD=SecretPassword
THEHIVE_URL=http://20.91.141.211:9003
THEHIVE_API_KEY=5icIawuRoHIgT52C87umiCZ8gidV8lZf
SHUFFLE_URL=http://20.91.141.211:3001
SHUFFLE_API_KEY=<get from Shuffle UI>
DB_HOST=platform-db
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_NAME=platform
```

### IMPORTANT — TLS on Azure:
- Wazuh Indexer uses HTTPS with self-signed certs
- NestJS must use `httpsAgent({ rejectUnauthorized: false })` for ALL Wazuh calls
- Or use the proxy ports: :9201 (indexer HTTP) and :55001 (API HTTP)

---

## NESTJS BACKEND — API ENDPOINTS

### Authentication pattern:
- Wazuh: POST /security/user/authenticate → JWT token (cached 14min)
- TheHive: Bearer API key in Authorization header
- Shuffle: Bearer API key in Authorization header
- OpenSearch: Basic auth (admin:SecretPassword) or use proxy

### Modules and endpoints:
```
WAZUH MODULE (/api/v1/wazuh/)
  GET  /agents-status          → active/disconnected/pending/total counts
  GET  /agents-list            → all agents: id, name, ip, status, os, lastKeepAlive
  GET  /security-alerts        → last 50 alerts level>=3, sorted desc
  GET  /vulnerability-summary  → CVE summary per agent

FIM MODULE (/api/v1/fim/)
  Queries: OpenSearch wazuh-alerts-* filter: rule.groups=syscheck
  GET  /alerts    → last 50 FIM events
  GET  /summary   → aggregated stats

VULNERABILITY MODULE (/api/v1/wazuh/vulnerabilities/)
  Queries: OpenSearch wazuh-states-vulnerabilities-*
  GET  /           → all CVEs sorted by CVSS desc
  GET  /summary    → by severity, by agent, avg CVSS
  GET  /:agentId   → CVEs for specific agent

NETWORK MODULE (/api/v1/network/)
  Queries: OpenSearch wazuh-alerts-* filter: data.suricata.*
  NOTE: requires Suricata on agents (not configured)

SOAR MODULE (/api/v1/soar/)
  POST /event    → save SOAR event (called by Shuffle)
  POST /sync     → alias for /event
  GET  /events   → all SOAR events sorted by timestamp desc
```

---

## NETWORK / FIREWALL

### Azure Public IP: 20.91.141.211
### Azure NSG Inbound rules needed:
```
Port 22     TCP → SSH
Port 443    TCP → Wazuh Dashboard (❌ container down)
Port 1514   TCP/UDP → Wazuh agents (⚠️ Tenzir conflict check)
Port 1515   TCP → Wazuh enrollment
Port 514    UDP → Syslog
Port 55000  TCP → Wazuh API ✅
Port 9200   TCP → Wazuh Indexer ✅
Port 3001   TCP → Shuffle Backend ✅
Port 3002   TCP → Shuffle Frontend ✅
Port 9003   TCP → TheHive ✅
Port 9000   TCP → MinIO S3 ✅
Port 9001   TCP → MinIO Console ✅
```

### Docker Networks:
```
shuffle_shuffle_network   → bridge, Shuffle + TheHive + Tenzir
single-node_default       → bridge, Wazuh manager + indexer
tenzir-network            → bridge, Tenzir
bridge                    → default (proxy)
ingress                   → swarm overlay (shuffle apps)
shuffle_swarm_executions  → swarm overlay (shuffle workers)
```

---

## GIT REPOSITORIES

### Repo 1: CySA-Atlas (GitHub)
- Contains: local platform (frontend + backend + docker-compose)
- Branch: main — on developer machine

### Repo 2: CySA-config (GitHub: Youness-Tr/CySA-config)
- Location on server: /opt/CySA-config/
- Commits: 1 commit ("Initial CySA infrastructure")
- **CRITICAL GAP**: docker-compose.yml files not yet committed ❌

---

## MASTER ROADMAP

### 🔴 PHASE 0 — Foundation Fixes (CURRENT PRIORITY)
- [ ] 0.1 Recreate all docker-compose.yml files and commit to git
- [ ] 0.2 Bring up Wazuh Dashboard container (add to wazuh compose)
- [ ] 0.3 Create deploy.sh script
- [ ] 0.4 Resolve Tenzir :1514 port conflict with Wazuh
- [ ] 0.5 Clean up dead containers and legacy directories

### 🟡 PHASE 1 — SIEM Activation
- [ ] 1.1 Configure ossec.conf — enable FIM (syscheck) with real paths
- [ ] 1.2 Configure ossec.conf — enable Vulnerability Detection
- [ ] 1.3 Add custom rules in local_rules.xml
- [ ] 1.4 Enroll first Wazuh agent (on Azure VM itself)
- [ ] 1.5 Verify FIM + CVE alerts in OpenSearch

### 🟡 PHASE 2 — SOAR Pipeline
- [ ] 2.1 Build Shuffle workflow: Wazuh webhook → alert routing
- [ ] 2.2 Configure Shuffle → TheHive case creation
- [ ] 2.3 Test end-to-end: alert → Shuffle → TheHive case
- [ ] 2.4 Build NestJS SOAR sync endpoint

### 🟢 PHASE 3 — CySA Atlas Platform (Frontend + Backend)
- [ ] 3.1 Fill NestJS backend .env with Azure credentials
- [ ] 3.2 Implement httpsAgent for Wazuh TLS calls
- [ ] 3.3 Test all /api/v1/* endpoints
- [ ] 3.4 Build SOC Dashboard UI in Next.js

### 🔵 PHASE 4 — Advanced Modules (Future)
- MISP (Threat Intel) → :443
- OpenCTI (ATT&CK) → :8080
- Sigma + Jupyter (Threat Hunting) → :8888
- Python ML UEBA (scikit-learn, Isolation Forest)
- Velociraptor (Digital Forensics) → :8889
- CAPE Sandbox (Malware) → :8000

---

## CURRENT STATUS (VERIFIED 2026-07-11)

### ✅ WORKING:
- Wazuh Manager + Indexer (4.14.5) — API auth working, OpenSearch GREEN, 194 alerts
- Shuffle full stack (backend + frontend + orborus + swarm app workers)
- TheHive + Cassandra + MinIO — login verified, API key: 5icIawuRoHIgT52C87umiCZ8gidV8lZf
- Cysa-proxy Nginx — stripping TLS for Wazuh services at :9201 and :55001
- Docker Swarm single-node manager active

### ❌ BROKEN / MISSING:
- Wazuh Dashboard container — NOT RUNNING (port :443 dead)
- docker-compose.yml files — MISSING FROM DISK (need recreate + git commit)
- Wazuh agents — NONE enrolled (only built-in manager agent 000)
- FIM (syscheck) — NOT CONFIGURED (0 FIM alerts)
- Vulnerability scanning — NOT CONFIGURED (0 CVEs)
- Shuffle→TheHive workflow — NOT BUILT
- NestJS backend .env — NOT CONFIGURED for Azure IPs
- Tenzir port :1514 — POTENTIAL CONFLICT with Wazuh agent port

### 🎯 IMMEDIATE NEXT TASK (Phase 0.1 + 0.2):
Recreate Wazuh docker-compose.yml (with dashboard container) and commit to git.
Then bring up the dashboard so Wazuh is fully operational.

---

## KEY ARCHITECTURAL DECISIONS & LESSONS LEARNED

1. **ARM→AMD migration**: Moved from Oracle Cloud ARM64 to Azure AMD x86_64.
   AMD: all official images work, no workarounds needed.

2. **Two git repos**: CySA-Atlas (platform code) + CySA-config (server configs).
   Config as code: always edit locally → git push → deploy.sh.

3. **TLS everywhere in Wazuh**: All Wazuh services use HTTPS mutual TLS.
   NestJS must use `httpsAgent({rejectUnauthorized:false})` for all calls,
   OR use cysa-proxy ports (:9201 for indexer, :55001 for API) which strip TLS.

4. **Shuffle internal port**: Backend runs on :5001 internally. Docker maps :3001→:5001.

5. **TheHive startup order**: cassandra healthy → minio healthy → minio-init done → thehive.
   Use healthchecks + depends_on with condition: service_healthy.

6. **TheHive storage**: Uses s3/MinIO. MinIO bucket must exist before TheHive starts.

7. **JWT caching**: Wazuh JWT tokens expire 15min. Cache for 14min in NestJS.

8. **Docker Swarm**: Shuffle uses Docker Swarm mode for app worker scaling.
   Both Compose services and Swarm services coexist on this node.

9. **OpenSearch dual use**:
   - Wazuh Indexer (port :9200) → HTTPS + auth, stores security events
   - Shuffle Database (internal) → HTTP, no auth, stores workflows
   These are TWO SEPARATE instances — never mix them.

10. **Proxy design**: cysa-proxy (Nginx) strips TLS from Wazuh services.
    :9201 = Wazuh Indexer (plain HTTP), :55001 = Wazuh API (plain HTTP).
