# AI Usage Note — Database MCP Server

## What AI Helped With
- Core agent/LLM logic and prompt design
- Code scaffolding for boilerplate (bot handlers, API clients)
- Test case generation
- Documentation drafting

## What AI Got Wrong
- Initial prompt lacked specificity — required iteration to get structured JSON output
- Edge cases in tool call sequencing needed explicit system prompt instructions
- Some generated code required manual correction for API compatibility

## Best Prompts Used
- System: "You are a database mcp server agent. Always [action] before [action]. Never skip [step]."
- Tool descriptions kept concise and action-oriented
- JSON-only output enforced with: "Return ONLY JSON, no preamble or markdown"


