import os

from mcp.server.fastmcp import FastMCP
from store import get_embeddings, list_indexed_repos
from store import get_embeddings, list_indexed_repos
from RAG import ask as rag_ask
from agent import get_github, triage_issue
from langchain_chroma import Chroma

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(BASE_DIR, "data", "chroma")

mcp = FastMCP("DevMate")


@mcp.tool()
def ask_repo(question: str, repo: str = "") -> str:
    """Indexed repo ke code se sawaal ka jawab do, sources ke saath. repo ka naam do (jaise 'TripMate') jab pata ho."""
    # kai repos index hain aur repo nahi bataya to poocho
    if not repo:
        repos = list_indexed_repos(PERSIST_DIR)
        if len(repos) > 1:
            return f"Kai repos index hain: {', '.join(repos)}. Batao kaun sa repo."

    embeddings = get_embeddings()
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    result = rag_ask(db, question, repo=repo or None)

    sources_text = ", ".join(
        f"{s['file']} (line {s['start_line']}-{s['end_line']})"
        for s in result["sources"]
    )
    return f"{result['response']}\n\nSources: {sources_text}"


@mcp.tool()
def search_github_issue(repo_full_name: str, issue_number: int) -> str:
    """GitHub repo se ek issue ka title aur description nikalo."""
    gh = get_github()
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)
    return f"Title: {issue.title}\n\nBody: {issue.body}"


@mcp.tool()
def indexed_repos() -> str:
    """Kaun kaun se repos index hain, unki list do."""
    repos = list_indexed_repos(PERSIST_DIR)
    return ", ".join(repos) if repos else "Koi repo index nahi hai"


@mcp.tool()
def triage_github_issue(repo_full_name: str, issue_number: int) -> str:
    """Kisi GitHub issue ko triage karo: label, priority aur reasoning do."""
    result = triage_issue(repo_full_name, issue_number)
    return (
        f"Label: {result.label}\n"
        f"Priority: {result.priority}\n"
        f"Reasoning: {result.reasoning}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

