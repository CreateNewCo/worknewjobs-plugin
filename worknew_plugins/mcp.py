"""Bounded MCP 2025-11-25 acceptance probe, not a general-purpose MCP client."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .contract import ContractError, load_contract, validate_arguments, validate_result, validate_tool
from .package import validate_endpoint

PROTOCOL = "2025-11-25"
MAX_BYTES = 2 * 1024 * 1024


class NoRedirects(HTTPRedirectHandler):
    """Never forward a protocol session or search query to a redirected origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Probe:
    """Send only initialization, discovery and one public search request."""

    def __init__(self, endpoint, development=False, timeout=15):
        self.endpoint = validate_endpoint(endpoint, development)
        self.timeout = timeout
        self.opener = build_opener(NoRedirects)
        self.session = None
        self.initialized = False
        self.request_id = 0

    def post(self, method, params=None, notification=False):
        """Exchange bounded JSON/SSE messages and return only the matched result."""
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if not notification:
            self.request_id += 1
            message["id"] = self.request_id
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.initialized:
            headers["MCP-Protocol-Version"] = PROTOCOL
        if self.session:
            headers["MCP-Session-Id"] = self.session
        request = Request(self.endpoint, data=json.dumps(message).encode(), headers=headers, method="POST")
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                session = response.headers.get("Mcp-Session-Id")
                if session:
                    if len(session) > 1024 or any(not 0x21 <= ord(c) <= 0x7E for c in session):
                        raise ContractError("Invalid MCP session header")
                    if method == "initialize":
                        self.session = session
                    elif session != self.session:
                        raise ContractError("Server changed the MCP session")
                if notification:
                    if response.status != 202:
                        raise ContractError("MCP notification was not accepted with HTTP 202")
                    return None
                content_type = response.headers.get_content_type()
                if content_type == "application/json":
                    raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise ContractError("MCP response exceeds the size limit")
                    return self.unwrap(json.loads(raw), message["id"])
                if content_type == "text/event-stream":
                    deadline = time.monotonic() + self.timeout
                    size, data = 0, []
                    while time.monotonic() < deadline:
                        line = response.readline(MAX_BYTES + 1)
                        if not line:
                            break
                        size += len(line)
                        if size > MAX_BYTES:
                            raise ContractError("MCP stream exceeds the size limit")
                        line = line.decode("utf-8").rstrip("\r\n")
                        if line.startswith("data:"):
                            data.append(line[5:].removeprefix(" "))
                        elif not line:
                            payload, data = "\n".join(data), []
                            if payload:
                                event = json.loads(payload)
                                if not isinstance(event, dict):
                                    raise ContractError("Invalid MCP stream event")
                                if event.get("id") == message["id"] and "method" not in event:
                                    return self.unwrap(event, message["id"])
                    raise ContractError("MCP stream ended or timed out before a response; resumable streams are not supported by this probe")
                raise ContractError("Unsupported MCP response content type")
        except HTTPError as error:
            status = error.code
            error.close()
            raise ContractError(f"MCP HTTP request failed with status {status}") from None
        except (URLError, TimeoutError, OSError):
            raise ContractError("MCP transport failed or timed out") from None
        except (json.JSONDecodeError, UnicodeError):
            raise ContractError("MCP returned invalid JSON or UTF-8") from None

    @staticmethod
    def unwrap(message, expected_id):
        """Reject malformed responses without exposing untrusted error messages."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or message.get("id") != expected_id:
            raise ContractError("Invalid JSON-RPC response identity")
        if "error" in message:
            raise ContractError("MCP returned a protocol error")
        if not isinstance(message.get("result"), dict):
            raise ContractError("MCP response is missing an object result")
        return message["result"]

    def check(self, arguments, tool=None):
        """Verify discovery and a successful search, without logging job contents."""
        tool = tool or load_contract()
        validate_arguments(arguments, tool)
        initialized = self.post("initialize", {
            "protocolVersion": PROTOCOL, "capabilities": {},
            "clientInfo": {"name": "worknew-plugin-check", "version": "0.3.0"}})
        if initialized.get("protocolVersion") != PROTOCOL:
            raise ContractError("Backend must support MCP 2025-11-25 for this compatibility probe")
        capabilities = initialized.get("capabilities")
        if not isinstance(capabilities, dict) or not isinstance(capabilities.get("tools"), dict):
            raise ContractError("Backend did not advertise tools capability")
        self.initialized = True
        self.post("notifications/initialized", notification=True)
        tools, seen, cursor = [], set(), None
        for _ in range(20):
            page = self.post("tools/list", {"cursor": cursor} if cursor else {})
            if not isinstance(page.get("tools"), list):
                raise ContractError("Invalid tools/list result")
            tools.extend(page["tools"])
            cursor = page.get("nextCursor")
            if cursor is None:
                break
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise ContractError("Invalid tools/list pagination")
            seen.add(cursor)
        else:
            raise ContractError("Tool discovery exceeded the page limit")
        if len(tools) != 1 or not isinstance(tools[0], dict) or tools[0].get("name") != "search_jobs":
            raise ContractError("Public WorkNew endpoint must expose only search_jobs")
        validate_tool(tools[0], tool)
        called = self.post("tools/call", {"name": "search_jobs", "arguments": arguments})
        if called.get("isError", False) is not False:
            raise ContractError("Search returned a tool error, not zero matches")
        result = called.get("structuredContent")
        validate_result(result, arguments, tool)
        content = called.get("content")
        if not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict) or content[0].get("type") != "text":
            raise ContractError("Search must return one JSON text block alongside structuredContent")
        try:
            same = json.loads(content[0]["text"]) == result
        except (KeyError, TypeError, json.JSONDecodeError):
            same = False
        if not same:
            raise ContractError("Search text differs from the public structured result")
        return {"protocol": PROTOCOL, "tool": "search_jobs", "returned": len(result["results"]),
                "total": result["pagination"]["total"], "hasMore": result["pagination"]["hasMore"]}
