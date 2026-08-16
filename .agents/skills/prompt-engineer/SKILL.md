---
name: prompt-engineer
description: >-
  Designs, evaluates, and optimizes system prompts, few-shot examples, tool schemas,
  and agent personas for maximum reasoning accuracy and reliability.
  Trigger with `/prompt-opt [prompt_or_task]`.
parameters:
  task:
    type: string
    description: Task or agent role to design prompt for
    required: true
  model_family:
    type: string
    description: Target LLM family (claude | openai | gemini | local)
    default: universal
---

# Prompt Engineer Skill

Systematic methodology for authoring, evaluating, and refining LLM prompts and agent instructions.

## Prompt Architecture Framework

Every robust prompt should include:
1. **Identity & Role Definition**: Precise persona, authority scope, and background context.
2. **Operational Constraints**: Explicit negative constraints (what NOT to do) and positive constraints.
3. **Execution Steps (Algorithm)**: Step-by-step reasoning procedure before taking action.
4. **Tool Use & Format Requirements**: Exact input/output schemas, JSON formatting, or markdown guidelines.
5. **Few-Shot Demonstrations**: High-quality input-output pairs illustrating edge cases and desired formatting.

## Heuristics for High Accuracy
- **Chain of Thought**: Instruct the model to deliberate in `<thinking>` blocks before emitting final answers.
- **XML / Markdown Delimiters**: Use tags like `<user_query>`, `<context>`, `<rules>` to eliminate prompt injection and confusion.
- **Edge-Case Anchoring**: Provide explicit fallback actions when data is missing or ambiguous.
