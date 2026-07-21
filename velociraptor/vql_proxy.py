#!/usr/bin/env python3
"""
CySA Atlas - Velociraptor VQL Proxy
Runs on the host, listens on port 4100, and proxies VQL queries
to the Velociraptor container via `docker exec`.

Backend container can call this via http://172.21.0.1:4100/query
"""

import json
import subprocess
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

VELOCIRAPTOR_CONTAINER = "velociraptor"
VELOCIRAPTOR_BIN = "/usr/local/bin/velociraptor"
VELOCIRAPTOR_API_CONFIG = "/tmp/api_client.yaml"

# Safe VQL queries we allow (whitelist)
ALLOWED_PREFIXES = [
    "SELECT", "select",
]

def run_vql(vql: str, timeout: int = 15) -> list:
    cmd = [
        "docker", "exec", VELOCIRAPTOR_CONTAINER,
        VELOCIRAPTOR_BIN,
        "--api_config", VELOCIRAPTOR_API_CONFIG,
        "query",
        vql,
        "--format", "json"
    ]
    logger.info(f"Running VQL: {vql[:80]}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.warning(f"VQL stderr: {result.stderr[:200]}")
            return []
        raw = result.stdout.strip()
        if not raw or raw == "[]":
            return []
        return json.loads(raw)
    except subprocess.TimeoutExpired:
        logger.error("VQL query timed out")
        return []
    except Exception as e:
        logger.error(f"VQL error: {e}")
        return []


class VQLHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def send_json(self, code: int, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "service": "vql-proxy"})
        elif self.path == "/clients":
            results = run_vql("SELECT client_id, os_info.hostname, os_info.release, last_seen_time, last_ip FROM clients()")
            self.send_json(200, results)
        elif self.path == "/processes":
            results = run_vql("SELECT Pid, Ppid, Name, CommandLine, Username, Exe, MemoryInfo.rss AS Rss FROM pslist()")
            self.send_json(200, results)
        elif self.path == "/netstat":
            results = run_vql("SELECT FamilyString, TypeString, Laddr, Raddr, Status, Pid FROM netstat()")
            self.send_json(200, results)
        elif self.path == "/users":
            results = run_vql("SELECT Name, Uid, Gid, HomeDir, Shell FROM user_accounts()")
            self.send_json(200, results)
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/query":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                vql = payload.get("vql", "").strip()
                if not vql:
                    self.send_json(400, {"error": "Missing vql field"})
                    return
                if not any(vql.startswith(p) for p in ALLOWED_PREFIXES):
                    self.send_json(400, {"error": "Only SELECT queries are allowed"})
                    return
                results = run_vql(vql)
                self.send_json(200, results)
            except json.JSONDecodeError:
                self.send_json(400, {"error": "Invalid JSON body"})
        else:
            self.send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 4100), VQLHandler)
    logger.info("Velociraptor VQL Proxy listening on 0.0.0.0:4100")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down VQL proxy")
        server.shutdown()
