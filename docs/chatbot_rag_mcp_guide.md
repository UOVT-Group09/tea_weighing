# Chatbot + RAG + MCP — Plan & Implementation Guide

> **Feature branch:** `feature/chatbot-rag-mcp`
> **Owner:** H.G.P.C. Sagara (PM & Integration Dev)
> **Cost:** LKR 0 — every component uses a free tier or runs locally.

This guide covers the plan, what is already implemented, what you must do
yourself (get a free API key, connect Claude Desktop), and how to demo and
defend the feature in the viva.

---

## 1. What was added, in one picture

```
                                Browser (operator, logged in)
                                   │  floating 💬 widget
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │  Flask app                                           │
        │  POST /chatbot/api  (src/chatbot/routes.py)          │
        │        │                                             │
        │        ▼                                             │
        │  llm.py ──1──► rag.py (BM25) ──► knowledge/*.md      │  RAG
        │        │                                             │
        │        ├──2──► Groq API (free tier, Llama 3.3 70B)   │  LLM
        │        │         │  "call tool X please"             │
        │        └──3──► tools.py (read-only SQL) ──► MySQL    │  Tools
        └──────────────────────────────────────────────────────┘
                                   ▲
                                   │ same tools.py, served over MCP
        Claude Desktop ──► src/mcp_server.py  (stdio, official mcp SDK)
```

Three ideas, one design:

1. **RAG (Retrieval-Augmented Generation)** — before the LLM answers, the
   most relevant sections of a built-in *user manual*
   (`src/chatbot/knowledge/*.md`) are retrieved with BM25 and injected into
   the prompt. The model answers from facts, not from guesses.
2. **LLM with function calling** — for *live data* questions ("how much tea
   today?") the model calls one of eight read-only tools; the SQL lives in
   our code, never in the model.
3. **MCP (Model Context Protocol)** — `src/mcp_server.py` exposes those
   same eight tools to any MCP client (e.g. Claude Desktop), so an external
   AI assistant can also query the system's data. Tools are **defined once,
   served two ways**.

## 2. Why these choices (and why they're free)

| Decision | Choice | Why |
|---|---|---|
| LLM provider | **Groq free tier** (`llama-3.3-70b-versatile`) | No card needed, generous free limits, OpenAI-compatible API, supports function calling. Swappable later by changing two constants in `llm.py`. |
| Retrieval | **Hand-written BM25** (~60 lines, `rag.py`) | Zero cost, zero heavy dependencies (no PyTorch/embeddings), works offline, and you can explain every line in the viva. BM25 is the ranking function behind Lucene/Elasticsearch. |
| Vector DB | **None** | The knowledge base is ~7 small files; a vector database would be resume-driven overkill. Documented as a future upgrade instead. |
| MCP SDK | **Official `mcp` Python package** (FastMCP) | The standard implementation; stdio transport means no ports, no hosting, no cost. |
| Chat memory | **Browser-side history** | Server stays stateless, matching the project's open→run→close DB philosophy. |
| Offline mode | **"Manual mode" fallback** | With no API key (or no internet) the chatbot answers with the retrieved manual sections directly — the demo can never die on stage. |

Safety rules baked in (say these in the viva):

- All tools are **read-only** — the assistant can never modify data.
- The LLM **never writes SQL**; it only picks a tool name + arguments, and
  every query in `tools.py` is parameterised.
- The endpoint sits behind the same **operator login** as every page.
- Replies are rendered as **plain text** in the browser (no HTML
  injection), and errors never leak stack traces (project guideline §5.5).

## 3. Files added / changed

```
src/chatbot/__init__.py        package + blueprint export
src/chatbot/routes.py          POST /chatbot/api (login-protected)
src/chatbot/rag.py             BM25 index + retrieve()
src/chatbot/llm.py             Groq client, tool-calling loop, fallback
src/chatbot/tools.py           8 read-only data tools + registry
src/chatbot/knowledge/*.md     7-file user manual (the RAG corpus)
src/mcp_server.py              MCP server wrapping the same tools
src/templates/chatbot/widget.html   floating chat panel
src/static/js/chatbot.js       widget behaviour (fetch + history)
src/static/css/style.css       widget styles (appended)
src/app.py                     chatbot blueprint registered at /chatbot
src/config.py                  GROQ_API_KEY, CHATBOT_MODEL
.env.example                   the two new variables
requirements.txt               + requests
requirements-mcp.txt           optional: mcp (only for the MCP server)
tests/test_chatbot.py          11 tests (RAG, tools, fallback, endpoint)
```

## 4. Setup — what YOU need to do (10 minutes)

### 4.1 Install dependencies

```bash
cd tea_weighing
.venv\Scripts\activate
pip install -r requirements.txt          # adds requests
pip install -r requirements-mcp.txt      # only if you want the MCP server
```

### 4.2 Get a free Groq API key

1. Go to <https://console.groq.com> and sign up (Google login works,
   **no credit card**).
2. Open **API Keys → Create API Key**, copy the key (starts with `gsk_`).
3. Put it in `tea_weighing/.env`:

   ```
   GROQ_API_KEY=gsk_...your-key...
   ```

4. Restart the app (`python -m src.app`), log in, click the 💬 button.

Free-tier limits (as of mid-2026: ~30 requests/min, generous daily token
quota) are far more than a demo needs. **Never commit the key** — `.env`
is git-ignored.

> No key? The chatbot still works in *manual mode* and answers from the
> built-in manual — try it before creating the key to see the difference.

### 4.3 Connect Claude Desktop over MCP (the MCP demo)

1. Install [Claude Desktop](https://claude.ai/download) (free plan is fine).
2. Open its config file — on Windows:
   `%APPDATA%\Claude\claude_desktop_config.json` (create it if missing).
3. Add the server, using **absolute paths** for your machine:

   ```json
   {
     "mcpServers": {
       "tea-weighing": {
         "command": "C:\\Pasindu\\Smart Tea Leaves Weighing System\\tea_weighing\\.venv\\Scripts\\python.exe",
         "args": ["-m", "src.mcp_server"],
         "cwd": "C:\\Pasindu\\Smart Tea Leaves Weighing System\\tea_weighing"
       }
     }
   }
   ```

4. Fully restart Claude Desktop. A tools icon appears; ask it e.g.
   *"Using the tea-weighing tools, which farmer supplied the most tea?"*

Claude Desktop launches `src/mcp_server.py` itself and talks to it over
stdio — you never run or host anything. MySQL must be running locally for
the data tools (the manual-search tool works regardless).

## 5. How each part works (viva depth)

### 5.1 RAG — `src/chatbot/rag.py`

- Each markdown file in `knowledge/` is split into chunks on `##` headings
  → one chunk ≈ one topic.
- Chunks are tokenised into lowercase words; a document-frequency table is
  built once and cached.
- A query is scored against every chunk with **BM25**: rare words weigh
  more (IDF), repeated words saturate (k1 = 1.5), and long chunks are
  normalised (b = 0.75).
- The top-3 chunks are injected into the LLM's system prompt under
  "MANUAL EXCERPTS". This is retrieval-augmented generation: the model is
  *grounded* in our documentation, which curbs hallucination.

To extend the knowledge base, just drop another `.md` file into
`knowledge/` with `##` sections — no re-indexing step, it's picked up on
next app start.

### 5.2 Function calling — `src/chatbot/llm.py` + `tools.py`

- The request to Groq includes a `tools` list (JSON Schema per tool,
  generated from `TOOL_REGISTRY`).
- If the model replies with `tool_calls` instead of text, we execute each
  tool via `run_tool()` and send results back as `role: "tool"` messages —
  looping at most 4 rounds, then returning the final text.
- Tools: `list_farmers`, `get_farmer_summary`, `get_daily_summary`,
  `get_flagged_records`, `get_payment_summary`, `get_attendance_summary`,
  `get_tea_price`, `search_app_knowledge`.

### 5.3 MCP — `src/mcp_server.py`

MCP is an open standard (think "USB-C for AI tools"): a client (Claude
Desktop) discovers and calls tools on servers over a JSON-RPC protocol.
Our server uses FastMCP decorators; each `@mcp.tool()` simply delegates to
the shared function in `tools.py`. Transport is stdio — the client spawns
the process, so there is no port, no auth surface and no hosting cost.

## 6. Testing & demo script

```bash
cd tea_weighing
python -m pytest tests/test_chatbot.py -v   # chatbot suite
python -m pytest                            # full suite
```

Suggested 3-minute demo:

1. Log in, open the 💬 widget.
2. Knowledge question: *"Why was a weight entry flagged?"* → RAG answer
   quoting the 3x/⅓ rule.
3. Live-data question: *"How much tea did we collect today, and were any
   entries flagged?"* → model calls `get_daily_summary`.
4. Kill the API key (or Wi-Fi) and repeat question 2 → manual-mode
   fallback still answers. Resilience point scored.
5. Switch to Claude Desktop → *"Which farmer's supply trend is down?"* →
   MCP tools fire against the same database.

## 7. Known limits & future upgrades

- BM25 is keyword-based; paraphrased questions with zero overlapping words
  can miss. *Upgrade path:* free embeddings (e.g. Gemini's embedding API
  free tier) with cosine similarity, keeping BM25 as fallback.
- Chat history lives per browser tab; refreshing clears it. *Upgrade:*
  store conversations in a table.
- Groq free tier rate limits (~30 req/min) are fine for one centre, not
  for production scale. *Upgrade:* paid tier or self-hosted Ollama.
- The MCP server is stdio/local-only by design. *Upgrade:* HTTP transport
  with auth if remote access were ever needed.
