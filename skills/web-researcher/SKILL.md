---
name: web-researcher
description: >-
  Performs multi-step, autonomous web research, documentation lookup, fact verification,
  and synthesizes findings into structured technical summaries or comparison tables.
  Trigger with `/research [query]`.
parameters:
  query:
    type: string
    description: Research question or topic
    required: true
  depth:
    type: string
    description: Research depth (quick | standard | deep)
    default: standard
---

# Web Researcher Skill

Conducts exhaustive, evidence-based research across official documentation, technical blogs, and public web sources.

## Workflow
1. **Query Decomposition**: Breaks the user's research topic into 3-5 precise search queries.
2. **Multi-Source Gathering**:
   - Queries web search engines (Brave Search / DuckDuckGo).
   - Fetches documentation and technical articles using `fetch` or `firecrawl` MCP tools.
3. **Synthesis & Fact Verification**:
   - Compares statements across multiple independent sources.
   - Discards outdated or conflicting claims.
4. **Structured Delivery**:
   - Produces an executive summary, key findings, comparative tables, and direct source citations.

## Guidelines
- Always prioritize primary official documentation over third-party blog summaries.
- Explicitly note version compatibility and release dates.
- Format results with clear headings, bullet points, and markdown tables.
