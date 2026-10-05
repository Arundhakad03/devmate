import os
from github import Github
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_chroma import Chroma
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from store import get_embeddings, list_indexed_repos
from RAG import ask as rag_ask

PERSIST_DIR = "data/chroma"



def get_github():
    token = os.getenv("GITHUB_TOKEN")
    from github import Auth
    return Github(auth=Auth.Token(token))




@tool
def search_code(question: str, repo: str = "") -> str:
    "repo ke code me search karke answer do and sath me file aur line number bhi. repo ka naam do (jaise 'TripMate') jab user ne bataya ho."

    # kai repos index hain aur user ne repo nahi bataya to poocho
    if not repo:
        repos = list_indexed_repos(PERSIST_DIR)
        if len(repos) > 1:
            return f"Kai repos index hain: {', '.join(repos)}. User se poocho kaun sa repo."

    embeddings = get_embeddings()
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)

    result = rag_ask(db, question, repo=repo or None)

    sources_text = ", ".join(
        f"{s['file']} (line {s['start_line']} - {s['end_line']})" for s in result['sources']
    )

    return f"{result['response']} \n\nSources : {sources_text}"




@tool
def indexed_repos() -> str:
    "kaun kaun se repos index hain, unki list do."
    repos = list_indexed_repos(PERSIST_DIR)
    return ", ".join(repos) if repos else "koi repo index nhi hai"




@tool
def get_issue(repo_full_name: str, issue_number: int) -> str:
    "github repo se ek issue ka title aur description nikalo.  repo_full_name format : 'owner/repo' , example - 'Arundhakad03/TripMate' "
    gh = get_github()
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    return f"Title : {issue.title}\n\nBody : {issue.body}"




@tool
def list_similar_issues(repo_full_name : str, query : str) -> str:
    "Kisi repo me diye gaye topic se milte jhulte open/closed issues dhundo."
    gh = get_github()
    repo = gh.get_repo(repo_full_name)
    issues = repo.get_issues(state='all')

    matches = []

    for issue in issues:
        if query.lower() in issue.title.lower():
            matches.append(f"#{issue.number} : {issue.title} ({issue.state})")
        if len(matches) >= 5:
            break

    if not matches:
        return "koi similar issue nhi mila"

    return "\n".join(matches)





@tool
def comment_on_pr (repo_full_name : str, pr_number: int, comment : str) -> str:
    "kisi PR ya issue pe comment post karo"
    gh = get_github()
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=pr_number)
    issue.create_comment(comment)

    return f"Comment posted on #{pr_number}"




def create_agent():
    llm = ChatGroq(model='openai/gpt-oss-120b', temperature=0)
    tools = [search_code, indexed_repos, get_issue, list_similar_issues, comment_on_pr]

    agent = create_react_agent(llm, tools)
    return agent





class TriageResult(BaseModel):
    label: str
    priority: str
    reasoning: str
    similar_issues: list[str]



def triage_issue(repo_full_name : str, issue_number : int) -> TriageResult:
    gh = get_github()
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    issues = repo.get_issues(state="all")
    similar = []
    for other in issues:
        if other.number == issue_number:
            continue
        if any(word in other.title.lower() for word in issue.title.lower().split()):
            similar.append(f"{other.number} : {other.title}")
        if len(similar) >= 5:
            break

    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    structured_llm = llm.with_structured_output(TriageResult)

    prompt = f"""Tum ek Github issue triage assistant ho.
    
Issue Title : {issue.title}
Issue body : {issue.body}

similar issues milke:
{chr(10).join(similar) if similar else "koi nhi mila"}

is issue ko triage karo:
- label : bug, feature, question, duplicate, ya documentation mein se ek
- priority : low, medium, ya high
- reasoning : ek ya do line mein kyu
- similar_issues : uper wali similar issues ki list (agar ho to)


"""
    response = structured_llm.invoke(prompt)
    return response


if __name__ == "__main__":
    agent = create_agent()
    response = agent.invoke({
        "messages": [("user", "Arundhakad03/TripMate repo me koi open issues hai kya? list_similar_issues tool use karke 'bug' search karo.")]
    })
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(response["messages"][-1].content)
    print("Done, check output.txt")

    result = triage_issue("Arundhakad03/AI-projects", 1)
    print(result)


