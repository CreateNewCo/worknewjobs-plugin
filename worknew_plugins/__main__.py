"""CLI: python -m worknew_plugins validate|build|check-backend."""

import argparse
import json
import sys

import yaml
from jsonschema.exceptions import SchemaError

from .contract import ContractError, public_endpoint
from .mcp import Probe
from .package import build, validate_sources
from .audit import audit_repository


def main():
    """Run developer commands, keeping server details out of error output."""
    parser = argparse.ArgumentParser(description="Build and check WorkNew public plugins")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Check source metadata, skills and contracts")
    commands.add_parser("audit", help="Scan publishable files for secret patterns and private route references")
    builder = commands.add_parser("build", help="Create deterministic platform folders and ZIPs")
    mode = builder.add_mutually_exclusive_group()
    mode.add_argument("--skills-only", action="store_true", help="Build without a connection")
    mode.add_argument("--mcp-url", help="Defaults to the public endpoint; loopback overrides require --development")
    builder.add_argument("--development", action="store_true", help="Allow loopback HTTP; mark development output")
    checker = commands.add_parser("check-backend", help="Send read-only discovery and one search to a chosen MCP endpoint")
    checker.add_argument("--mcp-url", default=public_endpoint())
    checker.add_argument("--arguments", default='{"query":"product designer","limit":3}', help="JSON search inputs (no CV or contact data)")
    checker.add_argument("--development", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate_sources()
            print("PASS: source manifests, skills, assets and search schemas")
        elif args.command == "audit":
            print(f"PASS: publication audit of {audit_repository()} files (pattern scan, not a security guarantee)")
        elif args.command == "build":
            print(build(endpoint=args.mcp_url, development=args.development, skills_only=args.skills_only))
            print("Built packages; backend availability and directory readiness are not verified.")
        else:
            report = Probe(args.mcp_url, args.development).check(json.loads(args.arguments))
            print(json.dumps(report, indent=2))
    except ContractError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, SchemaError):
        print("ERROR: Invalid or unreadable local configuration; run tests and validate the source files.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
