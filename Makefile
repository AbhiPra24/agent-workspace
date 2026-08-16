# ==============================================================================
# Universal AI Agent Workspace Makefile
# ==============================================================================

SHELL := /bin/bash
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
TARGET ?= all
SKILL ?= all
SERVERS ?= all
DRY_RUN ?= 0

# Colors for terminal styling
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BOLD := \033[1m
RESET := \033[0m

.PHONY: all help setup doctor list list-skills list-mcp install-skills install-mcp export-rules new-skill new-mcp validate test clean

all: help

## help: Display this interactive help reference
help:
	@echo -e "$(BOLD)$(CYAN)Universal AI Agent Workspace & Manager$(RESET)"
	@echo -e "Unified management for Skills, MCP Servers & Platform Rules\n"
	@echo -e "$(BOLD)Available Commands:$(RESET)"
	@sed -n 's/^## //p' $(MAKEFILE_LIST) | awk -F ': ' '{printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo -e "\n$(BOLD)Examples:$(RESET)"
	@echo -e "  make setup                          # Initialize virtualenv & dependencies"
	@echo -e "  make doctor                         # Run environment health check"
	@echo -e "  make list                           # List all skills & MCP presets"
	@echo -e "  make install-skills TARGET=cursor   # Export skills as Cursor MDC rules"
	@echo -e "  make install-mcp TARGET=claude      # Merge MCP servers to Claude Desktop"
	@echo -e "  make new-skill NAME=pdf-analyzer    # Scaffold a new skill"
	@echo -e "  make test                           # Run automated test validation"

## setup: Create Python virtual environment and install all dependencies
setup:
	@echo -e "$(CYAN)Creating Python virtual environment...$(RESET)"
	@$(PYTHON) -m venv $(VENV)
	@echo -e "$(CYAN)Installing dependencies from requirements.txt...$(RESET)"
	@$(BIN)/pip install --upgrade pip
	@$(BIN)/pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env && echo -e "$(GREEN)Created .env from .env.example$(RESET)"; fi
	@echo -e "$(BOLD)$(GREEN)✔ Workspace setup completed successfully!$(RESET)"

## doctor: Run diagnostic health checks for runtimes and detected AI clients
doctor:
	@$(PYTHON) scripts/agent_hub.py doctor

## list: List all available skills and MCP server presets
list:
	@$(PYTHON) scripts/agent_hub.py list-skills
	@echo ""
	@$(PYTHON) scripts/agent_hub.py list-mcp

## list-skills: List all bundled agent skills
list-skills:
	@$(PYTHON) scripts/agent_hub.py list-skills

## list-mcp: List all available MCP server presets
list-mcp:
	@$(PYTHON) scripts/agent_hub.py list-mcp

## install-skills: Install/export skills to target (TARGET=all|agy|claude|cursor|copilot|windsurf)
install-skills:
	@$(PYTHON) scripts/agent_hub.py install-skills --target $(TARGET) --name $(SKILL)

## install-mcp: Install/merge MCP servers (TARGET=all|claude|cursor|copilot|windsurf, SERVERS=all|key1,key2)
install-mcp:
	@if [ "$(DRY_RUN)" = "1" ]; then \
		$(PYTHON) scripts/agent_hub.py install-mcp --target $(TARGET) --servers $(SERVERS) --dry-run; \
	else \
		$(PYTHON) scripts/agent_hub.py install-mcp --target $(TARGET) --servers $(SERVERS); \
	fi

## export-rules: Export workspace instructions and skills to Cursor, Claude, Copilot & Windsurf
export-rules:
	@$(PYTHON) scripts/agent_hub.py export-rules --target $(TARGET)

## new-skill: Scaffold a new skill template (usage: make new-skill NAME=my-skill)
new-skill:
	@if [ -z "$(NAME)" ]; then \
		echo -e "$(RED)Error: NAME is required. Example: make new-skill NAME=my-skill$(RESET)"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/agent_hub.py new-skill --name "$(NAME)"

## new-mcp: Scaffold a new MCP server preset (usage: make new-mcp NAME=redis)
new-mcp:
	@if [ -z "$(NAME)" ]; then \
		echo -e "$(RED)Error: NAME is required. Example: make new-mcp NAME=redis$(RESET)"; \
		exit 1; \
	fi
	@$(PYTHON) scripts/agent_hub.py new-mcp --name "$(NAME)"

## validate: Validate all skill frontmatters and MCP configurations
validate:
	@$(PYTHON) scripts/agent_hub.py validate

## test: Run automated pytest verification suite
test: validate
	@if [ -f "$(BIN)/pytest" ]; then \
		$(BIN)/pytest tests/ -v; \
	else \
		$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v; \
	fi

## clean: Remove cache files, test artifacts, and system files
clean:
	@echo -e "$(CYAN)Cleaning workspace artifacts...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.py[co]" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.bak" -delete 2>/dev/null || true
	@echo -e "$(GREEN)✔ Cleanup complete.$(RESET)"
