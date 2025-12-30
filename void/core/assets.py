"""
Asset management and acquisition.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path
from urllib.parse import urlparse

from ..config import Config
from .network import NetworkTools
from .tools.android import ANDROID_PLATFORM_TOOLS_URL, check_android_tools, install_android_platform_tools
from .tools.qualcomm import check_qualcomm_tools


_FIREHOSE_EXTENSIONS = (".mbn", ".elf", ".bin")
_FIREHOSE_INDEX_KEYS = ("sources", "firehose_sources")
_FIREHOSE_INDEX_LIST_KEYS = ("source_indexes", "firehose_source_indexes")


def collect_required_assets() -> list[dict[str, object]]:
    """Return checklist items for required assets and tooling."""
    items: list[dict[str, object]] = []

    android_results = check_android_tools()
    missing_tools = [tool for tool in android_results if not tool.available]
    if missing_tools:
        missing_labels = ", ".join(tool.label for tool in missing_tools)
        items.append(
            {
                "key": "platform_tools",
                "label": "Android platform tools",
                "status": "fail",
                "detail": f"Missing: {missing_labels}.",
                "action": "download",
                "links": [{"label": "Android platform tools", "url": ANDROID_PLATFORM_TOOLS_URL}],
            }
        )
    else:
        versions = ", ".join(
            f"{tool.label} {tool.version}".strip() for tool in android_results if tool.version
        )
        detail = versions or "ADB/Fastboot detected in PATH."
        items.append(
            {
                "key": "platform_tools",
                "label": "Android platform tools",
                "status": "pass",
                "detail": detail,
                "action": "download",
                "links": [],
            }
        )

    firehose_dir = Config.SCRIPTS_DIR / "firehose"
    firehose_files = _list_firehose_files(firehose_dir)
    firehose_sources = _read_firehose_sources()
    firehose_candidates = _find_firehose_candidates(firehose_dir)
    if not firehose_dir.exists():
        items.append(
            {
                "key": "firehose_workspace",
                "label": "Firehose programmer workspace",
                "status": "fail",
                "detail": _firehose_missing_detail(firehose_sources, firehose_candidates),
                "action": _firehose_action(firehose_sources, firehose_candidates),
                "links": [{"label": "Qualcomm support", "url": "https://www.qualcomm.com/support"}],
            }
        )
    elif firehose_files:
        items.append(
            {
                "key": "firehose_workspace",
                "label": "Firehose programmer workspace",
                "status": "pass",
                "detail": f"{len(firehose_files)} programmer(s) available.",
                "action": "generate",
                "links": [],
            }
        )
    else:
        items.append(
            {
                "key": "firehose_workspace",
                "label": "Firehose programmer workspace",
                "status": "warn",
                "detail": _firehose_missing_detail(firehose_sources, firehose_candidates),
                "action": _firehose_action(firehose_sources, firehose_candidates),
                "links": [{"label": "Qualcomm support", "url": "https://www.qualcomm.com/support"}],
            }
        )

    qualcomm_results = check_qualcomm_tools()
    has_qualcomm_tool = any(tool.available for tool in qualcomm_results)
    if has_qualcomm_tool:
        items.append(
            {
                "key": "qualcomm_tools",
                "label": "Qualcomm EDL tools (edl/qdl/emmcdl)",
                "status": "pass",
                "detail": "At least one EDL recovery tool is available.",
                "action": "manual",
                "links": [],
            }
        )
    else:
        items.append(
            {
                "key": "qualcomm_tools",
                "label": "Qualcomm EDL tools (edl/qdl/emmcdl)",
                "status": "warn",
                "detail": "No EDL recovery tools detected. Install vendor-approved tools.",
                "action": "manual",
                "links": [{"label": "Qualcomm support", "url": "https://www.qualcomm.com/support"}],
            }
        )

    return items


def perform_asset_action(key: str, *, force: bool = False) -> dict[str, object]:
    """Run an install/generate action for a checklist item."""
    if key == "platform_tools":
        result = install_android_platform_tools(force=force)
        return _normalize_install_result(result)
    if key == "firehose_workspace":
        return _prepare_firehose_assets()
    return {
        "success": False,
        "message": "No automated action available.",
        "detail": "Use vendor documentation for this requirement.",
    }


def ensure_firehose_workspace() -> dict[str, object]:
    """Create the firehose workspace with guidance when files are missing."""
    Config.ensure_directories()
    firehose_dir = Config.SCRIPTS_DIR / "firehose"
    firehose_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = firehose_dir / "manifest.json"
    if not manifest_path.exists():
        manifest_path.write_text(
            (
                "{\n"
                '  "schema_version": 1,\n'
                '  "description": "OEM firehose programmer inventory",\n'
                '  "created_by": "Void Suite",\n'
                '  "notes": "Add OEM firehose binaries (.mbn/.elf/.bin) to this folder.",\n'
                '  "programmers": []\n'
                "}\n"
            ),
            encoding="utf-8",
        )

    return {
        "success": True,
        "message": "Firehose workspace ready with manifest.",
        "detail": f"Location: {firehose_dir}",
    }


def _download_firehose_sources() -> dict[str, object]:
    """Download firehose programmers from configured sources."""
    result = ensure_firehose_workspace()
    firehose_sources = _read_firehose_sources()
    if not firehose_sources:
        return {
            "success": False,
            "message": "No firehose download sources configured.",
            "detail": "Add OEM firehose binaries manually or configure firehose_sources in config.json.",
        }

    firehose_dir = Config.SCRIPTS_DIR / "firehose"
    downloaded: list[dict[str, str]] = []
    for source in firehose_sources:
        filename = _filename_from_url(source)
        dest = firehose_dir / filename
        if NetworkTools.download_file(source, dest, timeout=Config.TIMEOUT_LONG):
            downloaded.append({"filename": filename, "url": source})

    if not downloaded:
        refreshed_sources = _refresh_firehose_sources_from_indexes()
        if refreshed_sources and refreshed_sources != firehose_sources:
            return _download_firehose_sources()
        return {
            "success": False,
            "message": "Failed to download firehose programmers.",
            "detail": "Verify the URLs are reachable and provide OEM binaries.",
        }

    _append_firehose_manifest(downloaded)
    return {
        "success": True,
        "message": "Firehose programmers downloaded.",
        "detail": f"Downloaded {len(downloaded)} file(s) to {firehose_dir}.",
    }


def _list_firehose_files(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    return [
        path
        for path in base_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _FIREHOSE_EXTENSIONS
    ]


def _read_firehose_sources() -> list[str]:
    config = Config.read_config()
    sources = config.get("firehose_sources", []) if isinstance(config, dict) else []
    if not isinstance(sources, list):
        sources = []
    builtin = _load_builtin_firehose_sources()
    index_sources = _load_firehose_sources_from_indexes(config)
    combined = [str(item) for item in sources if isinstance(item, str) and item.strip()]
    combined.extend(builtin.get("firehose_sources", []))
    combined.extend(index_sources)
    return _unique_sources(combined)


def _firehose_action(sources: list[str], candidates: list[Path]) -> str:
    if sources:
        return "download"
    if candidates:
        return "import"
    return "manual"


def _firehose_missing_detail(sources: list[str], candidates: list[Path]) -> str:
    if sources:
        return "No programmer files found. Download from configured sources."
    if candidates:
        return f"Found {len(candidates)} candidate file(s). Import from known locations."
    return "No programmer files found. Add OEM firehose binaries to the workspace."


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "firehose.bin"


def _append_firehose_manifest(entries: list[dict[str, str]]) -> None:
    manifest_path = Config.SCRIPTS_DIR / "firehose" / "manifest.json"
    manifest = _load_firehose_manifest(manifest_path)
    manifest_entries = manifest.setdefault("programmers", [])
    for entry in entries:
        if entry not in manifest_entries:
            manifest_entries.append(entry)
    manifest_path.write_text(json_dumps(manifest), encoding="utf-8")


def _load_firehose_manifest(path: Path) -> dict[str, object]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {
        "schema_version": 1,
        "description": "OEM firehose programmer inventory",
        "created_by": "Void Suite",
        "notes": "Add OEM firehose binaries (.mbn/.elf/.bin) to this folder.",
        "programmers": [],
    }


def json_dumps(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _prepare_firehose_assets() -> dict[str, object]:
    ensure_firehose_workspace()
    sources = _read_firehose_sources()
    if sources:
        return _download_firehose_sources()
    candidates = _find_firehose_candidates(Config.SCRIPTS_DIR / "firehose")
    if candidates:
        return _import_firehose_candidates(candidates)
    return {
        "success": False,
        "message": "No firehose assets available to import or download.",
        "detail": "Provide OEM firehose binaries or configure firehose_sources in config.json.",
    }


def _find_firehose_candidates(workspace: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    for directory in _firehose_search_paths(workspace):
        if not directory.exists() or not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.is_file() and path.suffix.lower() in _FIREHOSE_EXTENSIONS:
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                candidates.append(path)
    return candidates


def _firehose_search_paths(workspace: Path) -> list[Path]:
    home = Path.home()
    candidates = [
        Config.BASE_DIR / "firehose",
        home / "Downloads",
        home / "Desktop",
        Path.cwd() / "firehose",
        Config.SCRIPTS_DIR / "firehose",
    ]
    return [path for path in candidates if path.resolve() != workspace.resolve()]


def _import_firehose_candidates(candidates: list[Path]) -> dict[str, object]:
    ensure_firehose_workspace()
    firehose_dir = Config.SCRIPTS_DIR / "firehose"
    imported: list[dict[str, str]] = []
    for path in candidates:
        dest = firehose_dir / path.name
        if dest.exists():
            continue
        shutil.copy2(path, dest)
        imported.append({"filename": path.name, "url": f"file://{path}"})
    if not imported:
        return {
            "success": False,
            "message": "No new firehose files imported.",
            "detail": "Candidates were already present in the workspace.",
        }
    _append_firehose_manifest(imported)
    return {
        "success": True,
        "message": "Firehose files imported.",
        "detail": f"Imported {len(imported)} file(s) to {firehose_dir}.",
    }


def _load_firehose_sources_from_indexes(config: dict) -> list[str]:
    builtin = _load_builtin_firehose_sources()
    indexes = config.get("firehose_source_indexes", []) if isinstance(config, dict) else []
    if not isinstance(indexes, list):
        indexes = []
    builtin_indexes = builtin.get("firehose_source_indexes", [])
    if isinstance(builtin_indexes, list):
        indexes.extend(builtin_indexes)
    sources: list[str] = []
    for index in indexes:
        sources.extend(_read_sources_from_index(str(index)))
    return _unique_sources(sources)


def _read_sources_from_index(index: str) -> list[str]:
    path = Path(index)
    if path.exists():
        return _parse_sources_json(path.read_text(encoding="utf-8"))
    Config.ensure_directories()
    cache_path = Config.CACHE_DIR / "firehose_sources.json"
    if NetworkTools.download_file(index, cache_path, timeout=Config.TIMEOUT_MEDIUM):
        return _parse_sources_json(cache_path.read_text(encoding="utf-8"))
    return []


def _parse_sources_json(payload: str) -> list[str]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    for key in _FIREHOSE_INDEX_KEYS:
        sources = data.get(key)
        if isinstance(sources, list):
            return [str(item) for item in sources if isinstance(item, str) and item.strip()]
    return []


def _parse_sources_index_list(payload: str) -> list[str]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    for key in _FIREHOSE_INDEX_LIST_KEYS:
        sources = data.get(key)
        if isinstance(sources, list):
            return [str(item) for item in sources if isinstance(item, str) and item.strip()]
    return []


def _refresh_firehose_sources_from_indexes() -> list[str]:
    config = Config.read_config()
    if not isinstance(config, dict):
        config = {}
    sources = _load_firehose_sources_from_indexes(config)
    if sources:
        _update_config_value("firehose_sources", sources)
    return sources


def _update_config_value(key: str, value: object) -> None:
    config = Config.read_config()
    if not isinstance(config, dict):
        config = {}
    config[key] = value
    Config.write_config(config)


def _load_builtin_firehose_sources() -> dict[str, list[str]]:
    try:
        payload = resources.files("void.data").joinpath("firehose_sources.json").read_text(
            encoding="utf-8"
        )
    except (FileNotFoundError, ModuleNotFoundError):
        return {"firehose_sources": [], "firehose_source_indexes": []}
    sources = _parse_sources_json(payload)
    index_list = _parse_sources_index_list(payload)
    return {
        "firehose_sources": sources,
        "firehose_source_indexes": index_list,
    }


def add_firehose_source(url: str) -> dict[str, object]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return {
            "success": False,
            "message": "Invalid URL.",
            "detail": "Only http/https URLs are supported.",
        }
    config = Config.read_config()
    if not isinstance(config, dict):
        config = {}
    sources = config.get("firehose_sources", [])
    if not isinstance(sources, list):
        sources = []
    sources.append(url.strip())
    config["firehose_sources"] = _unique_sources([str(item) for item in sources if str(item).strip()])
    Config.write_config(config)
    return {
        "success": True,
        "message": "Firehose source added.",
        "detail": url.strip(),
    }


def _unique_sources(items: list[str]) -> list[str]:
    seen = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _normalize_install_result(result: dict[str, object]) -> dict[str, object]:
    status = str(result.get("status", "info"))
    success = status == "pass"
    message = str(result.get("message", "")) if result.get("message") else "Operation complete."
    detail = str(result.get("detail", "")) if result.get("detail") else ""
    normalized = {"success": success, "message": message, "detail": detail, "status": status}
    links = result.get("links")
    if links:
        normalized["links"] = links
    return normalized
