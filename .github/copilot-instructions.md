# GitHub Copilot Custom Instructions

## Project Guidelines
- Modular, well-typed Python (3.9+) and TypeScript codebase.
- Adhere strictly to the Model Context Protocol standards for MCP servers.
- Use `pydantic` schemas for validation and `rich` for CLI output formatting.

## Registered Agent Skills
- **code-reviewer**: Performs deep, senior-level code reviews focusing on architecture, security vulnerabilities, performance bottlenecks, test coverage, and adherence to clean code principles. Trigger with `/review [path_or_git_diff]`.
- **job-matcher**: Extracts, evaluates, and ranks job postings against candidate resumes using an intelligent Hybrid Scrape & Cache layer (SQLite + BeautifulSoup + Firecrawl MCP fallback) and local or cloud LLM scoring. Trigger with `/jobmatch [resume_path] [optional_keywords]` or `/jobhunt [resume_path]`.
- **mcp-builder**: Guides the design, implementation, testing, and distribution of Model Context Protocol (MCP) servers in Python or TypeScript according to the official MCP specifications. Trigger with `/new-mcp-server [server_name]`.
- **prompt-engineer**: Designs, evaluates, and optimizes system prompts, few-shot examples, tool schemas, and agent personas for maximum reasoning accuracy and reliability. Trigger with `/prompt-opt [prompt_or_task]`.
- **web-researcher**: Performs multi-step, autonomous web research, documentation lookup, fact verification, and synthesizes findings into structured technical summaries or comparison tables. Trigger with `/research [query]`.
