# CySA Atlas — SOC Infrastructure Config

This repository contains the configuration, infrastructure setup, and pipelines for the **CySA Atlas Security Operations Center (SOC)** platform.

---

## 🏗️ Architecture Overview

CySA Atlas integrates industry-standard security tools with a custom Next.js/NestJS application to build a modern, automated, and analyst-driven SOC:

1. **SIEM Layer (Wazuh)**: Ingests logs, monitors file integrity (FIM), and detects system vulnerabilities from enrolled agents.
2. **SOAR Layer (Shuffle)**: Orchestrates automation playbooks, manages alert flows, and coordinates containment actions.
3. **Case Management (TheHive 5)**: Tracks incidents, correlates alerts into cohesive investigations, and maps threat indicators.
4. **Unified Platform (Next.js + NestJS)**: The analyst workspace. Built locally on your development machine, it interfaces with the Azure VM stack via secure REST APIs and WebSockets.

```
+------------+       +-------------------+       +--------------------+       +----------------------+
| Wazuh SIEM | ----> | Shuffle Ingestion | ----> |   NestJS Backend   | ----> |     Shuffle SOAR     |
| Raw Alert  |       |    (Webhook)      |       | Correlation Engine |       | (Playbook Triggered) |
+------------+       +-------------------+       +--------------------+       +----------------------+
                                                                                          |
                                                                                          v
+------------+                                                                  +--------------------+
|  TheHive 5 | <--------------------------------------------------------------- |  Create Case &     |
| Case Mgmt  |                                                                  |  Register Approval |
+------------+                                                                  +--------------------+
```

---

## 📚 Documentation & Status Tracking

Use these documents to track where the project stands, understand how the components interact, and find setup instructions:

* 📈 **[Active Progress & Pipeline Tracking](./PROGRESS_TRACKING.md)**:
  * Real-time update log of verified milestones, active data flows, and current infrastructure checklist.
* 🧭 **[Infrastructure Status & Roadmap](./docs/infrastructure_status.md)**:
  * Current container/service health.
  * Verified workflows and data metrics.
  * Master project roadmap (Phases 0 through 4).
* ⚙️ **[SOC Integration & Pipeline Plan](./docs/cysa_soc_integration_plan.md)**:
  * Detailed REST API specifications for NestJS.
  * Correlation window and grouping architecture.
  * TheHive case promotion and auto-assignment.
  * Interactive containment approval gate callback mechanism.
* 💻 **[NestJS Backend Integration Prompt](./nestjs_prompt.md)** *(Local/Gitignored)*:
  * A pre-formatted AI instructions prompt ready to feed to your local NestJS development agent to spin up the required modules.

---

## 🚀 End-to-End SOAR Pipeline Flow

1. **Wazuh Alert**: Wazuh manager detects an anomaly (e.g. SSH brute force) and forwards it to the Shuffle Ingestion endpoint.
2. **Ingestion Relaying**: Shuffle's Ingestion workflow forwards the raw alert to your NestJS `/api/v1/soar/alert` route.
3. **Correlation**: NestJS groups alerts by `agent.id` and `rule.id` over a 5-minute sliding window. Once matching alerts exceed a threshold of 5, it triggers the Shuffle Playbook on the Azure VM.
4. **Incident Response Playbook**:
   * Creates a security alert in TheHive 5.
   * Auto-promotes the alert to a Case.
   * Registers a pending approval request on NestJS `/api/v1/soar/approvals`.
5. **Interactive Approval Gate**: The Next.js UI prompts the analyst. If approved, NestJS POSTs to Shuffle's callback webhook trigger, resuming the playbook to run automated containment (e.g. isolating the compromised agent).

---

## 🔑 Port & Service Quick Reference (Azure VM)

* **Shuffle Frontend**: `http://<AZURE_VM_PUBLIC_IP>:3002` (Admin ID: `admin@cysa.local`)
* **TheHive 5**: `http://<AZURE_VM_PUBLIC_IP>:9003` (Admin ID: `admin@thehive.local`)
* **Wazuh Proxy (HTTP)**: `http://<AZURE_VM_PUBLIC_IP>:9201` (OpenSearch Indexer endpoint with auto Basic auth)
