# DevMate

**An AI agent that understands your GitHub repos.** Ask it questions about your code, let it triage new issues automatically, and talk to it from the terminal, a REST API, or Claude Desktop.

Built to explore Retrieval-Augmented Generation (RAG), LangGraph agents, tool calling, GitHub automation, and the Model Context Protocol (MCP) — all in one working project.

---

## What it does

- **Understands your code** — clones a GitHub repo, chunks it with language-aware splitting, embeds it locally (Ollama), and answers questions with file + line-number citations.
- **Supports multiple repos at once** — each repo is tagged and isolated in the vector store, so answers never bleed across projects.
- **Triages GitHub issues automatically** — a webhook fires the moment a new issue is opened; the agent reads it, finds similar past issues, and posts a structured comment with a label, priority, and reasoning.
- **Is a real agent, not just a RAG wrapper** — built with LangGraph's ReAct pattern on top of 6+ tools (code search, issue lookup, similarity search, commenting), so it decides for itself which tool to call.
- **Speaks MCP** — exposed as an MCP server, so Claude Desktop (or any MCP client) can call DevMate's tools directly.
- **Has three front doors** — a FastAPI REST API, a Typer CLI, and a terminal chatbot with conversation history.

## Architecture

```
GitHub repo
    │
    ▼
clone → chunk (language-aware) → embed (Ollama, local) → ChromaDB
                                                              │
                                                              ▼
                                                 ┌─────────────────────┐
                                                 │   LangGraph Agent    │
                                                 │  (Groq-hosted LLM)   │
                                                 └─────────────────────┘
                                                   │   │   │   │   │
                                       search_code │   │   │   │   │ comment_on_pr
                                   indexed_repos ──┘   │   │   └──────────┐
                                           get_issue ──┘   │              │
                                    list_similar_issues ───┘              │
                                                                          ▼
        ┌──────────────┬────────────────┬──────────────────┬────────────────────┐
        │   CLI         │  Terminal      │   FastAPI          │   MCP Server        │
        │  (cli.py)     │  Chatbot       │  REST API +        │  (Claude Desktop,   │
        │               │  (chat.py)     │  GitHub Webhook    │   other MCP clients)│
        └──────────────┴────────────────┴──────────────────┴────────────────────┘
```

## Tech stack

| Layer | Tech |
|---|---|
| Language | Python |
| Agent framework | LangChain, LangGraph (ReAct agent) |
| LLM | Groq (`openai/gpt-oss-120b`) |
| Embeddings | Ollama (`nomic-embed-text`), local — no API cost |
| Vector store | ChromaDB, with per-repo metadata filtering |
| Backend | FastAPI |
| GitHub integration | PyGithub, signature-verified webhooks |
| Tool protocol | MCP (Model Context Protocol) |
| CLI | Typer |
| Structured output | Pydantic |

## Project structure

```
devmate/
├── ingest.py       # clone repo → load files → chunk
├── store.py        # embeddings + Chroma (multi-repo aware)
├── RAG.py          # retrieval + answer generation, with citations
├── agent.py        # tools + LangGraph ReAct agent + issue triage
├── chat.py         # terminal chatbot with conversation history
├── server.py       # FastAPI REST API + GitHub webhook
├── mcp_server.py   # MCP server (Claude Desktop integration)
├── cli.py          # CLI: index / ask / list repos
├── requirements.txt
└── .env            # not committed — see below
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Arundhakad03/devmate.git
cd devmate
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Pull the local embedding model

```bash
ollama pull nomic-embed-text
ollama serve
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_key
GITHUB_TOKEN=your_github_token        # repo scope
WEBHOOK_SECRET=any_random_string      # for webhook signature verification
```

## Usage

### Index a repo

```bash
python cli.py index https://github.com/owner/repo
```

### Ask questions from the CLI

```bash
python cli.py ask-question "how does flight search work?" --repo repo-name
python cli.py repos    # list all indexed repos
```

### Chat in the terminal

```bash
python chat.py
```

### Run the API + webhook server

```bash
uvicorn server:app
```

- `POST /ask` — ask a question, get an answer with sources
- `POST /triage` — manually triage a GitHub issue
- `POST /webhooks/github` — GitHub webhook endpoint (auto-triages new issues)

### Connect to Claude Desktop (MCP)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devmate": {
      "command": "/path/to/venv/Scripts/python.exe",
      "args": ["/path/to/devmate/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop, then ask it to use the `devmate` tools directly.

## Status

Actively being built. Next up: retrieval accuracy evaluation and a web UI.

## Author

**Arun Dhakad** — [GitHub](https://github.com/Arundhakad03)
