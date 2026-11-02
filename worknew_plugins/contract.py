"""Validate the shared, public search contract without calling the backend."""

import json
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


class ContractError(ValueError):
    """A safe diagnostic which never includes server payloads or credentials."""


def public_endpoint(root=ROOT):
    """Read the public service address without exposing private integration details."""
    return json.loads((root / "contracts/service.json").read_text())["endpoint"]


def load_contract(root=ROOT):
    """Read and validate the canonical tool definition."""
    tool = json.loads((root / "contracts/search_jobs.json").read_text())
    for key in ("inputSchema", "outputSchema"):
        Draft202012Validator.check_schema(tool[key])
    return tool


def validate_schema(schema, value, label):
    """Report the location of invalid data, without including its value."""
    error = next(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value), None)
    if error:
        # Do not include arbitrary server-controlled field names in diagnostics.
        raise ContractError(f"{label} violates {error.validator} in the search contract")


def validate_arguments(arguments, tool=None):
    """Check caller arguments; defaults and public policy are applied by the backend."""
    validate_schema((tool or load_contract())["inputSchema"], arguments, "Arguments")


def validate_result(result, arguments, tool=None):
    """Check schema, canonical links, pagination consistency, and input bounds."""
    tool = tool or load_contract()
    validate_schema(tool["outputSchema"], result, "Result")
    page = result["pagination"]
    count = len(result["results"])
    expected_limit = arguments.get("limit", 20)
    expected_offset = arguments.get("offset", 0)
    if (page["limit"], page["offset"]) != (expected_limit, expected_offset):
        raise ContractError("Backend changed the requested pagination")
    expected_count = min(page["limit"], max(0, page["total"] - page["offset"]))
    if count != expected_count:
        raise ContractError("Result count disagrees with pagination")
    more = page["offset"] + count < page["total"]
    if page["hasMore"] != more or page["nextOffset"] != (page["offset"] + count if more else None):
        raise ContractError("Pagination cursor is inconsistent")
    ids = [job["id"] for job in result["results"]]
    if len(set(ids)) != len(ids):
        raise ContractError("A result page contains duplicate jobs")
    for job in result["results"]:
        link = job["fields"]["url"]
        if not link:
            continue
        try:
            parsed = urlsplit(link)
            valid = (parsed.scheme == "https" and parsed.hostname in {"worknew.co", "www.worknew.co"}
                     and parsed.port in (None, 443) and not parsed.username and not parsed.password
                     and not any(c.isspace() or ord(c) < 32 for c in link) and "\\" not in link)
        except ValueError:
            valid = False
        if not valid:
            raise ContractError("A job has a non-canonical WorkNew link")


def validate_tool(actual, expected=None):
    """Require the reviewed public contract, allowing additional tool metadata."""
    expected = expected or load_contract()
    for key in ("name", "inputSchema", "outputSchema"):
        if actual.get(key) != expected[key]:
            raise ContractError(f"Discovered tool differs from the canonical {key}")
    annotations = actual.get("annotations", {})
    if any(annotations.get(key) is not value for key, value in expected["annotations"].items()):
        raise ContractError("Discovered tool has unexpected safety annotations")
