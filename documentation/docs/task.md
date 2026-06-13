# Custom MCP Database Chat Client

## Goal

Build an online custom AI chat client that demonstrates the Database MCP Server.
The application should look and feel like ChatGPT while matching the visual theme
of the existing documentation website in `documentation/docs/web`.

Visitors should be able to open the client from a "Try it online" button on the
documentation website, select an AI model, add or select a SQLite database, and
ask natural-language questions about its data.

## My Understanding

- Keep the documentation website as a static site deployed through GitHub Pages.
- Add a "Try it online" button to the documentation website.
- The button redirects visitors to a separate custom chat application deployed
  on Vercel.
- The custom client uses a ChatGPT-style layout but inherits the documentation
  site's colors, typography, spacing, dark/light themes, and DB/BRIDGE branding.
- Use FastAPI as the backend for chat requests and database management.
- Use the existing MCP tools to inspect and query SQLite databases safely.
- Start with the Groq API for LLM inference.
- Allow users to choose between multiple supported LLM models.
- Deploy both the custom chat frontend and FastAPI backend on Vercel.

## Important Technical Decisions

### Groq API

This brief assumes "grog api" means the **Groq API**. Groq provides access to
multiple hosted LLMs, so the first version can offer a model selector populated
from an approved server-side model configuration.

The `GROQ_API_KEY` must remain on the backend and must never be exposed to the
browser.

### MCP Communication

The current MCP server uses the `stdio` transport, which is designed for local
clients such as Claude Desktop. A browser cannot connect directly to a `stdio`
MCP server.

For the hosted client, the FastAPI backend should act as the MCP host/client:

1. Receive a chat message from the frontend.
2. Send the conversation and MCP tool definitions to the selected Groq model.
3. Detect model tool calls.
4. execute the corresponding existing MCP database functions.
5. Return tool results to the model.
6. Stream or return the final answer to the frontend.

The existing MCP tool logic should remain the source of truth rather than
duplicating database query logic in the chat API.

### Database Storage on Vercel

Vercel serverless functions do not provide durable local filesystem storage.
An uploaded SQLite file saved only to the function filesystem can disappear
between requests.

The implementation must choose one of these approaches:

- **Recommended production approach:** store uploaded database files in durable
  object/blob storage and copy the selected database to temporary storage while
  processing a request.
- **Demo-only approach:** provide bundled sample databases and clearly label
  user uploads as temporary for the current session.

The first implementation should use strict upload limits and never allow users
to access another user's database.

## User Experience

### Documentation Website

Add a prominent "Try it online" button to `documentation/docs/web`.

The button should:

- Match the existing documentation theme.
- Open the deployed Vercel chat client.
- Make it clear that the destination is an interactive MCP database demo.

### Chat Client Layout

Create a responsive ChatGPT-inspired interface with:

- Collapsible sidebar.
- New chat button.
- Conversation history for the current browser/user.
- Main conversation area.
- Welcome screen with suggested database questions.
- Sticky message composer.
- Streaming response state.
- Stop-generation action.
- Clear error and retry states.
- Dark and light themes matching the documentation website.

Do not copy ChatGPT branding or assets. Use the existing DB/BRIDGE identity.

### Model Selection

Provide a model selector that:

- Lists multiple Groq-supported models configured by the backend.
- Shows the active model.
- Allows switching models before or during a conversation.
- Handles unavailable or deprecated models gracefully.
- Keeps provider credentials and provider-specific logic on the backend.

The backend should use a provider abstraction so another LLM provider can be
added later without rewriting the chat UI or MCP tool loop.

### Database Management

Provide a database panel or modal that allows users to:

- View available SQLite databases.
- Upload `.db` and `.sqlite` files.
- Select the active database for the conversation.
- View basic database metadata and table names.
- Delete databases they uploaded, when persistent user storage is enabled.
- Fall back to the bundled sample database for first-time visitors.

The UI must show which database is currently active.

### MCP Activity

Make MCP usage visible so visitors can understand the feature being demonstrated.

For each assistant response, optionally show expandable activity such as:

- `list_databases`
- `get_database_metadata`
- `list_tables`
- `get_schema`
- `run_select`
- `explain_query`

Show tool names, safe summaries of arguments, status, and results. Avoid exposing
secrets, internal paths, or excessive database content.

## Functional Requirements

### Chat API

- Accept a conversation, selected model, and selected database identifier.
- Validate all inputs.
- Use Groq tool/function calling to decide when MCP tools are needed.
- Execute a bounded tool-call loop with a maximum number of iterations.
- Return or stream the final assistant response.
- Return MCP activity metadata for display in the client.
- Handle provider timeouts, rate limits, malformed tool calls, and database
  errors with user-friendly messages.

### MCP and Database Safety

- Preserve the existing read-only SQL policy.
- Allow only `SELECT` queries from the model.
- Keep the existing 100-row maximum or apply a stricter configurable limit.
- Validate database and table identifiers.
- Add query execution timeouts where possible.
- Limit uploaded file size.
- Verify uploaded files are valid SQLite databases.
- Isolate databases by anonymous session or authenticated user.
- Never send full database files to the LLM provider.

### Suggested Backend Endpoints

- `GET /api/health`
- `GET /api/models`
- `POST /api/chat`
- `GET /api/databases`
- `POST /api/databases/upload`
- `GET /api/databases/{id}/metadata`
- `DELETE /api/databases/{id}`

The exact endpoint shape may change during implementation.

## Proposed Repository Structure

```text
07-database-mcp-server/
├── documentation/
│   └── docs/web/                  # GitHub Pages documentation
├── mcp/
│   ├── src/                       # MCP tools and server
│   ├── tests/
│   ├── sample_data/
│   └── web/                       # Existing database manager UI
├── client/
│   ├── frontend/                  # Custom DB/BRIDGE chat frontend
│   └── api/                       # FastAPI hosted chat/backend entry points
├── task.md
└── vercel.json
```

The final structure should follow Vercel's supported Python and frontend
deployment conventions. The frontend framework can be selected during
implementation; React-based tooling is preferred for the interactive chat UI.

## Deployment Plan

### GitHub Pages

- Continue deploying only `documentation/docs/web`.
- Add the hosted chat client's Vercel URL to the "Try it online" button.
- Keep the existing GitHub Pages workflow independent from the Vercel deploy.

### Vercel

- Deploy the custom chat frontend.
- Deploy FastAPI endpoints as Vercel Python functions.
- Configure `GROQ_API_KEY` and storage credentials as Vercel environment
  variables.
- Configure CORS to allow only the documentation site and hosted client origins.
- Do not rely on the Vercel function filesystem for permanent uploads.

## Testing Requirements

- Unit tests for the provider abstraction and MCP tool-call loop.
- Unit tests for database upload validation and isolation.
- Existing MCP server tests must continue to pass.
- API integration tests for model listing, chat, and database management.
- End-to-end test covering:
  1. Open the online client.
  2. Select a model.
  3. Select or upload a database.
  4. Ask a database question.
  5. Observe MCP tool activity.
  6. Receive a correct natural-language answer.
- Responsive UI checks for desktop and mobile.
- Dark and light theme checks.

## Initial Milestones

1. Refactor the existing MCP database functions into reusable backend services
   without breaking local `stdio` MCP support.
2. Add the Groq provider abstraction and MCP tool-calling loop.
3. Build FastAPI chat and database-management endpoints.
4. Build the themed custom chat frontend with model and database selectors.
5. Add visible MCP activity to chat responses.
6. Add the documentation site's "Try it online" button.
7. Configure Vercel deployment and persistent database storage.
8. Add automated tests and deployment documentation.

## Acceptance Criteria

- The documentation remains hosted on GitHub Pages.
- A documentation button opens the hosted Vercel chat client.
- The client visually matches the documentation theme and uses DB/BRIDGE
  branding.
- A user can select from multiple configured Groq models.
- A user can select or upload a SQLite database.
- A user can ask a natural-language question and receive an answer generated
  using the existing MCP database tools.
- The UI visibly demonstrates which MCP tools were used.
- Database access remains read-only.
- Provider API keys are never exposed to the frontend.
- Uploaded database handling works within the selected Vercel storage strategy.

## Decisions Needed Before Implementation

- Should uploaded databases persist across visits, or is temporary demo storage
  acceptable for the first release?
- Should the first release support anonymous sessions only, or include user
  authentication?
- Which Groq models should be available in the model selector?
- Should conversation history persist across visits?
- Which durable storage provider should be used for uploaded SQLite files?
- What maximum database upload size should be allowed?
- Should responses stream token-by-token in the first release?

