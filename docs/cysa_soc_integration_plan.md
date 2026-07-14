# CySA Atlas — 3-Tier SOC Backend Integration Plan

This document outlines the detailed architecture and implementation specifications for the **NestJS Backend** (running on your developer machine) to complete the integration with the Azure VM services (Wazuh, Shuffle, TheHive).

---

## 1. Alert Correlation Architecture

Instead of triggering a separate Case and SOAR workflow for every single raw alert (which causes alert fatigue), the correlation engine acts as a gatekeeper.

```
+------------+        +---------------+        +----------------------+        +-----------------+
| Wazuh SIEM | -----> | Shuffle SOAR  | -----> |   NestJS Backend     | -----> |  Shuffle SOAR   |
| Raw Alert  |        | Raw Webhook   |        |  Correlation Engine  |        |  SOAR Pipeline  |
+------------+        +---------------+        +----------------------+        +-----------------+
```

### NestJS Endpoint: `POST /api/v1/soar/alert`
* **Purpose**: Receive raw alerts from Shuffle's webhook relay.
* **Logic**:
  1. Store the incoming alert in a transient database table or memory cache (e.g. Redis) with a TTL of 15 minutes.
  2. Perform correlation queries. For example, group alerts where:
     * `rule.id` is the same (e.g., SSH brute force).
     * `data.srcip` or `agent.id` matches within a sliding window of 5 minutes.
  3. If the count of matching alerts exceeds a threshold (e.g., 5 failed attempts):
     * Consolidate the alerts into a single **Correlated Incident**.
      * Call the Shuffle API (`POST /api/v1/workflows/40642101-1eea-4b86-b1b7-f88404f3b5d5/execute`) to trigger the main SOAR pipeline with the grouped alert details.

### 1.5. SOAR Playbook Enrichment & Ingestion Flow

Once triggered, the main SOAR Playbook (`40642101-1eea-4b86-b1b7-f88404f3b5d5`) automatically executes the following enrichment steps before raising a Case:
1. **IP Geolocation Lookup**: Hits `https://freeipapi.com/api/json/{source_ip}` to retrieve the country name, country code, region, city, and ISP/ASN organization of the attacker.
2. **Threat Intelligence Query (Mocked)**: Calls `https://httpbin.org/anything` with a POST payload to mock threat reputation data, simulating VirusTotal hits, abuse confidence scores, and threat classification.
3. **TheHive Case Creation**: Consolidates the alert metadata, geolocation, and threat intelligence metrics into a rich markdown description and opens a High-Severity Case in TheHive 5.

---

## 2. Interactive Response & Approval Gate

To prevent automated containment actions from accidentally disrupting critical business operations, NestJS acts as the approval manager.

```
+--------------------+            +-------------------+            +---------------------+
|    Shuffle SOAR    | ---------> |  NestJS Backend   | ---------> |  Next.js Dashboard  |
|  Approval Action   |  (Webhook) |  Create Approval  |  (Socket)  |   Approve Prompt    |
+--------------------+            +-------------------+            +---------------------+
          ^                                                                   |
          | (Resume Callback HTTP POST)                                       |
          +-------------------------------------------------------------------+
```

### NestJS Endpoint: `POST /api/v1/soar/approvals`
* **Triggered by**: A custom HTTP action in Shuffle when a critical containment action is initiated.
* **Payload from Shuffle**:
  ```json
  {
    "approval_id": "shuffle-execution-id-or-random-uuid",
    "case_id": "~41005072",
    "action_name": "Isolate Agent / Block IP",
    "target": "185.220.101.50",
    "callback_url": "http://<AZURE_VM_PUBLIC_IP>:3002/api/v1/hooks/webhook_7f83b19a-d8c3-4e4b-927d-0a887413d9cf?agent=001&case=~41005072"
  }
  ```
* **NestJS Logic**:
  1. Save the approval request to your local Database with status `PENDING`.
  2. Broadcast the pending approval to the Next.js frontend (e.g., via WebSockets/Socket.io).
  3. Expose two REST endpoints for the analyst:
     * `POST /api/v1/soar/approvals/:id/approve`
     * `POST /api/v1/soar/approvals/:id/reject`
  4. When the analyst approves the action in your platform:
     * Set status to `APPROVED`.
     * Send an HTTP POST back to Shuffle's `callback_url` with payload `{"status": "approved"}` to resume the playbook.

---

## 3. Case Context API & Module Adaptation

The "Case Context" allows the analyst's workspace to adapt entirely to the active case without leaving the unified platform.

```
                   +----------------------------------+
                   | Next.js Frontend (Case Selected) |
                   +----------------------------------+
                                    |
                        (Activate Case Context)
                                    v
                   +----------------------------------+
                   |      NestJS Backend Router       |
                   +----------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                          |                          |
         v                          v                          v
+------------------+       +------------------+       +------------------+
|   Tenzir Logs    |       |  Malware Sandbox |       |   UEBA Profiles  |
| (Search filter)  |       | (Filter uploads) |       | (Filter user/IP) |
+------------------+       +------------------+       +------------------+
```

### NestJS Implementation:
1. **Case Observables Query**:
   * When a case is opened, query TheHive API: `GET /api/v1/case/{id}/observable`.
   * Extract all observables (e.g., IP: `185.220.101.50`, Hash: `e3b0c442...`).
2. **Context Router**:
   * Maintain the active case ID in the analyst's session context.
   * Modify your module proxy endpoints:
     * **Threat Hunting (`GET /api/v1/network/search`)**: Append the observables to the Tenzir query template automatically (e.g., `where src_ip == 185.220.101.50` or `file_hash == e3b0c442...`).
     * **Malware Sandbox (`GET /api/v1/sandbox/status`)**: Restrict results to files uploaded under that Case ID.
     * **UEBA (`GET /api/v1/ueba/behavior`)**: Query behavior analytics only for the specific usernames or host IPs linked to the active case.

---

## 4. Summary of Required NestJS API Endpoints

Implement these endpoints in your local NestJS codebase:

| Method | Endpoint | Description | Expected Payload |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/soar/alert` | Ingestion endpoint for raw Wazuh alerts (handles correlation) | Raw Wazuh JSON |
| **POST** | `/api/v1/soar/approvals` | Webhook target for Shuffle to register a pending containment action | `{ approval_id, case_id, action_name, target, callback_url }` |
| **GET** | `/api/v1/soar/approvals` | Fetch all pending/history approvals for the analyst | *None* |
| **POST** | `/api/v1/soar/approvals/:id/approve` | API called by Next.js UI when the analyst approves the response | *None* |
| **POST** | `/api/v1/soar/approvals/:id/reject` | API called by Next.js UI when the analyst rejects the response | *None* |
| **GET** | `/api/v1/case/:id/context` | Fetch context details (observables, notes) to adapt other panels | *None* |
