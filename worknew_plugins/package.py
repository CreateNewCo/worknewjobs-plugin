"""Build deterministic, platform-specific packages from reviewed source files."""

import copy
import hashlib
import json
import math
import re
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from .contract import ROOT, ContractError, load_contract, public_endpoint
from .audit import audit_bytes


def json_bytes(value):
    """Serialize generated metadata consistently across platforms."""
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def checked_file(root, relative):
    """Resolve a regular source file, rejecting symlinks and package escapes."""
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise ContractError("A package path escapes the repository") from None
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ContractError("A declared package file is missing or is a symlink")
    return path


def validate_endpoint(url, development=False):
    """Permit only the public service or an explicit loopback development server."""
    if url != public_endpoint() and not development:
        raise ContractError("Production packages must use the canonical public MCP endpoint")
    try:
        parsed = urlsplit(url)
        port = parsed.port
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        valid = ((url == public_endpoint() and parsed.scheme == "https")
                 or (development and local and parsed.scheme in {"https", "http"}))
        valid = valid and bool(parsed.hostname) and bool(parsed.path) and port != 0
        valid = valid and not (parsed.username or parsed.password or parsed.query or parsed.fragment)
        valid = valid and not any(c.isspace() or ord(c) < 32 or c in "<>\\" for c in url)
        valid = valid and not parsed.hostname.endswith((".invalid", ".example", ".test"))
        valid = valid and parsed.hostname not in {"example.com", "example.org", "example.net"}
        if local and not development:
            valid = False
    except (ValueError, AttributeError):
        valid = False
    if not valid:
        raise ContractError("Use a real HTTPS MCP URL without credentials/query/fragment; loopback needs --development")
    return url


def validate_sources(root=ROOT):
    """Validate manifests, skills, links, assets and the backend tool contract."""
    manifests = [json.loads(checked_file(root, p).read_text()) for p in
                 (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")]
    claude, chatgpt = manifests
    for key in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords", "skills", "mcpServers"):
        if claude.get(key) != chatgpt.get(key):
            raise ContractError(f"Source manifests disagree on {key}")
    if claude["name"] != "worknew-jobs" or not re.fullmatch(r"\d+\.\d+\.\d+", claude["version"]):
        raise ContractError("Invalid package identity/version")
    for manifest in manifests:
        if manifest.get("skills") != "./skills/" or manifest.get("mcpServers") != "./.mcp.json" or any(k in manifest for k in ("apps", "hooks")):
            raise ContractError("Source manifests must declare the public MCP config and shared skills")
    mcp = json.loads(checked_file(root, ".mcp.json").read_text())
    if mcp != {"mcpServers": {"worknew": {"type": "http", "url": public_endpoint(root)}}}:
        raise ContractError("Source MCP configuration must declare only the canonical public service")
    checked_file(root, "LICENSE")
    if len(checked_file(root, "docs/package-readme.md").read_text().split()) < 40:
        raise ContractError("The packaged README must contain at least 40 words")
    ui = chatgpt["interface"]
    if ui["displayName"] != claude["displayName"]:
        raise ContractError("Platform display names disagree")
    for key, maximum in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000), ("developerName", 80)):
        value = ui.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ContractError(f"Invalid listing field: {key}")
    prompts = ui.get("defaultPrompt", [])
    if not 1 <= len(prompts) <= 3 or any(not isinstance(p, str) or not p.strip() or len(p) > 128 or "\n" in p or "@" in p for p in prompts):
        raise ContractError("Invalid starter prompts")
    if len(set(prompts)) != len(prompts):
        raise ContractError("Duplicate starter prompts")
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        value = ui.get(key, "")
        parsed = urlsplit(value)
        if len(value) > 1024 or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ContractError(f"Invalid public listing URL: {key}")
    review = chatgpt["extensions"]["com.openai"].get("review", {})
    for kind, count in (("positive", 5), ("negative", 3)):
        cases = review.get("test_cases", {}).get(kind, [])
        if len(cases) != count:
            raise ContractError(f"Review requires {count} {kind} cases")
        required = ("description", "prompt", "expected_behavior") + (("tools_triggered",) if kind == "positive" else ())
        if any(not isinstance(case.get(key), str) or not case[key].strip() for case in cases for key in required):
            raise ContractError("Review cases are incomplete")
    onboarding = chatgpt["extensions"]["com.openai"]["onboardingSkill"]
    if onboarding != "./skills/get-started/SKILL.md":
        raise ContractError("Onboarding must reference the packaged get-started skill")
    checked_file(root, onboarding)
    for name in ("get-started", "search-jobs"):
        path = checked_file(root, f"skills/{name}/SKILL.md")
        text = path.read_text()
        match = re.match(r"\A---\n(.*?)\n---\n(.+)", text, re.S)
        if not match:
            raise ContractError("Skill frontmatter or instructions are missing")
        metadata = yaml.safe_load(match[1])
        if not isinstance(metadata, dict) or metadata.get("name") != name:
            raise ContractError("Skill name does not match its folder")
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            raise ContractError("Invalid skill description")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in target and not target.startswith("#"):
                resolved = path.parent / target.split("#")[0]
                checked_file(root, resolved.relative_to(root))
    assets = set()
    for path in [claude.get("icon"), ui.get("logo"), ui.get("composerIcon"), *ui.get("screenshots", [])]:
        if path is None:
            continue
        if not isinstance(path, str) or not path.startswith("./assets/") or ".." in Path(path).parts:
            raise ContractError("Brand assets must live inside assets/")
        file = checked_file(root, path)
        if file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"} or file.stat().st_size > 5 * 1024 * 1024:
            raise ContractError("Unsupported or oversized brand asset")
        assets.add(path.removeprefix("./"))
    load_contract(root)
    return claude, chatgpt, assets


def build(root=ROOT, endpoint=None, development=False, skills_only=False):
    """Build allowlisted packages and a backend handoff; never modify source manifests."""
    claude, chatgpt, assets = validate_sources(root)
    if skills_only and (endpoint or development):
        raise ContractError("A skills-only build cannot configure a server")
    if not skills_only and endpoint is None:
        if development:
            raise ContractError("--development requires a loopback --mcp-url")
        endpoint = public_endpoint(root)
    if endpoint:
        validate_endpoint(endpoint, development)
    if development and not endpoint:
        raise ContractError("--development requires --mcp-url")
    mode = "development" if development else "connected" if endpoint else "skills-only"
    # Only this tool's generated mode directory is replaced; other dist contents survive.
    dist = root / "dist"
    target = dist / mode
    if dist.is_symlink() or target.is_symlink():
        raise ContractError("Build output may not be a symlink")
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".worknew-", dir=dist) as temporary:
        staging = Path(temporary)
        common = {f"skills/{name}/SKILL.md": checked_file(root, f"skills/{name}/SKILL.md").read_bytes()
                  for name in ("get-started", "search-jobs")}
        common.update({path: checked_file(root, path).read_bytes() for path in assets})
        common["README.md"] = checked_file(root, "docs/package-readme.md").read_bytes()
        if not endpoint:
            common["README.md"] = ("**Skills-only pakket: live zoeken is niet aangesloten. Installeer het verbonden pakket voor zoeken.**\n\n").encode() + common["README.md"]
        common["LICENSE"] = checked_file(root, "LICENSE").read_bytes()
        portable = {k: copy.deepcopy(chatgpt[k]) for k in
                    ("name", "version", "description", "author", "homepage", "repository", "license", "keywords")}
        portable["$schema"] = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
        portable["extensions"] = copy.deepcopy(chatgpt["extensions"])
        portable["extensions"]["com.openai"]["interface"] = copy.deepcopy(chatgpt["interface"])
        claude = copy.deepcopy(claude)
        claude.pop("mcpServers", None)
        if not endpoint:
            portable["extensions"]["com.openai"].pop("review", None)
        variants = {"claude": {".claude-plugin/plugin.json": json_bytes(claude)},
                    "chatgpt": {"plugin.json": json_bytes(portable)}}
        if endpoint:
            claude["mcpServers"] = "./.mcp.json"
            variants["claude"][".claude-plugin/plugin.json"] = json_bytes(claude)
            variants["claude"][".mcp.json"] = json_bytes({"mcpServers": {
                "worknew": {"type": "http", "url": endpoint}}})
            variants["chatgpt"]["mcp.json"] = json_bytes({
                "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                "mcpServers": {"worknew": {"type": "streamable-http", "url": endpoint,
                    "extensions": {"com.openai": {"auth": {"type": "none"}}}}}})
        report = {"version": claude["version"], "mode": mode, "backendVerified": False, "archives": {}}
        for platform, metadata in variants.items():
            files = {**common, **metadata}
            archive_name = f"worknew-jobs-{platform}-{claude['version']}.zip"
            with zipfile.ZipFile(staging / archive_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for relative, contents in sorted(files.items()):
                    audit_bytes(contents)
                    destination = staging / platform / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(contents)
                    entry = zipfile.ZipInfo(relative, date_time=(2020, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(entry, contents)
            report["archives"][archive_name] = hashlib.sha256((staging / archive_name).read_bytes()).hexdigest()
        handoff = staging / "backend-contract"
        handoff.mkdir()
        for name in ("search_jobs.json", "service.json"):
            contents = checked_file(root, f"contracts/{name}").read_bytes()
            audit_bytes(contents)
            (handoff / name).write_bytes(contents)
        contents = checked_file(root, "docs/backend-handoff.md").read_bytes()
        audit_bytes(contents)
        (handoff / "README.md").write_bytes(contents)
        (staging / "build-report.json").write_bytes(json_bytes(report))
        if target.exists():
            shutil.rmtree(target)
        staging.rename(target)
    return target


def publication_gaps(root=ROOT):
    """Report locally detectable submission gaps, without claiming portal acceptance."""
    _, chatgpt, _ = validate_sources(root)
    gaps = []
    ui = chatgpt["interface"]
    for key in ("logo", "composerIcon"):
        relative = ui.get(key)
        if not relative:
            gaps.append(f"Missing listing image: {key}")
            continue
        path = checked_file(root, relative)
        if path.suffix.lower() == ".svg":
            try:
                text = path.read_text()
                if "<!DOCTYPE" in text or "<!ENTITY" in text:
                    raise ValueError("External XML declarations are not supported")
                svg = ET.fromstring(text)
                if svg.tag != "{http://www.w3.org/2000/svg}svg":
                    raise ValueError("Not an SVG")
                # Prefer explicit display dimensions, falling back to the viewBox.
                if "width" in svg.attrib and "height" in svg.attrib:
                    width, height = float(svg.attrib["width"]), float(svg.attrib["height"])
                else:
                    _, _, width, height = map(float, svg.attrib["viewBox"].replace(",", " ").split())
                if not all(math.isfinite(v) for v in (width, height)) or width != height or width < 48:
                    raise ValueError("Image must be square and at least 48 by 48")
            except (ET.ParseError, ValueError, KeyError):
                gaps.append(f"Invalid square SVG dimensions or XML: {key}")
        else:
            gaps.append(f"Raster image requires a separate dimension/format check: {key}")
    review = chatgpt["extensions"]["com.openai"]["review"]
    recording = review.get("demo_recording_url", "")
    parsed = urlsplit(recording)
    if (not recording or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.hostname in {"example.com", "example.org", "example.net"}):
        gaps.append("Missing reviewer-accessible HTTPS video recording URL")
    if not chatgpt["extensions"]["com.openai"].get("publication", {}).get("release_notes", "").strip():
        gaps.append("Missing release notes")
    return gaps
