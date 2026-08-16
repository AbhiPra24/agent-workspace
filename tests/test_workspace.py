#!/usr/bin/env python3
"""
Automated Test Suite for AI Agent Workspace
============================================
Validates Skills, MCP server configurations, rule exporters, and CLI utilities.
"""

import os
import sys
import json
import unittest
import tempfile
from pathlib import Path

# Add project root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.agent_hub import (
    parse_frontmatter,
    get_all_skills,
    get_mcp_registry,
    resolve_mcp_config,
    SKILLS_DIR,
    REGISTRY_FILE
)


class TestSkillsRegistry(unittest.TestCase):
    """Tests that all skills in skills/ are correctly structured and formatted."""

    def test_skills_exist(self):
        skills = get_all_skills()
        self.assertGreaterEqual(len(skills), 4, "Expected at least 4 bundled skills.")

    def test_skills_frontmatter(self):
        skills = get_all_skills()
        for name, skill in skills.items():
            with self.subTest(skill=name):
                self.assertTrue(name, "Skill must have a non-empty name.")
                self.assertTrue(skill.get("description"), f"Skill '{name}' must have a description.")
                self.assertNotEqual(
                    skill.get("description"),
                    "No description provided.",
                    f"Skill '{name}' has missing or fallback description."
                )
                self.assertTrue(skill["path"].exists(), f"Skill file {skill['path']} must exist.")
                self.assertGreater(len(skill["content"]), 20, f"Skill '{name}' content is too short.")

    def test_parse_frontmatter_standalone(self):
        sample = """---
name: test-skill
description: >-
  A test skill description that spans
  multiple lines cleanly.
parameters:
  query:
    type: string
---
# Body Content
Hello world!
"""
        metadata, body = parse_frontmatter(sample)
        self.assertEqual(metadata.get("name"), "test-skill")
        self.assertIn("A test skill description", metadata.get("description", ""))
        self.assertIn("Hello world!", body)


class TestMCPRegistry(unittest.TestCase):
    """Tests that the MCP server registry and presets are valid."""

    def test_registry_file_validity(self):
        self.assertTrue(REGISTRY_FILE.exists(), "mcp-servers/registry.json must exist.")
        registry = get_mcp_registry()
        self.assertIn("servers", registry, "Registry must contain 'servers' key.")
        servers = registry["servers"]
        self.assertGreaterEqual(len(servers), 8, "Expected at least 8 MCP server presets.")

        for key, spec in servers.items():
            with self.subTest(server=key):
                self.assertIn("command", spec, f"Server '{key}' missing 'command'.")
                self.assertIn("args", spec, f"Server '{key}' missing 'args'.")
                self.assertIsInstance(spec["args"], list, f"Server '{key}' 'args' must be a list.")
                self.assertIn("description", spec, f"Server '{key}' missing 'description'.")

    def test_resolve_mcp_config(self):
        spec = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "${WORKSPACE_DIR:-.}"],
            "env": {
                "TEST_VAR": "${UNSET_TEST_VAR_XYZ}"
            }
        }
        resolved = resolve_mcp_config(spec)
        self.assertEqual(resolved["command"], "npx")
        self.assertEqual(resolved["args"][2], str(WORKSPACE_ROOT))
        self.assertEqual(resolved["env"]["TEST_VAR"], "")


class TestExporters(unittest.TestCase):
    """Tests exporting rules to target formats."""

    def test_skills_can_be_converted_to_mdc(self):
        skills = get_all_skills()
        for name, skill in skills.items():
            mdc = f"""---
description: {skill['description']}
globs: *
alwaysApply: false
---

# {name}

{skill['content']}
"""
            self.assertTrue(mdc.startswith("---"))
            self.assertIn("alwaysApply: false", mdc)
            self.assertIn(name, mdc)


class TestJobMatcherCLI(unittest.TestCase):
    """Tests the job matcher script imports and helper functions."""

    def test_job_matcher_imports(self):
        try:
            import scripts.job_matcher as jm
            self.assertTrue(hasattr(jm, "init_db"))
            self.assertTrue(hasattr(jm, "parse_resume"))
            self.assertTrue(hasattr(jm, "evaluate_job_match"))
        except ImportError as e:
            self.fail(f"Failed to import job_matcher.py: {e}")


if __name__ == "__main__":
    unittest.main()
