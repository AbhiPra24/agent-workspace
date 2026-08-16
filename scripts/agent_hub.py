#!/usr/bin/env python3
"""
Universal AI Agent Workspace CLI & Manager (`agent_hub.py`)
===========================================================
Unified installer and manager for Skills, MCP Servers, and Agent Rules
across Claude Desktop/Code, Gemini / Antigravity (`agy`), Cursor,
GitHub Copilot, and Windsurf.
"""

import os
import sys
import json
import shutil
import platform
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Try to import yaml, fallback to simple parser if needed
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Try to import rich formatting, fallback to plain text if needed
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False

# Try to load environment variables from .env
try:
    from dotenv import load_dotenv
    WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=WORKSPACE_ROOT / ".env")
except ImportError:
    WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

SKILLS_DIR = WORKSPACE_ROOT / "skills"
MCP_DIR = WORKSPACE_ROOT / "mcp-servers"
TEMPLATES_DIR = WORKSPACE_ROOT / "templates"
REGISTRY_FILE = MCP_DIR / "registry.json"


# ==============================================================================
# Terminal Logging Helpers
# ==============================================================================

def log_info(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold cyan]ℹ[/bold cyan] {msg}")
    else:
        print(f"[INFO] {msg}")


def log_success(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold green]✔[/bold green] {msg}")
    else:
        print(f"[SUCCESS] {msg}")


def log_warning(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold yellow]⚠[/bold yellow] {msg}")
    else:
        print(f"[WARNING] {msg}")


def log_error(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold red]✖[/bold red] {msg}")
    else:
        print(f"[ERROR] {msg}")


# ==============================================================================
# Helper Utilities & Frontmatter Parsers
# ==============================================================================

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extracts YAML frontmatter and markdown body from a skill file."""
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    fm_raw = parts[1]
    body = parts[2].strip()
    
    if HAS_YAML:
        try:
            metadata = yaml.safe_load(fm_raw) or {}
            if isinstance(metadata, dict):
                return metadata, body
        except Exception:
            pass
            
    # Standalone robust fallback parser for top-level YAML keys & folded blocks
    metadata = {}
    lines = fm_raw.splitlines()
    current_key = None
    multiline_accum = []
    
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        # Top-level key has no leading whitespace and contains ':'
        if not line[0].isspace() and ":" in line:
            if current_key and multiline_accum:
                metadata[current_key] = " ".join(multiline_accum).strip()
                multiline_accum = []
            k, v = line.split(":", 1)
            current_key = k.strip()
            v_clean = v.strip()
            if v_clean in [">-", ">", "|", "|-"]:
                multiline_accum = []
            else:
                metadata[current_key] = v_clean.strip("\"'")
                current_key = None
        elif current_key and (line.startswith("  ") or line.startswith("\t")):
            multiline_accum.append(line.strip())
        else:
            if current_key and multiline_accum:
                metadata[current_key] = " ".join(multiline_accum).strip()
                multiline_accum = []
            current_key = None
            
    if current_key and multiline_accum:
        metadata[current_key] = " ".join(multiline_accum).strip()
        
    return metadata, body


def get_all_skills() -> Dict[str, Dict[str, Any]]:
    """Discovers and parses all skills in the workspace."""
    skills = {}
    if not SKILLS_DIR.exists():
        return skills
        
    for item in sorted(SKILLS_DIR.iterdir()):
        if item.is_dir():
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text(encoding="utf-8")
                metadata, body = parse_frontmatter(content)
                name = metadata.get("name", item.name)
                skills[name] = {
                    "name": name,
                    "folder": item.name,
                    "description": metadata.get("description", "No description provided."),
                    "parameters": metadata.get("parameters", {}),
                    "path": skill_file,
                    "content": body,
                    "raw": content,
                }
    return skills


def get_mcp_registry() -> Dict[str, Any]:
    """Loads the master MCP registry."""
    if not REGISTRY_FILE.exists():
        return {"servers": {}}
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log_error(f"Failed to parse MCP registry: {e}")
        return {"servers": {}}


def get_platform_paths() -> Dict[str, Dict[str, Path]]:
    """Resolves standard target config paths for various AI agent environments."""
    home = Path.home()
    system = platform.system()
    
    # Claude Desktop
    if system == "Darwin":
        claude_desktop_dir = home / "Library" / "Application Support" / "Claude"
    elif system == "Windows":
        app_data = os.getenv("APPDATA", str(home / "AppData" / "Roaming"))
        claude_desktop_dir = Path(app_data) / "Claude"
    else:
        claude_desktop_dir = home / ".config" / "Claude"
        
    return {
        "claude_desktop": {
            "dir": claude_desktop_dir,
            "mcp_config": claude_desktop_dir / "claude_desktop_config.json"
        },
        "claude_code": {
            "dir": home / ".claude",
            "workspace_rules": WORKSPACE_ROOT / "CLAUDE.md"
        },
        "cursor": {
            "dir": WORKSPACE_ROOT / ".cursor",
            "rules_dir": WORKSPACE_ROOT / ".cursor" / "rules",
            "mcp_config": WORKSPACE_ROOT / ".cursor" / "mcp.json"
        },
        "agy": {
            "dir": home / ".gemini" / "antigravity-cli",
            "workspace_skills": WORKSPACE_ROOT / ".agents" / "skills",
            "global_skills": home / ".gemini" / "antigravity-cli" / "skills",
            "mcp_config": home / ".gemini" / "antigravity-cli" / "mcp"
        },
        "copilot": {
            "dir": WORKSPACE_ROOT / ".github",
            "instructions": WORKSPACE_ROOT / ".github" / "copilot-instructions.md",
            "vscode_mcp": WORKSPACE_ROOT / ".vscode" / "mcp.json"
        },
        "windsurf": {
            "dir": home / ".codeium" / "windsurf",
            "mcp_config": home / ".codeium" / "windsurf" / "mcp_config.json",
            "workspace_rules": WORKSPACE_ROOT / ".windsurfrules"
        }
    }


# ==============================================================================
# Command: Doctor (System & Configuration Health Check)
# ==============================================================================

def cmd_doctor(args: argparse.Namespace):
    """Performs system diagnostic check for runtimes and AI client configs."""
    log_info("Running AI Agent Workspace Diagnostics...")
    
    runtimes = [
        ("Python 3", ["python3", "--version"]),
        ("Node.js", ["node", "--version"]),
        ("npx", ["npx", "--version"]),
        ("uv / uvx", ["uv", "--version"]),
        ("Docker", ["docker", "--version"]),
        ("Git", ["git", "--version"]),
    ]
    
    runtime_results = []
    for name, cmd in runtimes:
        is_installed = shutil.which(cmd[0]) is not None
        version_str = "Not Found"
        if is_installed:
            try:
                import subprocess
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
                out = res.stdout.strip() or res.stderr.strip()
                version_str = out.splitlines()[0] if out else "Installed"
            except Exception:
                version_str = "Installed"
        runtime_results.append((name, is_installed, version_str))
        
    paths = get_platform_paths()
    platforms = [
        ("Claude Desktop", paths["claude_desktop"]["dir"].exists(), str(paths["claude_desktop"]["mcp_config"])),
        ("Antigravity / Gemini", paths["agy"]["dir"].exists(), str(paths["agy"]["dir"])),
        ("Cursor", (WORKSPACE_ROOT / ".cursor").exists() or (Path.home() / ".cursor").exists(), str(paths["cursor"]["rules_dir"])),
        ("GitHub Copilot / VS Code", (WORKSPACE_ROOT / ".github").exists() or (WORKSPACE_ROOT / ".vscode").exists(), str(paths["copilot"]["instructions"])),
        ("Windsurf", paths["windsurf"]["dir"].exists() or (WORKSPACE_ROOT / ".windsurfrules").exists(), str(paths["windsurf"]["mcp_config"])),
    ]
    
    if HAS_RICH and console:
        rt_table = Table(title="🔧 System Runtimes & Dependencies")
        rt_table.add_column("Runtime", style="cyan", no_wrap=True)
        rt_table.add_column("Status", justify="center")
        rt_table.add_column("Details", style="dim")
        
        for name, ok, ver in runtime_results:
            status = "[bold green]✔ OK[/bold green]" if ok else "[bold yellow]⚠ Missing[/bold yellow]"
            rt_table.add_row(name, status, ver)
        console.print(rt_table)
        console.print()
        
        plat_table = Table(title="🤖 Detected AI Client Environments")
        plat_table.add_column("Platform", style="magenta", no_wrap=True)
        plat_table.add_column("Detected", justify="center")
        plat_table.add_column("Target Path", style="dim")
        
        for name, detected, target_path in platforms:
            status = "[bold green]Detected[/bold green]" if detected else "[dim]Not Detected[/dim]"
            plat_table.add_row(name, status, target_path)
        console.print(plat_table)
    else:
        print("\n--- Runtimes ---")
        for name, ok, ver in runtime_results:
            print(f"[{'OK' if ok else 'MISSING'}] {name}: {ver}")
        print("\n--- Detected Platforms ---")
        for name, detected, target_path in platforms:
            print(f"[{'YES' if detected else 'NO'}] {name} -> {target_path}")
            
    log_success("Diagnostic check complete.")


# ==============================================================================
# Command: List Skills
# ==============================================================================

def cmd_list_skills(args: argparse.Namespace):
    """Lists all available agent skills."""
    skills = get_all_skills()
    if not skills:
        log_warning("No skills found in skills/ directory.")
        return
        
    if HAS_RICH and console:
        table = Table(title=f"📦 Available AI Agent Skills ({len(skills)} total)")
        table.add_column("Skill Name", style="bold cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Folder", style="dim")
        
        for name, info in skills.items():
            table.add_row(name, info["description"], info["folder"])
        console.print(table)
    else:
        print(f"\nAvailable Skills ({len(skills)} total):")
        for name, info in skills.items():
            print(f"- {name}: {info['description']} (in skills/{info['folder']})")


# ==============================================================================
# Command: List MCP Servers
# ==============================================================================

def cmd_list_mcp(args: argparse.Namespace):
    """Lists all MCP server presets from the registry."""
    registry = get_mcp_registry()
    servers = registry.get("servers", {})
    if not servers:
        log_warning("No MCP servers found in mcp-servers/registry.json.")
        return
        
    if HAS_RICH and console:
        table = Table(title=f"🔌 Available MCP Server Presets ({len(servers)} total)")
        table.add_column("Preset Key", style="bold cyan", no_wrap=True)
        table.add_column("Name", style="bold white")
        table.add_column("Category", style="yellow")
        table.add_column("Command", style="green")
        table.add_column("Required Env", style="magenta")
        table.add_column("Description", style="dim")
        
        for key, s in servers.items():
            env_keys = list(s.get("env", {}).keys())
            env_status = []
            for ek in env_keys:
                is_set = os.getenv(ek) is not None
                color = "green" if is_set else "red"
                env_status.append(f"[{color}]{ek}[/{color}]")
            env_str = ", ".join(env_status) if env_status else "[dim]None[/dim]"
            
            cmd_full = f"{s.get('command', '')} {' '.join(s.get('args', []))}"
            if len(cmd_full) > 28:
                cmd_full = cmd_full[:25] + "..."
                
            table.add_row(key, s.get("name", key), s.get("category", "general"), cmd_full, env_str, s.get("description", ""))
        console.print(table)
    else:
        print(f"\nAvailable MCP Presets ({len(servers)} total):")
        for key, s in servers.items():
            print(f"- [{key}] {s.get('name', key)} ({s.get('category', 'general')}): {s.get('description', '')}")


# ==============================================================================
# Command: Install Skills
# ==============================================================================

def cmd_install_skills(args: argparse.Namespace):
    """Installs or exports skills to the target platform."""
    skills = get_all_skills()
    if not skills:
        log_error("No skills found to install.")
        return
        
    target = args.target.lower()
    selected_skill = args.name.lower() if args.name else "all"
    
    target_skills = skills if selected_skill == "all" else {k: v for k, v in skills.items() if k.lower() == selected_skill}
    if not target_skills:
        log_error(f"Skill '{args.name}' not found. Use 'list-skills' to see available skills.")
        return
        
    paths = get_platform_paths()
    log_info(f"Installing {len(target_skills)} skill(s) -> Target: [bold]{target.upper()}[/bold]")
    
    # 1. Antigravity / Gemini CLI (`.agents/skills/`)
    if target in ["agy", "gemini", "all"]:
        dest_dir = paths["agy"]["workspace_skills"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        for name, info in target_skills.items():
            skill_dest = dest_dir / info["folder"]
            skill_dest.mkdir(parents=True, exist_ok=True)
            (skill_dest / "SKILL.md").write_text(info["raw"], encoding="utf-8")
        log_success(f"Installed {len(target_skills)} skills to Antigravity workspace: {dest_dir}")
        
    # 2. Cursor Rules (`.cursor/rules/*.mdc`)
    if target in ["cursor", "all"]:
        rules_dir = paths["cursor"]["rules_dir"]
        rules_dir.mkdir(parents=True, exist_ok=True)
        for name, info in target_skills.items():
            mdc_file = rules_dir / f"{name}.mdc"
            mdc_content = f"""---
description: {info['description']}
globs: *
alwaysApply: false
---

# {name.replace('-', ' ').title()}

{info['content']}
"""
            mdc_file.write_text(mdc_content, encoding="utf-8")
        log_success(f"Exported {len(target_skills)} Cursor MDC rules to: {rules_dir}")
        
    # 3. Claude Code / CLAUDE.md & Custom Instructions
    if target in ["claude", "all"]:
        claude_file = paths["claude_code"]["workspace_rules"]
        skills_summary = []
        for name, info in target_skills.items():
            skills_summary.append(f"### {name}\n**Description**: {info['description']}\n\n{info['content']}\n")
            
        claude_text = f"""# Claude Workspace Guidelines & Active Skills

This repository is equipped with modular AI Agent skills.

## Quickstart & Workflows
- Check environment: `make doctor`
- List skills & MCP servers: `make list`
- Run test validations: `make test`

## Active Skills & Capabilities
{chr(10).join(skills_summary)}
"""
        claude_file.write_text(claude_text, encoding="utf-8")
        log_success(f"Generated Claude workspace rules: {claude_file}")
        
    # 4. GitHub Copilot (`.github/copilot-instructions.md`)
    if target in ["copilot", "vscode", "all"]:
        copilot_dir = paths["copilot"]["dir"]
        copilot_dir.mkdir(parents=True, exist_ok=True)
        copilot_file = paths["copilot"]["instructions"]
        skills_summary = []
        for name, info in target_skills.items():
            skills_summary.append(f"- **{name}**: {info['description']}")
            
        copilot_text = f"""# GitHub Copilot Custom Instructions

## Project Guidelines
- Modular, well-typed Python (3.9+) and TypeScript codebase.
- Adhere strictly to the Model Context Protocol standards for MCP servers.
- Use `pydantic` schemas for validation and `rich` for CLI output formatting.

## Registered Agent Skills
{chr(10).join(skills_summary)}
"""
        copilot_file.write_text(copilot_text, encoding="utf-8")
        log_success(f"Generated Copilot custom instructions: {copilot_file}")
        
    # 5. Windsurf (`.windsurfrules`)
    if target in ["windsurf", "all"]:
        windsurf_file = paths["windsurf"]["workspace_rules"]
        skills_summary = []
        for name, info in target_skills.items():
            skills_summary.append(f"- **{name}**: {info['description']}")
            
        windsurf_text = f"""# Windsurf Cascade Rules & Agent Skills

## Active Agent Skills
{chr(10).join(skills_summary)}

## Standards
- Clean modular components, comprehensive testing, and strict schema validation.
"""
        windsurf_file.write_text(windsurf_text, encoding="utf-8")
        log_success(f"Generated Windsurf workspace rules: {windsurf_file}")


# ==============================================================================
# Command: Install / Merge MCP Servers
# ==============================================================================

def resolve_mcp_config(server_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves environment variables and paths in an MCP server configuration."""
    cfg = {
        "command": server_spec.get("command", "npx"),
        "args": list(server_spec.get("args", [])),
    }
    
    # Process args template replacements
    processed_args = []
    for arg in cfg["args"]:
        arg_resolved = arg.replace("${WORKSPACE_DIR:-.}", str(WORKSPACE_ROOT))
        arg_resolved = arg_resolved.replace("${SQLITE_DB_PATH:-./workspace.db}", str(WORKSPACE_ROOT / "workspace.db"))
        arg_resolved = arg_resolved.replace("${DATABASE_URL}", os.getenv("DATABASE_URL", "postgresql://localhost:5432/postgres"))
        processed_args.append(arg_resolved)
    cfg["args"] = processed_args
    
    # Process env vars
    env_vars = {}
    for k, v in server_spec.get("env", {}).items():
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            var_name = v[2:-1]
            env_vars[k] = os.getenv(var_name, "")
        else:
            env_vars[k] = str(v)
            
    if env_vars:
        cfg["env"] = env_vars
        
    return cfg


def cmd_install_mcp(args: argparse.Namespace):
    """Merges selected MCP servers into the target platform's JSON configuration."""
    registry = get_mcp_registry()
    all_servers = registry.get("servers", {})
    if not all_servers:
        log_error("No MCP servers defined in registry.")
        return
        
    target = args.target.lower()
    selected_raw = args.servers or "all"
    if selected_raw.lower() == "all":
        servers_to_install = all_servers
    else:
        requested_keys = [k.strip().lower() for k in selected_raw.split(",")]
        servers_to_install = {k: v for k, v in all_servers.items() if k.lower() in requested_keys}
        
    if not servers_to_install:
        log_error(f"No matching MCP servers found for: {selected_raw}")
        return
        
    paths = get_platform_paths()
    target_configs: List[Tuple[str, Path]] = []
    
    if target in ["claude", "claude_desktop", "all"]:
        target_configs.append(("Claude Desktop", paths["claude_desktop"]["mcp_config"]))
    if target in ["cursor", "all"]:
        target_configs.append(("Cursor", paths["cursor"]["mcp_config"]))
    if target in ["vscode", "copilot", "all"]:
        target_configs.append(("VS Code / Copilot", paths["copilot"]["vscode_mcp"]))
    if target in ["windsurf", "all"]:
        target_configs.append(("Windsurf", paths["windsurf"]["mcp_config"]))
    if target in ["workspace", "agy"]:
        target_configs.append(("Antigravity Workspace", WORKSPACE_ROOT / ".agents" / "mcp.json"))
        
    for plat_name, config_path in target_configs:
        log_info(f"Configuring MCP servers for [bold]{plat_name}[/bold] -> {config_path}")
        
        existing_data = {"mcpServers": {}}
        if config_path.exists():
            try:
                existing_data = json.loads(config_path.read_text(encoding="utf-8"))
                if "mcpServers" not in existing_data:
                    existing_data["mcpServers"] = {}
                # Create backup
                if not args.dry_run:
                    backup_path = config_path.with_suffix(".json.bak")
                    shutil.copy2(config_path, backup_path)
                    log_info(f"Created backup: {backup_path}")
            except Exception as e:
                log_warning(f"Could not parse existing {config_path}: {e}. Creating new configuration.")
                existing_data = {"mcpServers": {}}
                
        # Merge new servers
        added_count = 0
        for server_key, spec in servers_to_install.items():
            existing_data["mcpServers"][server_key] = resolve_mcp_config(spec)
            added_count += 1
            
        if args.dry_run:
            log_info(f"[DRY-RUN] Generated {plat_name} config:")
            print(json.dumps(existing_data, indent=2))
        else:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(existing_data, indent=2), encoding="utf-8")
            log_success(f"Merged {added_count} MCP server(s) into {config_path}")


# ==============================================================================
# Command: Export Rules
# ==============================================================================

def cmd_export_rules(args: argparse.Namespace):
    """Exports workspace rules to all or specified platforms."""
    args.name = "all"
    cmd_install_skills(args)


# ==============================================================================
# Command: New Skill Scaffolder
# ==============================================================================

def cmd_new_skill(args: argparse.Namespace):
    """Scaffolds a new skill directory and template."""
    name = args.name.lower().strip().replace(" ", "-").replace("_", "-")
    description = args.description or f"Custom AI Agent skill for {name}."
    skill_dir = SKILLS_DIR / name
    
    if skill_dir.exists():
        log_error(f"Skill directory already exists: {skill_dir}")
        return
        
    skill_dir.mkdir(parents=True, exist_ok=True)
    template_content = f"""---
name: {name}
description: >-
  {description}
  Trigger with `/{name} [args]`.
parameters:
  query:
    type: string
    description: Input query or target for the skill
    required: true
---

# {name.replace('-', ' ').title()} Skill

{description}

## Workflow & Steps
1. **Input Validation**: Parse and validate incoming user parameters.
2. **Execution**: Perform the required computation, tool invocations, or data transformations.
3. **Synthesis & Output**: Deliver structured results formatted with clear markdown.

## Usage
Trigger in chat or CLI:
```bash
/{name} <parameter>
```
"""
    (skill_dir / "SKILL.md").write_text(template_content, encoding="utf-8")
    log_success(f"Created new skill at: {skill_dir / 'SKILL.md'}")


# ==============================================================================
# Command: New MCP Preset Scaffolder
# ==============================================================================

def cmd_new_mcp(args: argparse.Namespace):
    """Adds a new MCP server configuration to the registry."""
    key = args.name.lower().strip().replace(" ", "-").replace("_", "-")
    registry = get_mcp_registry()
    if "servers" not in registry:
        registry["servers"] = {}
        
    if key in registry["servers"]:
        log_error(f"MCP server key '{key}' already exists in registry.")
        return
        
    command = args.command or "npx"
    pkg = args.package or f"@modelcontextprotocol/server-{key}"
    
    registry["servers"][key] = {
        "name": args.name.title(),
        "category": args.category or "custom",
        "description": args.description or f"MCP Server integration for {key}.",
        "command": command,
        "args": ["-y", pkg] if command == "npx" else [pkg],
        "env": {},
        "homepage": "https://modelcontextprotocol.io"
    }
    
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    log_success(f"Added new MCP preset '{key}' to registry.")


# ==============================================================================
# Command: Validate & Self-Test
# ==============================================================================

def cmd_validate(args: argparse.Namespace):
    """Validates all skills, YAML frontmatters, and JSON configs in the repo."""
    log_info("Validating workspace skills and configurations...")
    
    # 1. Validate skills
    skills = get_all_skills()
    skill_errors = 0
    for name, s in skills.items():
        if not s.get("description") or s.get("description") == "No description provided.":
            log_warning(f"Skill '{name}' has missing or empty description.")
            skill_errors += 1
            
    # 2. Validate MCP registry
    registry = get_mcp_registry()
    servers = registry.get("servers", {})
    mcp_errors = 0
    for key, spec in servers.items():
        if "command" not in spec or "args" not in spec:
            log_error(f"MCP preset '{key}' is missing required fields (command, args).")
            mcp_errors += 1
            
    if skill_errors == 0 and mcp_errors == 0:
        log_success(f"Validation successful: {len(skills)} skills and {len(servers)} MCP servers validated with 0 errors.")
    else:
        log_error(f"Validation failed with {skill_errors} skill warnings and {mcp_errors} MCP errors.")
        sys.exit(1)


# ==============================================================================
# CLI Argument Parser & Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="agent_hub",
        description="Universal AI Agent Workspace CLI & Manager for Skills and MCP Servers",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # doctor
    subparsers.add_parser("doctor", help="Run system diagnostics and detect AI client configs")
    
    # list-skills
    subparsers.add_parser("list-skills", help="List all available skills")
    
    # list-mcp
    subparsers.add_parser("list-mcp", help="List all MCP server presets")
    
    # install-skills
    p_inst_skill = subparsers.add_parser("install-skills", help="Install/export skills to target platforms")
    p_inst_skill.add_argument("--name", default="all", help="Skill name or 'all'")
    p_inst_skill.add_argument("--target", default="all", choices=["all", "agy", "gemini", "claude", "cursor", "copilot", "vscode", "windsurf"], help="Target AI client")
    
    # install-mcp
    p_inst_mcp = subparsers.add_parser("install-mcp", help="Install/merge MCP server configs into AI clients")
    p_inst_mcp.add_argument("--servers", default="all", help="Comma-separated server keys or 'all'")
    p_inst_mcp.add_argument("--target", default="all", choices=["all", "claude", "claude_desktop", "cursor", "vscode", "copilot", "windsurf", "agy", "workspace"], help="Target platform")
    p_inst_mcp.add_argument("--dry-run", action="store_true", help="Print config output without writing to disk")
    
    # export-rules
    p_exp_rules = subparsers.add_parser("export-rules", help="Export workspace instructions to Cursor/Copilot/Claude/Windsurf")
    p_exp_rules.add_argument("--target", default="all", choices=["all", "agy", "gemini", "claude", "cursor", "copilot", "vscode", "windsurf"], help="Target AI client")
    
    # new-skill
    p_new_skill = subparsers.add_parser("new-skill", help="Scaffold a new skill")
    p_new_skill.add_argument("--name", required=True, help="Unique skill name (e.g. data-analyzer)")
    p_new_skill.add_argument("--description", help="Description of the skill")
    
    # new-mcp
    p_new_mcp = subparsers.add_parser("new-mcp", help="Add a new MCP preset to registry")
    p_new_mcp.add_argument("--name", required=True, help="Server preset key (e.g. redis)")
    p_new_mcp.add_argument("--command", default="npx", help="Execution command (npx, uvx, node, python3)")
    p_new_mcp.add_argument("--package", help="NPM or Python package name")
    p_new_mcp.add_argument("--category", default="custom", help="Category (web, database, system, etc.)")
    p_new_mcp.add_argument("--description", help="Description of the MCP server")
    
    # validate
    subparsers.add_parser("validate", help="Validate all skill definitions and MCP configurations")
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    cmd_map = {
        "doctor": cmd_doctor,
        "list-skills": cmd_list_skills,
        "list-mcp": cmd_list_mcp,
        "install-skills": cmd_install_skills,
        "install-mcp": cmd_install_mcp,
        "export-rules": cmd_export_rules,
        "new-skill": cmd_new_skill,
        "new-mcp": cmd_new_mcp,
        "validate": cmd_validate,
    }
    
    handler = cmd_map.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
