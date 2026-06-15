import json
import os
import urllib.error
import urllib.request


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class ProviderError(RuntimeError):
    pass


class GroqProvider:
    """
    A lightweight, dependency-free HTTP client for the Groq chat completions API.
    Used to connect to LLaMa models for natural language database querying.
    """
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")

    def complete(self, model: str, messages: list[dict], tools: list[dict]) -> dict:
        """
        Send a completion request to the Groq API, passing along the chat history
        and available MCP tool schemas.
        """
        if not self.api_key:
            raise ProviderError("GROQ_API_KEY is not configured on the server.")

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2,
        }).encode("utf-8")
        request = urllib.request.Request(
            GROQ_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Groq request failed ({exc.code}): {detail[:500]}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ProviderError(f"Groq is currently unavailable: {exc}") from exc

        try:
            return result["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Groq returned an unexpected response.") from exc
