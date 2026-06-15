import json
from typing import Callable

from client.api.groq_provider import ProviderError
from mcp.src import server as mcp_server


SYSTEM_PROMPT = """You are DB/BRIDGE, a concise database analyst.
If the user says a simple greeting or asks a general question, respond directly without using tools.
Use the available MCP tools ONLY when the user asks about the selected SQLite database or requests data.
Inspect tables and schemas before writing SQL when needed. Only use read-only SELECT queries.
Never invent database values. Explain results clearly and mention limits or errors."""

HOSTED_TOOL_NAMES = {
    "list_databases",
    "get_database_metadata",
    "list_tables",
    "get_schema",
    "run_select",
    "explain_query",
}


def groq_tools() -> list[dict]:
    """
    Format the locally hosted MCP tools into the function-calling schema 
    expected by the Groq API.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": definition["description"],
                "parameters": definition["inputSchema"],
            },
        }
        for name, definition in mcp_server.TOOLS.items()
        if name in HOSTED_TOOL_NAMES
    ]


def execute_tool(name: str, arguments: dict, db_name: str | None) -> dict:
    """
    Execute a requested MCP tool by formatting a JSON-RPC request and passing
    it directly to the local mcp_server's handle_request method.
    """
    args = dict(arguments)
    if name != "list_databases" and db_name:
        args["db_name"] = db_name

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": args},
    }
    response = mcp_server.handle_request(request)
    if not response or "result" not in response:
        return {"error": response.get("error", "MCP tool call failed") if response else "MCP tool call failed"}

    text = response["result"]["content"][0]["text"]
    return json.loads(text)


def run_chat(
    provider,
    model: str,
    messages: list[dict],
    db_name: str | None,
    max_tool_rounds: int = 6,
    tool_executor: Callable[[str, dict, str | None], dict] = execute_tool,
) -> tuple[str, list[dict]]:
    """
    Run a multi-turn chat interaction with the language model.
    The LLM may call MCP tools multiple times in a loop to investigate
    database schemas and run queries before answering the user.
    """
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    conversation.extend({"role": item["role"], "content": item["content"]} for item in messages)
    activity = []

    for _ in range(max_tool_rounds + 1):
        assistant = provider.complete(model, conversation, groq_tools())
        tool_calls = assistant.get("tool_calls") or []

        if not tool_calls:
            content = assistant.get("content") or "I could not produce an answer."
            return content, activity

        conversation.append({
            "role": "assistant",
            "content": assistant.get("content"),
            "tool_calls": tool_calls,
        })

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            name = function.get("name", "")
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}

            if name not in HOSTED_TOOL_NAMES:
                result = {"error": f"Unknown hosted MCP tool: {name}"}
            else:
                result = tool_executor(name, arguments, db_name)

            activity.append({
                "tool": name,
                "arguments": arguments,
                "status": "error" if "error" in result else "success",
                "result": result,
            })
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "name": name,
                "content": json.dumps(result),
            })

    raise ProviderError("The model exceeded the MCP tool-call limit.")
