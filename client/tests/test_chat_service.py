from client.api.chat_service import run_chat


class ToolCallingProvider:
    def __init__(self):
        self.calls = 0

    def complete(self, model, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "list_tables", "arguments": "{}"},
                }],
            }
        return {"role": "assistant", "content": "The database contains customers.", "tool_calls": []}


def test_run_chat_executes_mcp_tool_and_returns_activity():
    executions = []

    def execute(name, arguments, db_name):
        executions.append((name, arguments, db_name))
        return {"tables": ["customers"]}

    answer, activity = run_chat(
        ToolCallingProvider(),
        "test-model",
        [{"role": "user", "content": "What tables exist?"}],
        "sample.db",
        tool_executor=execute,
    )

    assert answer == "The database contains customers."
    assert executions == [("list_tables", {}, "sample.db")]
    assert activity[0]["tool"] == "list_tables"
    assert activity[0]["status"] == "success"


def test_run_chat_records_tool_errors():
    def execute(name, arguments, db_name):
        return {"error": "Database unavailable"}

    _, activity = run_chat(
        ToolCallingProvider(),
        "test-model",
        [{"role": "user", "content": "What tables exist?"}],
        "missing.db",
        tool_executor=execute,
    )

    assert activity[0]["status"] == "error"
