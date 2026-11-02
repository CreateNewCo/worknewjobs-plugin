"""Offline contract, distribution and MCP transport tests; synthetic data only."""

import copy
import json
import shutil
import tempfile
import threading
import unittest
import zipfile
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from worknew_plugins.contract import ROOT, ContractError, load_contract, validate_arguments, validate_result, public_endpoint
from worknew_plugins.audit import audit_bytes
from worknew_plugins.mcp import Probe
from worknew_plugins.package import build, validate_endpoint, validate_sources, publication_gaps


def sample_result(arguments=None, total=1):
    """Produce public synthetic results without real candidate or employer data."""
    arguments = arguments or {}
    offset, limit = arguments.get("offset", 0), arguments.get("limit", 20)
    fields = {key: "" for key in load_contract()["outputSchema"]["properties"]["results"]["items"]["properties"]["fields"]["required"]}
    fields.update(role="Synthetische testopdracht", client="Afgeschermde testorganisatie", clientLogo=[],
                  hoursPerWeek=None, rateOfPayMin=None, rateOfPayMax=None, duration=None, applicationDeadline=None)
    results = [{"id": f"synthetic-{index}", "fields": copy.deepcopy(fields)}
               for index in range(offset, min(offset + limit, total))]
    more = offset + len(results) < total
    return {"results": results, "pagination": {"offset": offset, "limit": limit, "total": total,
            "hasMore": more, "nextOffset": offset + len(results) if more else None}}


@contextmanager
def mock_mcp(mode="json"):
    """Serve a loopback-only fixture, including session and SSE variants."""
    calls, failures = [], []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def do_POST(self):
            message = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(message)
            method = message["method"]
            if self.headers.get("Authorization"):
                failures.append("Unexpected credentials")
            if "application/json" not in self.headers.get("Accept", "") or "text/event-stream" not in self.headers.get("Accept", ""):
                failures.append("Missing accept types")
            if method != "initialize":
                if self.headers.get("MCP-Session-Id") != "synthetic-session":
                    failures.append("Missing session")
                if self.headers.get("MCP-Protocol-Version") != "2025-11-25":
                    failures.append("Missing protocol version")
            if mode == "http-error":
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if mode == "redirect":
                self.send_response(307)
                self.send_header("Location", "/should-not-follow")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if method == "notifications/initialized":
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if method == "initialize":
                result = {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}},
                          "serverInfo": {"name": "synthetic", "version": "0.0.0"}}
            elif method == "tools/list":
                tool = load_contract()
                if mode == "unsafe-tool":
                    tool["annotations"]["readOnlyHint"] = False
                if mode == "schema-drift":
                    tool["inputSchema"]["additionalProperties"] = True
                if mode == "discovery-pages" and not message.get("params", {}).get("cursor"):
                    result = {"tools": [], "nextCursor": "page-two"}
                else:
                    result = {"tools": [] if mode == "missing-tool" else [tool]}
                if mode == "cursor-loop":
                    result = {"tools": [], "nextCursor": "same"}
            else:
                arguments = message["params"]["arguments"]
                data = sample_result(arguments, 0 if mode == "empty" else 1)
                if mode == "private-output":
                    data["results"][0]["fields"]["fullClient"] = "PRIVATE_SYNTHETIC_VALUE"
                if mode == "wrong-page":
                    data["pagination"]["hasMore"] = True
                result = {"structuredContent": data, "content": [{"type": "text", "text": json.dumps(data)}], "isError": False}
                if mode == "text-leak":
                    result["content"][0]["text"] = "PRIVATE_SYNTHETIC_VALUE"
                if mode == "tool-error":
                    result = {"isError": True, "content": [{"type": "text", "text": "PRIVATE_SYNTHETIC_VALUE"}]}
            envelope = {"jsonrpc": "2.0", "id": message["id"], "result": result}
            if mode == "wrong-id":
                envelope["id"] = 9999
            body = json.dumps(envelope).encode()
            if mode == "malformed":
                body = b"PRIVATE_SYNTHETIC_VALUE"
            if mode == "oversize":
                body = b" " * (2 * 1024 * 1024 + 1)
            if mode == "sse":
                body = b': keepalive\n\nid: prime\ndata:\n\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\ndata: ' + body + b'\n\n'
            self.send_response(200)
            if method == "initialize":
                self.send_header("MCP-Session-Id", "synthetic-session")
            self.send_header("Content-Type", "text/event-stream" if mode == "sse" else "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/mcp", calls, failures
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class ContractTests(unittest.TestCase):
    def test_valid_inputs_and_boundaries(self):
        for arguments in ({}, {"query": "designer", "limit": 1}, {"query": "x" * 500, "limit": 100, "offset": 1000},
                          {"hoursPerWeek": "24-32", "payRate": "100+", "exclusiveOnly": True}):
            validate_arguments(arguments)

    def test_rejects_private_and_invalid_inputs(self):
        cases = [{key: "test"} for key in ("personId", "scope", "brand", "profileInfluence", "includeClosedJobs", "type", "url", "token", "cv")]
        cases += [{"limit": 0}, {"limit": 101}, {"limit": True}, {"offset": -1}, {"query": "x" * 501},
                  {"exclusiveOnly": "false"}, {"hoursPerWeek": "30"}, {"dateRange": "year"}]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ContractError):
                validate_arguments(arguments)

    def test_pagination_empty_final_and_beyond_end(self):
        for arguments, total in (({}, 0), ({"limit": 1}, 3), ({"limit": 1, "offset": 2}, 3), ({"offset": 50}, 1)):
            validate_result(sample_result(arguments, total), arguments)

    def test_rejects_private_fields_and_bad_links(self):
        result = sample_result()
        result["results"][0]["fields"]["personId"] = "private"
        with self.assertRaises(ContractError):
            validate_result(result, {})
        for link in ("https://worknew.co.attacker.invalid/job", "https://user@worknew.co/job", "javascript:alert(1)", "http://worknew.co/job", "https://worknew.co:444/job"):
            result = sample_result()
            result["results"][0]["fields"]["url"] = link
            with self.subTest(link=link), self.assertRaises(ContractError):
                validate_result(result, {})


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        for name in (".claude-plugin", ".codex-plugin", "skills", "contracts", "docs", "assets"):
            shutil.copytree(ROOT / name, self.root / name)
        for name in (".mcp.json", "LICENSE"):
            shutil.copyfile(ROOT / name, self.root / name)

    def tearDown(self):
        self.temp.cleanup()

    def test_safe_reproducible_archives(self):
        (self.root / ".env").write_text("SECRET_MUST_NOT_SHIP")
        (self.root / "skills/get-started/cv.pdf").write_text("PRIVATE_MUST_NOT_SHIP")
        (self.root / "dist").mkdir()
        (self.root / "dist/unrelated.txt").write_text("preserve")
        target = build(self.root, skills_only=True)
        before = {p.name: p.read_bytes() for p in target.glob("*.zip")}
        build(self.root, skills_only=True)
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.glob("*.zip")})
        self.assertEqual((self.root / "dist/unrelated.txt").read_text(), "preserve")
        for path in target.glob("*.zip"):
            with zipfile.ZipFile(path) as archive:
                self.assertIn("LICENSE", archive.namelist())
                self.assertIn("assets/worknew-icon.svg", archive.namelist())
                self.assertNotIn(".env", archive.namelist())
                self.assertNotIn("skills/get-started/cv.pdf", archive.namelist())
                self.assertNotIn(".mcp.json", archive.namelist())
                self.assertNotIn("mcp.json", archive.namelist())
                self.assertIn("skills/get-started/SKILL.md", archive.namelist())
                self.assertIn("skills/search-jobs/SKILL.md", archive.namelist())

    def test_connected_platform_formats(self):
        url = "http://127.0.0.1:8765/mcp"
        target = build(self.root, url, development=True)
        claude = json.loads((target / "claude/.mcp.json").read_text())
        chatgpt = json.loads((target / "chatgpt/mcp.json").read_text())
        self.assertEqual(claude["mcpServers"]["worknew"], {"type": "http", "url": url})
        self.assertEqual(chatgpt["mcpServers"]["worknew"]["type"], "streamable-http")
        self.assertEqual(chatgpt["mcpServers"]["worknew"]["extensions"]["com.openai"]["auth"], {"type": "none"})
        self.assertFalse(json.loads((target / "build-report.json").read_text())["backendVerified"])
        portable = json.loads((target / "chatgpt/plugin.json").read_text())
        self.assertEqual(portable["extensions"]["com.openai"]["onboardingSkill"], "./skills/get-started/SKILL.md")
        self.assertEqual(json.loads((self.root / ".claude-plugin/plugin.json").read_text())["mcpServers"], "./.mcp.json")
        self.assertEqual(portable["license"], "LicenseRef-WorkNew-Proprietary")
        self.assertEqual(len(portable["extensions"]["com.openai"]["review"]["test_cases"]["positive"]), 5)
        self.assertEqual(len(portable["extensions"]["com.openai"]["review"]["test_cases"]["negative"]), 3)
        self.assertIn("release_notes", portable["extensions"]["com.openai"]["publication"])
        self.assertGreaterEqual(len((target / "claude/README.md").read_text().split()), 40)

    def test_skills_only_does_not_declare_a_server_or_remote_review(self):
        target = build(self.root, skills_only=True)
        claude = json.loads((target / "claude/.claude-plugin/plugin.json").read_text())
        portable = json.loads((target / "chatgpt/plugin.json").read_text())
        self.assertNotIn("mcpServers", claude)
        self.assertNotIn("review", portable["extensions"]["com.openai"])

    def test_source_cannot_add_another_server_or_credentials(self):
        path = self.root / ".mcp.json"
        manifest = json.loads(path.read_text())
        manifest["mcpServers"]["worknew"]["headers"] = {"Authorization": "synthetic-secret"}
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ContractError):
            validate_sources(self.root)

    def test_publication_check_catches_undersized_icon_and_missing_recording(self):
        asset = self.root / "assets/worknew-icon.svg"
        asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"/>')
        manifest_path = self.root / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["extensions"]["com.openai"]["review"].pop("demo_recording_url", None)
        manifest_path.write_text(json.dumps(manifest))
        gaps = publication_gaps(self.root)
        self.assertTrue(any("SVG" in gap for gap in gaps))
        self.assertTrue(any("recording" in gap for gap in gaps))
        asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 32 32"/>')
        self.assertFalse(any("SVG" in gap for gap in publication_gaps(self.root)))
        self.assertTrue(any("recording" in gap for gap in publication_gaps(self.root)))

    def test_default_build_uses_only_public_endpoint(self):
        target = build(self.root)
        self.assertEqual(public_endpoint(), "https://mcp.worknew.co/v1/mcp")
        for path in (target / "claude/.mcp.json", target / "chatgpt/mcp.json"):
            self.assertEqual(json.loads(path.read_text())["mcpServers"]["worknew"]["url"], public_endpoint())
        service = json.loads((target / "backend-contract/service.json").read_text())
        self.assertNotIn("backend", service)
        self.assertEqual(service["userAuthentication"], "none")
        self.assertFalse((target / "backend-contract/backend-policy.json").exists())

    def test_nonpublic_endpoint_rejected_even_in_development(self):
        for url in ("https://www.worknew.co/private", "https://mcp.worknew.co/v1", "https://mcp.worknew.co/v1/mcp?token=value"):
            for development in (False, True):
                with self.subTest(url=url, development=development), self.assertRaises(ContractError):
                    build(self.root, url, development=development)

    def test_unsafe_urls(self):
        for url in ("http://www.worknew.co/mcp", "https://user:secret@worknew.co/mcp", "https://worknew.co/mcp?token=secret",
                    "https://worknew.co/mcp#x", "https://example.com/mcp", "http://127.0.0.1:80/mcp", "not-a-url"):
            with self.subTest(url=url), self.assertRaises(ContractError):
                validate_endpoint(url)

    def test_rejects_manifest_drift(self):
        path = self.root / ".claude-plugin/plugin.json"
        manifest = json.loads(path.read_text())
        manifest["version"] = "9.0.0"
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ContractError):
            validate_sources(self.root)

    def test_rejects_symlink_and_missing_skill_reference(self):
        skill = self.root / "skills/get-started/SKILL.md"
        original = skill.read_text()
        skill.write_text(original + "\n[missing](missing.md)\n")
        with self.assertRaises(ContractError):
            build(self.root)
        skill.unlink()
        skill.symlink_to(ROOT / "skills/get-started/SKILL.md")
        with self.assertRaises(ContractError):
            build(self.root)


class PublicationAuditTests(unittest.TestCase):
    def test_rejects_synthetic_private_routes_and_secret_values(self):
        samples = ["/api_" + "a" * 12 + "/jobs", "sk-" + "a" * 24,
                   'api_key="' + "s" * 24 + '"']
        for sample in samples:
            with self.subTest(kind=sample[:4]), self.assertRaises(ContractError) as raised:
                audit_bytes(sample.encode())
            self.assertNotIn(sample, str(raised.exception))

    def test_accepts_public_contract(self):
        audit_bytes((ROOT / "contracts/service.json").read_bytes())
        audit_bytes((ROOT / "contracts/search_jobs.json").read_bytes())


class TransportTests(unittest.TestCase):
    def test_json_sse_empty_and_discovery_pagination(self):
        for mode in ("json", "sse", "empty", "discovery-pages"):
            with self.subTest(mode=mode), mock_mcp(mode) as (url, calls, failures):
                report = Probe(url, development=True).check({"limit": 3})
                self.assertEqual(report["returned"], 0 if mode == "empty" else 1)
                self.assertEqual(calls[-1]["method"], "tools/call")
                self.assertFalse(failures)

    def test_errors_fail_without_leaking_payloads(self):
        for mode in ("http-error", "redirect", "unsafe-tool", "schema-drift", "missing-tool", "cursor-loop", "tool-error",
                     "private-output", "text-leak", "wrong-page", "wrong-id", "malformed", "oversize"):
            with self.subTest(mode=mode), mock_mcp(mode) as (url, calls, failures):
                with self.assertRaises(ContractError) as raised:
                    Probe(url, development=True).check({"limit": 3})
                self.assertNotIn("PRIVATE_SYNTHETIC_VALUE", str(raised.exception))
                if mode == "redirect":
                    self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
